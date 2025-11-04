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

"""The root of the jax.cs.storage module.

e.g.

from jax.cs.storage import StorageObject, StorageObjectIngest

OR

from jax.cs.storage.entrypoint import init
StorageObject, StorageObjectIngest = init()
"""
try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata

__version__ = metadata.version("jax-cs-storage")

from jax.cs.storage.base import StorageObjectIngest, StorageObject
from jax.cs.storage.entrypoint import init
from jax.cs.storage.enums import UrlTypes
from jax.cs.storage.object.services.gcs import ObjectSvcGCS, ObjectIngestSvcGCS
from jax.cs.storage.object.services.io import ObjectSvcIO
from jax.cs.storage.object.services.r2 import ObjectSvcR2

__all__ = ['StorageObject', 'StorageObjectIngest', 'init', 'UrlTypes', 'ObjectSvcGCS',
           'ObjectIngestSvcGCS', 'ObjectSvcIO', 'ObjectSvcR2', '__version__']
