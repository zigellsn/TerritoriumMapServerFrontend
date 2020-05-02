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
import uuid

import pika
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from fileserver.models import RenderJob

logger = logging.getLogger("django.request")


@method_decorator(csrf_exempt, name="dispatch")
class ReceiverView(LoginRequiredMixin, View):

    @staticmethod
    def create_job(polygon):
        job = {"job": str(uuid.uuid4()),
               "payload": json.loads(polygon)}
        return job

    def post(self, request, *args, **kwargs):
        request_type = request.META.get("HTTP_X_TERRITORIUM")

        if request_type == "map_rendering":
            job = self.create_job(request.body)
            try:
                connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
                channel = connection.channel()
                channel.queue_declare(queue="mapnik")
                channel.basic_publish(exchange="",
                                      routing_key="mapnik",
                                      body=json.dumps(job))
                connection.close()
                RenderJob.objects.create_render_job(guid=job["job"], owner=request.user,
                                                    media_type=job["payload"]["polygon"]["mediaType"])
            except pika.exceptions.AMQPConnectionError as e:
                print(e)
                return HttpResponse(status=500)
            return HttpResponse("success")

        return HttpResponse(status=204)
