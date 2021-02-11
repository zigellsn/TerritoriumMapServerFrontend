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

import logging
import os
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("django.custom.smtp")


class RenderJobQuerySet(QuerySet):
    def by_owner(self, owner, finished=None):
        if finished is None:
            return self.filter(owner=owner)
        elif finished:
            return self.filter(owner=owner, finish_time__isnull=False)
        else:
            return self.filter(owner=owner, finish_time__isnull=True)


class RenderJobManager(models.Manager):
    def get_query_set(self):
        return RenderJobQuerySet(self.model, using=self._db)

    def by_owner(self, owner, finished=None):
        return self.get_query_set().by_owner(owner, finished)

    def create_render_job(self, guid, owner, polygon_count=1):
        return self.create(guid=guid, owner=owner, polygon_count=polygon_count)


class RenderJob(models.Model):
    guid = models.CharField(_('GUID'), primary_key=True, max_length=36)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    send_time = models.DateTimeField(default=timezone.now)
    finish_time = models.DateTimeField(null=True)
    polygon_count = models.IntegerField(_('Polygon count'), default=1)
    message = models.TextField(null=True)

    objects = RenderJobManager()


@receiver(post_save, sender=RenderJob)
def send_mail_receiver(sender, instance, **kwargs):
    if not kwargs["created"] and instance.owner.email != "":
        map_result = MapResult.objects.by_job([instance])
        if not map_result:
            return
        html_message = render_to_string("fileserver/job_status_mail.html", {"url": settings.EMAIL_SEND_URL,
                                                                            "map_result": map_result})
        send_mail(
            _("Territorium Map Server rendering job finished"),
            message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.owner.email],
            fail_silently=True,
            html_message=html_message
        )
    logging.info("ok")


class MapResultQuerySet(QuerySet):
    def by_job(self, job):
        return self.filter(job__in=job)

    def by_guid(self, guid):
        return self.get(guid=guid)

    def invalid(self):
        date = timezone.now() - timedelta(days=7)
        return self.filter(result_time__lt=date)


class MapResultManager(models.Manager):
    def get_query_set(self):
        return MapResultQuerySet(self.model, using=self._db)

    def create_map_result(self, guid, job, file, media_type="image/png"):
        return self.create(guid=guid, job=job, file=file, media_type=media_type)

    def delete_invalid(self):
        return self.get_query_set().invalid().delete()

    def by_job(self, job):
        if not job:
            return MapResult.objects.none()
        map_results = self.get_query_set().by_job(job).order_by("-result_time", "file")
        for map_result in map_results:
            map_result.filename = os.path.basename(map_result.file.name)
        return map_results

    def by_guid(self, guid):
        return self.get_query_set().by_guid(guid)


class MapResult(models.Model):
    guid = models.CharField(_('GUID'), primary_key=True, max_length=36)
    job = models.ForeignKey(RenderJob, on_delete=models.CASCADE)
    media_type = models.CharField(_('Media type'), default="image/png", max_length=100)
    file = models.FileField(upload_to='maps', blank=True)
    result_time = models.DateTimeField(default=timezone.now)

    objects = MapResultManager()
