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

"""Storage Object Services backed by Google Cloud Storage."""

import uuid
from typing import Dict, BinaryIO, Type, Optional, Set, Union

import requests

from jax.cs.storage.exceptions import ApiAuthError
from jax.cs.storage.object.abstract import ObjectSvc, ObjectIngestSvc, UrlTypes
from . import utils as gcs


class ObjectSvcGCS(ObjectSvc):
    """An ObjectSvc implementation that uses Google Cloud Storage as the storage backend."""

    def __init__(self, url: str, **kwargs):
        """Create an instance of ObjectSvcGCS.

        This initializer performs pre-processing on the url of the GCS object to determine
        bucket_name, file_name, and blob_name during class instantiation.
        :param url: The url of location of the object the service will handle
        :param kwargs: keyword arguments to be used when handling the file
        """
        super().__init__(url, **kwargs)
        self.bucket_name, self.file_name, self.blob_name = gcs.split_gs_uri(self.url)
        self.bucket, self.client = gcs.get_bucket_and_client(
            self.bucket_name,
            credential_content=self.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        self.blob: gcs.Blob = self.bucket.blob(self.blob_name)

        if self.CONFIG.GCS_CHECK_BLOB_EXISTS:
            self.blob.reload()

    @classmethod
    def _client(cls):
        return gcs.get_client(credential_content=cls.CONFIG.GCS_CREDENTIALS_CONTENTS)

    @classmethod
    def validate(cls, url: str, **kwargs) -> bool:
        _client = cls._client() if cls.CONFIG.GCS_CHECK_BLOB_EXISTS else None
        return gcs.validate_url(url,
                                check_exists=cls.CONFIG.GCS_CHECK_BLOB_EXISTS,
                                client=_client)

    @classmethod
    def all(cls, root: Optional[str] = None, **kwargs) -> Set[str]:
        return gcs.all_files(cls.CONFIG.GCS_BUCKET,
                             prefix=root,
                             full_gs_path=kwargs.get('full_gs_path'),
                             client=cls._client())

    @classmethod
    def exists(cls, sub_location: str, root: Optional[str] = None, **kwargs) -> Optional[str]:
        _client = gcs.get_client(credential_content=cls.CONFIG.GCS_CREDENTIALS_CONTENTS)
        sub_location = f"{root}/{sub_location}" if root else sub_location
        existing = gcs.all_files(cls.CONFIG.GCS_BUCKET,
                                 full_gs_path=False,
                                 client=cls._client())
        if sub_location in existing:
            return f"gs://{cls.CONFIG.GCS_BUCKET}/{sub_location}"
        return None

    def available(self) -> Dict[UrlTypes, ObjectSvc]:
        return {
            UrlTypes.GCS: self,
        }

    def download(self,
                 local_file: BinaryIO,
                 start: Optional[int] = None,
                 end: Optional[int] = None,
                 **kwargs) -> BinaryIO:
        return gcs.download_blob_by_uri(self.client, self.url, local_file, start=start, end=end)

    def download_as_bytes(self,
                          start: Optional[int] = None,
                          end: Optional[int] = None,
                 **kwargs) -> bytes:
        return gcs.download_as_bytes(self.client, self.url, start=start, end=end)

    def replace(self, replacement: ObjectSvc, **kwargs):
        available = replacement.available()
        if UrlTypes.GCS in available and isinstance(available[UrlTypes.GCS], ObjectSvcGCS):
            replacement = available[UrlTypes.GCS]
            gcs.move_object_within_gcs(replacement.bucket,
                                       replacement.blob_name,
                                       self.bucket,
                                       self.blob_name,
                                       **kwargs)
        elif UrlTypes.LOCAL_MEMORY in available:
            replacement = available[UrlTypes.LOCAL_MEMORY]
            gcs.upload_string_to_bucket_loaction(self.bucket,
                                                 replacement.url,
                                                 replacement.content_type,
                                                 self.blob_name,
                                                 **kwargs)
        elif UrlTypes.FILE_IO in available:
            replacement = available[UrlTypes.FILE_IO]
            gcs.upload_file_to_bucket_location(
                self.bucket, replacement.url, self.blob_name, **kwargs
            )
        else:
            gcs.upload_string_to_bucket_loaction(self.bucket,
                                                 replacement.download_as_bytes(),
                                                 replacement.content_type,
                                                 self.blob_name,
                                                 **kwargs)
        self.refresh_info()

    def delete(self, **kwargs):
        self.blob.delete(**kwargs)
        gcs.delete_blob(self.blob)

    @property
    def user_url(self) -> str:
        expire_hrs = self.CONFIG.GCS_URL_EXPIRE_HOURS
        try:
            return gcs.generate_signed_url(self.blob, expiration=expire_hrs)
        except AttributeError as e:
            raise ApiAuthError(e) from e

    def user_upload_url(self, **kwargs) -> str:
        expire_hrs = kwargs.get('expiration') or self.CONFIG.GCS_URL_UPLOAD_EXPIRE_HOURS
        content_type = kwargs.get('content_type') or 'application/octet-stream'
        return gcs.generate_signed_upload_url(self.blob,
                                              content_type=content_type,
                                              expiration=expire_hrs)

    @property
    def info(self) -> Dict[str, str]:
        return {
            'name': self.blob.name,
            'size': self.blob.size,
            'path': self.blob.path,
            'bucket': self.blob.bucket.name,
            'metadata': self.blob.metadata,
            'id': self.blob.id,
            'created': self.blob.time_created,
            'url': self.url
        }

    def refresh_info(self, **kwargs) -> Dict[str, str]:
        self.blob.reload(**kwargs)
        return self.info


class ObjectIngestSvcGCS(ObjectIngestSvc):
    """A Google cloud storage backed ObjectIngestSvc.

    See the documentation for `jax.cs.storage.object.abstract.ObjectIngestSvc`.
    """

    def __init__(self, base_svc: Type[ObjectSvc] = None):
        """Create an ingestion service class instance.

        See documentation on `jax.cs.storage.object.abstract.ObjectIngestSvc`.
        :param base_svc: Optional override for the base Google Cloud storage
        backed ObjectSvc implementation.
        """
        super().__init__(base_svc or ObjectSvcGCS)

    def ingest(self, ext_file: ObjectSvc, **kwargs) -> ObjectSvc:
        """Create a StorageObject instance from ingesting the provided object.

        A factory method to build a ObjectSvc representing a file that is
        internal to the system from a ObjectSvc instance representing a file
        external to the system.
        :param ext_file: An instance of an ObjectSvc representing a file to ingest
        :param kwargs: keyword args to be used by the ingestion service
        :return: An instance of a ObjectSvc after representing the file after being moved
        """
        return self.base_svc(self.__ingest(ext_file, **kwargs), **kwargs)

    def _client(self):
        return gcs.get_client(
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )

    @property
    def object_prefix(self):
        return self.base_svc.CONFIG.GCS_PREFIX_DIR

    @property
    def bucket_name(self):
        return self.base_svc.CONFIG.GCS_BUCKET

    def __internal_validate(self, url: str, check_exists=False):
        if check_exists:
            return (
                    self.__url_in_bucket(url)
                    and
                    gcs.validate_url(url, check_exists=True, client=self._client())
            )
        else:
            return url.startswith(self.bucket_name)

    def __url_in_bucket(self, url):
        url.startswith(self.bucket_name)

    def __generate_internal_name(self, *args, **kwargs):
        filename = '_'.join(args)
        _ = kwargs.pop('filename', None)
        return self.generate_internal_name(filename, uuid=uuid.uuid4().hex, **kwargs)

    def generate_internal_name(self,
                               filename: Optional[str] = None,
                               **kwargs) -> str:
        """Format the name of the ingested object.

        Default template method implementation for GCS.
        Override me to customize object naming behavior in GCS.
        :param filename: The base filename prior to ingestion of the file
        :param kwargs: To be used to pull in extra information to be used in the naming process
        :return: The internal name of the file to use
        """
        ret = f"{self.object_prefix}/" if self.object_prefix else ''
        include_uuid = kwargs.get('include_uuid')
        if include_uuid:
            ret += f"{uuid.uuid4().hex}/"

        return f"{ret}{filename}"

    def __ingest(self, ext_file: ObjectSvc, **kwargs) -> str:
        available = ext_file.available()
        if UrlTypes.GCS in available:
            return self._ingest_gcs_url(available[UrlTypes.GCS], **kwargs)
        elif UrlTypes.LOCAL_MEMORY in available:
            return self._ingest_local_memory(available[UrlTypes.LOCAL_MEMORY], **kwargs)
        elif UrlTypes.FILE_IO in available:
            return self._ingest_local_file(available[UrlTypes.FILE_IO], **kwargs)
        elif UrlTypes.R2 in available:
            return self._ingest_r2_url(available[UrlTypes.R2], **kwargs)
        else:
            raise AttributeError

    def _ingest_gcs_url(self, file_svc: ObjectSvc, **kwargs) -> str:
        src_bucket_name, src_filename, src_blob_name = gcs.split_gs_uri(file_svc.url)
        src_bucket, src_client = gcs.get_bucket_and_client(
            src_bucket_name,
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        dst_bucket, dst_client = gcs.get_bucket_and_client(
            self.bucket_name,
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        # Override the original filename with one speicifed in the kwargs
        src_filename = kwargs.get('filename', src_filename)
        dst_blob_name = self.__generate_internal_name(src_filename, **kwargs)
        if self.__internal_validate(file_svc.url, check_exists=True):
            # Is it already where we would want to put it?
            if src_bucket_name == self.bucket_name and src_blob_name == dst_blob_name:
                return gcs.gs_path_from_blob(dst_bucket.blob(dst_blob_name))
            else:
                return gcs.move_object_within_gcs(src_bucket, src_blob_name,
                                                  dst_bucket, dst_blob_name)
        elif gcs.validate_url(file_svc.url, check_exists=True, client=src_client):
            return gcs.copy_object_within_gcs(src_bucket, src_blob_name,
                                              dst_bucket, dst_blob_name)
        else:
            raise AttributeError("No way to download provided file")

    def _ingest_r2_url(self, file_svc: ObjectSvc, **kwargs) -> str:
        src_filename = kwargs.get('filename') or file_svc.info.get('name', 'r2_file')
        dst_bucket, dst_client = gcs.get_bucket_and_client(
            self.bucket_name,
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        dst_blob_name = self.__generate_internal_name(src_filename, **kwargs)

        resp = requests.get(file_svc.user_url)
        return gcs.upload_string_to_bucket_loaction(dst_bucket,
                                                    resp.content,
                                                    resp.headers['content-type'],
                                                    dst_blob_name)

    def _ingest_local_memory(self, file_svc: ObjectSvc, **kwargs):
        src_filename = kwargs.get('filename') or file_svc.info.get('name', 'local_memory_file')
        content_type = kwargs.get('content_type', 'text/plain')
        dst_bucket, dst_client = gcs.get_bucket_and_client(
            self.bucket_name,
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        dst_blob_name = self.__generate_internal_name(src_filename, **kwargs)
        return gcs.upload_string_to_bucket_loaction(dst_bucket,
                                                    file_svc.url,
                                                    content_type,
                                                    dst_blob_name)

    def _ingest_local_file(self, file_svc: ObjectSvc, **kwargs) -> str:
        src_filename = kwargs.get('filename') or file_svc.info.get('name', 'local_file')
        dst_bucket, dst_client = gcs.get_bucket_and_client(
            self.bucket_name,
            credential_content=self.base_svc.CONFIG.GCS_CREDENTIALS_CONTENTS
        )
        dst_blob_name = self.__generate_internal_name(src_filename, **kwargs)
        return gcs.upload_file_to_bucket_location(
            dst_bucket, file_svc.url, dst_blob_name
        )
