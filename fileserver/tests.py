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

import uuid

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from fileserver.models import RenderJob, MapResult


class FileListViewTests(TestCase):

    def setUp(self):
        self.test_user = User.objects.create(username="testuser")
        self.test_user.set_password("12345")
        self.test_user.save()

    def test_download_empty(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("fileserver:filelist"))
        self.assertContains(response, "No files")

    def test_download_all(self):
        self.client.login(username="testuser", password="12345")
        job_guid = uuid.uuid4()
        render_job = RenderJob.objects.create_render_job(guid=job_guid, owner=self.test_user)
        file_name = f"{uuid.uuid4()}.pdf"
        file = SimpleUploadedFile(f"map/{file_name}", b"pdf")
        MapResult.objects.create_map_result(guid=uuid.uuid4(), job=render_job, file=file)
        response = self.client.get(reverse("fileserver:filelist"))
        self.assertNotContains(response, "No files")
        self.assertNotContains(response, f"map/{file_name}")
        self.assertContains(response, file_name)
        self.assertContains(response, job_guid)
        # absolute_file_name = f"files/map/{file}"
        # os.remove(absolute_file_name)

    def test_not_authorized(self):
        response = self.client.get(reverse("fileserver:filelist"))
        self.assertEqual(response.status_code, 302)
