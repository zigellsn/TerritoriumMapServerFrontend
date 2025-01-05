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
import os
import uuid
from json import JSONDecodeError

import aio_pika
from asgiref.sync import sync_to_async
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ninja import NinjaAPI
from ninja.signature import is_async

from TerritoriumMapServerFrontend import settings
from TerritoriumMapServerFrontend.settings import MAX_POLYGONS, PAGE_SIZES, ORIENTATIONS, CONTAINER_MEDIA_TYPES, \
    CONTENT_MEDIA_TYPES, RENDER_FONT_DIR
from fileserver.models import RenderJob

api = NinjaAPI(csrf=True)

logger = logging.getLogger("django.request")


async def async_auth(request: HttpRequest):
    if hasattr(request, "auser") and is_async(request.auser):
        current_user = await request.auser()
    else:
        current_user = request.user

    if current_user.is_authenticated:
        return current_user
    return None


@api.post("/receiver/", auth=async_auth)
@csrf_exempt
async def receiver(request):
    request_type = request.META.get("HTTP_X_TERRITORIUM")
    if request_type == "map_rendering":
        try:
            payload = json.loads(request.body)
        except JSONDecodeError:
            return HttpResponse(status=400, content="Invalid JSON")
        (okay, message) = __check_payload__(payload)
        if not okay:
            return HttpResponse(status=400, content=message)
        job_message = __create_job__(payload)
        job = json.loads(job_message)
        try:
            polygon_count = 1
            if type(payload["polygon"]) == list and "page" not in payload:
                polygon_count = len(payload["polygon"])
            await sync_to_async(RenderJob.objects.create_render_job)(guid=job["job"], owner=request.user,
                                                                     polygon_count=polygon_count)

            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()
            queue = await channel.declare_queue(name="mapnik", durable=True)
            await channel.default_exchange.publish(aio_pika.Message(body=job_message), routing_key=queue.name)
            await connection.close()
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.error(e)
            return HttpResponse(status=500)
        return HttpResponse(status=200)

    return HttpResponse(status=204)


@api.get("/fonts/", auth=async_auth)
@csrf_exempt
async def fonts(request):
    request_type = request.META.get("HTTP_X_TERRITORIUM")
    if request_type != "fonts":
        return HttpResponse(status=204)
    font_list = []
    try:
        path = os.path.abspath(RENDER_FONT_DIR)
        for f in os.listdir(path):
            if os.path.isfile(f"{path}/{f}") and (
                    f.endswith("ttf") or f.endswith("woff") or f.endswith("woff2") or f.endswith("otf")):
                font_list.append(f)
    except OSError:
        pass
    return JsonResponse({"fonts": font_list}, status=200)


@api.get("/constants/", auth=async_auth)
@csrf_exempt
async def constants(request):
    request_type = request.META.get("HTTP_X_TERRITORIUM")
    if request_type != "constants":
        return HttpResponse(status=204)
    return JsonResponse({"constants": {
        "media_type": {"container": CONTAINER_MEDIA_TYPES, "content": CONTENT_MEDIA_TYPES}, "page_size": PAGE_SIZES,
        "orientation": ORIENTATIONS}}, status=200)


def __check_page__(page):
    if "mediaType" not in page:
        return False, f"No page media type given."
    if page["mediaType"] not in CONTAINER_MEDIA_TYPES:
        return False, f"Page media type has to be application/pdf, image/svg+xml or " \
                      f"application/xhtml+xml."
    if page["mediaType"] != "application/pdf":
        return True, ""
    pagesize = None
    if "pageSize" in page:
        pagesize = page["pageSize"]
    if pagesize is not None and pagesize not in PAGE_SIZES:
        return False, f"Unknown page size '{pagesize}'."
    orientation = page["orientation"]
    if orientation is not None and orientation not in ORIENTATIONS:
        return False, f"Unknown page orientation '{orientation}'."
    return True, ""


def __check_polygon__(number, polygon):
    if "mediaType" not in polygon or polygon["mediaType"] not in CONTENT_MEDIA_TYPES:
        return False, f"Polygon {number}: Media type has to be image/png or image/svg+xml."
    return True, ""


def __check_payload__(payload):
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
            (okay, message) = __check_polygon__(i, polygon)
            if not okay:
                return okay, message
    else:
        (okay, message) = __check_polygon__(1, payload["polygon"])

    if not okay:
        return okay, message

    page_count = list(payload.keys()).count("page")
    if page_count == 1:
        return __check_page__(payload["page"])
    elif page_count > 1:
        return False, "Only one or zero page definitions are allowed."
    else:
        return True, ""


def __create_job__(payload):
    job = {"job": str(uuid.uuid4()),
           "payload": payload}
    return bytes(json.dumps(job).encode("utf-8"))
