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
from json import JSONDecodeError

import pika
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from TerritoriumMapServerFrontend.settings.common import MAX_POLYGONS
from fileserver.models import RenderJob

logger = logging.getLogger("django.request")


@method_decorator(csrf_exempt, name="dispatch")
class ReceiverView(LoginRequiredMixin, View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def __check_page__(page):
        if "mediaType" not in page:
            return False, f"No page media type given."
        if page["mediaType"] != "image/svg+xml" and page["mediaType"] != "application/pdf" \
                and page != "application/xhtml+xml":
            return False, f"Page media type has to be application/pdf, image/svg+xml or " \
                          f"application/xhtml+xml. "
        if page["mediaType"] != "application/pdf":
            return True, ""
        pagesize = None
        if "pageSize" in page:
            pagesize = page["pageSize"]
        if pagesize is not None and pagesize != "4A0" and pagesize != "2A0" and pagesize != "A0" and pagesize != "A1" \
                and pagesize != "A2" and pagesize != "A3" and pagesize != "A4" and pagesize != "A5" \
                and pagesize != "A6" and pagesize != "A7" and pagesize != "A8" and pagesize != "A9" \
                and pagesize != "A10" and pagesize != "B0" and pagesize != "B1" and pagesize != "B2" \
                and pagesize != "B3" and pagesize != "B4" and pagesize != "B5" and pagesize != "B6" \
                and pagesize != "B7" and pagesize != "B8" and pagesize != "B9" and pagesize != "B10" \
                and pagesize != "C0" and pagesize != "C1" and pagesize != "C2" and pagesize != "C3" \
                and pagesize != "C4" and pagesize != "C5" and pagesize != "C6" and pagesize != "C7" \
                and pagesize != "C8" and pagesize != "C9" and pagesize != "C10" \
                and pagesize != "RA0" and pagesize != "RA1" and pagesize != "RA2" and pagesize != "RA3" \
                and pagesize != "RA4" and pagesize != "SRA0" and pagesize != "SRA1" and pagesize != "SRA2" \
                and pagesize != "SRA3" and pagesize != "SRA4" \
                and pagesize != "EXECUTIVE" and pagesize != "FOLIO" and pagesize != "LEGAL" and pagesize != "LETTER" \
                and pagesize != "TABLOID":
            return False, f"Unknown page size '{pagesize}'."
        orientation = page["orientation"]
        if orientation is not None and orientation != "landscape" and orientation != "portrait":
            return False, f"Unknown page orientation '{orientation}'."
        return True, ""

    @staticmethod
    def __check_polygon__(number, polygon):
        if "mediaType" not in polygon or (
                polygon["mediaType"] != "image/svg+xml" and polygon["mediaType"] != "image/png"):
            return False, f"Polygon {number}: Media type has to be image/png or image/svg+xml."
        return True, ""

    def __check_payload__(self, payload):
        polygon_count = list(payload.keys()).count("polygon")
        if polygon_count != 1:
            return False, "Exactly one polygon definition is required."

        okay = True
        message = ""
        if type(payload["polygon"]) == list:
            polygon_count = len(payload["polygon"])
            if polygon_count > MAX_POLYGONS:
                return False, f"Maximum number of {MAX_POLYGONS} polygons exceeded."
            i = 0
            for polygon in payload["polygon"]:
                i = i + 1
                (okay, message) = self.__check_polygon__(i, polygon)
                if not okay:
                    return okay, message
        else:
            (okay, message) = self.__check_polygon__(1, payload["polygon"])

        if not okay:
            return okay, message

        page_count = list(payload.keys()).count("page")
        if page_count == 1:
            return self.__check_page__(payload["page"])
        elif page_count > 1:
            return False, "Only one or zero page definitions are allowed."
        else:
            return True, ""

    @staticmethod
    def __create_job__(payload):
        job = {"job": str(uuid.uuid4()),
               "payload": payload}
        return bytes(json.dumps(job).encode('utf-8'))

    def post(self, request, *args, **kwargs):
        request_type = request.META.get("HTTP_X_TERRITORIUM")
        if request_type == "map_rendering":
            try:
                payload = json.loads(request.body)
            except JSONDecodeError:
                return HttpResponse(status=400, content="Invalid JSON")
            (okay, message) = self.__check_payload__(payload)
            if not okay:
                return HttpResponse(status=400, content=message)
            job_message = self.__create_job__(payload)
            job = json.loads(job_message)
            try:
                polygon_count = 1
                if type(payload["polygon"]) == list and "page" not in payload:
                    polygon_count = len(payload["polygon"])
                RenderJob.objects.create_render_job(guid=job["job"], owner=request.user,
                                                    polygon_count=polygon_count)

                connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
                channel = connection.channel()
                channel.queue_declare(queue="mapnik")
                channel.basic_publish(exchange="",
                                      routing_key="mapnik",
                                      body=job_message)
                connection.close()
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(e)
                return HttpResponse(status=500)
            return HttpResponse(status=200)

        return HttpResponse(status=204)
