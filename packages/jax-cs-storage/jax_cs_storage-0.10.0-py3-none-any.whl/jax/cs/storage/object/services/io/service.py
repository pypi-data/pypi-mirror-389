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

"""Storage object service backed by python IO."""

import gc
import logging
import os
import shutil
import uuid
from typing import Dict, BinaryIO, Set, Optional, Type

from jax.cs.storage.object.abstract import ObjectSvc, ObjectIngestSvc, UrlTypes


class ObjectSvcIO(ObjectSvc):
    """A service for interacting with file like IO as objects."""

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        self._info_cache = None

    @classmethod
    def exists(cls, sub_location: str, root: Optional[str] = None) -> Optional[str]:
        sub_location = os.path.join(root, sub_location) if root else sub_location
        full_path = os.path.join(cls.CONFIG.IO_FILE_ROOT or '', sub_location)
        return full_path if cls.validate(full_path) else None

    @classmethod
    def validate(cls, url: str) -> bool:
        return os.path.isfile(url)

    @classmethod
    def all(cls, root: Optional[str] = None, **kwargs) -> Set[str]:
        root = root or cls.CONFIG.IO_FILE_ROOT or ''
        return {
            os.path.join(dp or '', f or '')
            for dp, dn, filenames in os.walk(root)
            for f in filenames
        }

    def available(self) -> Dict[UrlTypes, ObjectSvc]:
        return {
            UrlTypes.FILE_IO: self,
        }

    def download(self,
                 local_file: BinaryIO,
                 start: Optional[int] = None,
                 end: Optional[int] = None) -> BinaryIO:
        try:
            with open(self.url, 'rb') as this_io:
                shutil.copyfileobj(this_io, local_file)
        except TypeError:
            with open(self.url, 'r') as this_io:
                shutil.copyfileobj(this_io, local_file)
        return local_file

    def download_as_bytes(self,
                          start: Optional[int] = None,
                          end: Optional[int] = None) -> bytes:
        with open(self.url, 'rb') as f:
            content = f.read()
        return content

    def replace(self, replacement: ObjectSvc):
        with open(self.url, 'wb') as dst_file:
            replacement.download(dst_file)

    def delete(self):
        os.remove(self.url)

    @property
    def user_url(self) -> str:
        raise NotImplementedError

    def user_upload_url(self, **kwargs) -> str:
        raise NotImplementedError

    def _get_info(self):
        self._info_cache = {
            'name': os.path.basename(self.url),
            'size': str(os.path.getsize(self.url)),
            'modified': str(os.path.getmtime(self.url)),
            'created': str(os.path.getctime(self.url)),
            'path': self.url,
            'url': self.url
        }

    @property
    def info(self) -> Dict[str, str]:
        if not self._info_cache:
            self._get_info()
        return self._info_cache

    def refresh_info(self) -> Dict[str, str]:
        self._get_info()
        return self._info_cache


class ObjectIngestSvcIO(ObjectIngestSvc):
    """A service to ingest files into file like IO."""

    def __init__(self, base_svc: Optional[Type[ObjectSvc]] = None):
        """Create an instance of to ingest files."""
        super().__init__(base_svc or ObjectSvcIO)

    def ingest(self, ext_file: ObjectSvc, **kwargs) -> ObjectSvc:
        return self.base_svc(self._ingest(ext_file, **kwargs), **kwargs)

    def _ingest(self, ext_file: ObjectSvc, **kwargs) -> str:
        available = ext_file.available()
        if UrlTypes.LOCAL_MEMORY in available:
            return self._ingest_local_memory(available[UrlTypes.LOCAL_MEMORY], **kwargs)
        else:
            raise NotImplementedError("No way to ingest the provided file")

    def _ingest_local_memory(self, file_svc: ObjectSvc, **kwargs) -> str:
        try:
            src_filename = kwargs.pop('filename', None) or file_svc.info.get('name',
                                                                             uuid.uuid4().hex)
        except NotImplementedError:
            src_filename = uuid.uuid4().hex

        dst_path = self.generate_internal_name(src_filename, **kwargs)
        file_mode = kwargs.get('file_mode', 'wb')

        with open(dst_path, file_mode) as dst_file:
            dst_file.write(file_svc.url)
        return dst_path

    def generate_internal_name(self,
                               filename: Optional[str] = None,
                               **kwargs) -> str:
        return os.path.join(self.base_svc.CONFIG.IO_FILE_ROOT or '', filename or '')


class ObjectSvcInMemory(ObjectSvc):
    """A utility service to enable creating new files from memory."""

    @classmethod
    def exists(cls, sub_location: str, root: Optional[str] = None) -> Optional[str]:
        logging.error("You'll need to give the ObjectSvcInMemory the memory "
                      "content when you crate it")
        return None

    @classmethod
    def validate(cls, url: str) -> bool:
        logging.error("The ObjectSvcInMemory must be manually selected")
        return False

    @classmethod
    def all(cls, root: Optional[str] = None, **kwargs) -> Set[str]:
        return set()

    def available(self) -> Dict[UrlTypes, ObjectSvc]:
        return {
            UrlTypes.LOCAL_MEMORY: self,
        }

    def download(self,
                 local_file: BinaryIO,
                 start: Optional[int] = None,
                 end: Optional[int] = None) -> BinaryIO:
        # TODO: Deal with this syntax check error
        #  "Expected type 'bytes' (matched generic type 'AnyStr'), got 'str' instead"
        local_file.write(self.url.encode())
        return local_file

    def download_as_bytes(self,
                          start: Optional[int] = None,
                          end: Optional[int] = None) -> bytes:
        try:
            return self.url.encode()
        except AttributeError:
            return self.url

    @property
    def user_url(self) -> str:
        raise NotImplementedError

    def replace(self, replacement: ObjectSvc):
        self.url = replacement.download_as_bytes()

    def delete(self):
        del self.url
        gc.collect()
        self.url = ''

    @property
    def info(self) -> Dict[str, str]:
        raise NotImplementedError

    def refresh_info(self) -> Dict[str, str]:
        raise NotImplementedError