#  Copyright 2019-2020 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import json
import logging
import threading
import uuid

import pika
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


class AMQPConsuming(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def callback(ch, method, properties, body):
        try:
            result = json.loads(body)
        except AttributeError as e:
            logging.error(e)
            return
        if not ("job" in result and "payload" in result):
            return
        try:
            from fileserver.models import RenderJob, MapResult
            render_job = RenderJob.objects.get(guid=result["job"])
            if render_job.finish_time is not None:
                logging.warning(f"Rendering job {render_job.guid} already finished.")
                return
            if "error" in result and result["error"]:
                render_job.message = bytes(result["payload"]["data"]).decode("utf-8")
                render_job.finish_time = timezone.now()
                render_job.save()
                return
            else:
                map_result = MapResult()
                map_result.guid = uuid.uuid4()
                map_result.job = render_job

                map_result.media_type = result["mediaType"]
                map_result.file.save(result["filename"], ContentFile(bytes(result["payload"]["data"])))
                map_result.save()
            logging.info("File received")
            map_result_count = MapResult.objects.filter(job=render_job).count()
            if map_result_count == render_job.polygon_count:
                render_job.finish_time = timezone.now()
                render_job.save()
                logging.info(f"Job {render_job.guid} finished.")

        except Exception as e:
            logging.error(e)

    @staticmethod
    def _get_connection():
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        return connection

    def run(self):
        connection = self._get_connection()
        logging.info("Connected")
        channel = connection.channel()

        channel.queue_declare(queue="maps")
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_message_callback=self.callback, queue="maps", auto_ack=True)

        channel.start_consuming()
