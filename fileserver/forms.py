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

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

from fileserver.models import MapResult


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = MapResult
        fields = ["job", "user", "file"]

    user = ModelChoiceField(queryset=User.objects.all(), empty_label=None,
                            to_field_name="id")
