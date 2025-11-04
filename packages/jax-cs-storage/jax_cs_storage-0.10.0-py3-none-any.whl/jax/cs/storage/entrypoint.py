# Copyright 2022 The Jackson Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper init function to make it easy to configure package settings."""

from typing import List, Type, Tuple, Optional

from jax.cs.storage.base import StorageObject, StorageObjectIngest
from jax.cs.storage.config import StorageConfig
from jax.cs.storage.object.abstract import ObjectSvc, ObjectIngestSvc

init_return = Tuple[Type[StorageObject], Type[StorageObjectIngest]]


def init(settings: Optional[StorageConfig] = None,
         default_svc: Optional[Type[ObjectSvc]] = None,
         services: Optional[List[Type[ObjectSvc]]] = None,
         ingestion_svc: Optional[Type[ObjectIngestSvc]] = None) -> init_return:
    """Build StorageObject, StorageObjectIngest by helping with configuration and customization.

    :param settings: explicit settings to use with the library,
                        otherwise uses .env/environment variables
    :param default_svc: an ObjectSvc to use as the default service
    :param services: a list of ObjectSvc to select from when creating a StorageObject
    :param ingestion_svc: an ObjectIngestSvc to use to ingest storage objects
    :return: an un-instantiated StorageObject and StorageObjectIngest
    """
    if settings:
        ObjectSvc.CONFIG = settings

    if services:
        StorageObject.SVCS = services

    if default_svc:
        StorageObject.DEFAULT_SVC = default_svc

    if ingestion_svc:
        StorageObjectIngest.INGESTION_SERVICE = ingestion_svc

    return StorageObject, StorageObjectIngest
