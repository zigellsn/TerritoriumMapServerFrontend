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

import os
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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

    def create_render_job(self, guid, owner, media_type="image/png"):
        return self.create(guid=guid, owner=owner, media_type=media_type)


class RenderJob(models.Model):
    guid = models.CharField(_('GUID'), primary_key=True, max_length=36)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    send_time = models.DateTimeField(default=timezone.now)
    finish_time = models.DateTimeField(null=True)
    media_type = models.CharField(_('Media type'), default="image/png", max_length=100)

    objects = RenderJobManager()


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

    def create_map_result(self, guid, job, file):
        return self.create(guid=guid, job=job, file=file)

    def delete_invalid(self):
        return self.get_query_set().invalid().delete()

    def by_job(self, job):
        if not job:
            return MapResult.objects.none()
        map_results = self.get_query_set().by_job(job).order_by("-result_time", "file")
        for map_result in map_results:
            render_job = RenderJob.objects.get(guid=map_result.job_id)
            map_result.filename = os.path.basename(map_result.file.name)
            map_result.media_type = render_job.media_type
        return map_results

    def by_guid(self, guid):
        return self.get_query_set().by_guid(guid)


class MapResult(models.Model):
    guid = models.CharField(_('GUID'), primary_key=True, max_length=36)
    job = models.ForeignKey(RenderJob, on_delete=models.CASCADE)
    file = models.FileField(upload_to='maps')
    result_time = models.DateTimeField(default=timezone.now)

    objects = MapResultManager()
