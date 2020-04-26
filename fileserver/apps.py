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
import threading
import uuid

import pika
from decouple import config
from django.apps import AppConfig
from django.core.files.base import ContentFile
from django.utils import timezone


class FileserverConfig(AppConfig):
    name = 'fileserver'

    def ready(self):
        consumer = AMQPConsuming()
        consumer.daemon = True
        consumer.start()


class AMQPConsuming(threading.Thread):

    @staticmethod
    def callback(ch, method, properties, body):
        try:
            result = json.loads(body)
        except AttributeError as e:
            print(e)
            return
        if not ("job" in result and "payload" in result and "filename" in result):
            return
        try:
            from fileserver.models import RenderJob, MapResult
            render_job = RenderJob.objects.get(guid=result["job"])
            if render_job.finish_time is not None:
                return
            render_job.finish_time = timezone.now()
            map_result = MapResult()
            map_result.guid = uuid.uuid4()
            map_result.job = render_job
            map_result.file.save(result["filename"], ContentFile(bytes(result["payload"]["data"])))
            map_result.save()
            render_job.save()
            # if render_job.owner.email is not None:
            #     domain = Site.objects.get_current().domain
            #     html_message = render_to_string("fileserver/job_status_mail.html", {"protocol": "https",
            #                                                                         "domain": domain,
            #                                                                         "map_result": map_result})
            #     send_mail(
            #         _("Territorium Map Server render job finished"),
            #         from_email=settings.DEFAULT_FROM_EMAIL,
            #         recipient_list=[render_job.owner.email],
            #         fail_silently=True,
            #         html_message=html_message
            #     )
        except Exception as e:
            print(e)

    @staticmethod
    def _get_connection():
        credentials = pika.PlainCredentials(config("RABBITMQ_DEFAULT_USER"), config("RABBITMQ_DEFAULT_PASS"))
        parameters = pika.ConnectionParameters(config("RABBITMQ_HOST", default="localhost"), credentials=credentials,
                                               connection_attempts=10, retry_delay=5.0)
        connection = pika.BlockingConnection(parameters)
        return connection

    def run(self):
        connection = self._get_connection()
        print("Connected")
        channel = connection.channel()

        channel.queue_declare(queue="maps")
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_message_callback=self.callback, queue="maps", auto_ack=True)

        channel.start_consuming()
