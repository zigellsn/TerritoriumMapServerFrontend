#  Copyright 2019-2025 Simon Zigelli
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
import uuid
from pathlib import Path

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.utils import timezone

from TerritoriumMapServerFrontend import settings
from fileserver.models import RenderJob, MapResult


class MqConsumer(AsyncConsumer):

    @staticmethod
    async def callback(message: AbstractIncomingMessage):
        try:
            result = json.loads(message.body)
        except AttributeError as e:
            logging.error(e)
            return
        if not ("job" in result and "payload" in result):
            return
        try:
            render_job = await database_sync_to_async(RenderJob.objects.get)(guid=result["job"])
            if render_job.finish_time is not None:
                logging.warning(f"Rendering job {render_job.guid} already finished.")
                return
            if "error" in result and result["error"]:
                render_job.message = result["payload"]
                render_job.finish_time = timezone.now()
                await database_sync_to_async(render_job.save)()
                return
            else:
                map_result = MapResult()
                map_result.guid = uuid.uuid4()
                map_result.job = render_job

                map_result.media_type = result["mediaType"]
                print(f"{settings.EXCHANGE_DIR}")
                contents = Path(f"{settings.EXCHANGE_DIR}{result['payload']}").read_bytes()
                await database_sync_to_async(map_result.file.save)(result["filename"], ContentFile(contents))
                await database_sync_to_async(map_result.save)()
                Path(f"{settings.EXCHANGE_DIR}{result['payload']}").unlink(missing_ok=True)
            logging.info("File received")
            map_result_count = await database_sync_to_async(MapResult.objects.filter(job=render_job).count)()
            if map_result_count == render_job.polygon_count:
                render_job.finish_time = timezone.now()
                await database_sync_to_async(render_job.save)()
                logging.info(f"Job {render_job.guid} finished.")

        except Exception as e:
            logging.error(e)

    async def mq_listen(self, message):
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(name="maps", durable=True)
        await queue.consume(callback=self.callback, no_ack=True)
