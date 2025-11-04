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

"""Storage Object Services backed by Jax/CS's R2 web file service."""

import logging
from typing import BinaryIO, Dict, Optional, Set

from jax.cs.storage.object.abstract import ObjectSvc, UrlTypes
from jax.cs.storage.object.services.gcs.service import ObjectSvcGCS
from . import utils


class ObjectSvcR2(ObjectSvc):
    """An object storage service backed by Jax/CS's R2 web file service."""

    def __init__(self, url: str, **kwargs):
        """Create an instance of the service.

        :param url: The url of the file in r2.
        :param kwargs: If passed, the `auth_header` and `r2_url` kwargs will be used.
        """
        logging.warning(
            "R2 service is deprecated and will be removed in a future release."
        )
        super().__init__(url, **kwargs)
        self.auth_header = kwargs.get('auth_header')
        self.r2_url = kwargs.get('r2_url')
        self.__info_cache = None
        if not self.auth_header:
            raise AttributeError("Auth header required for r2 service")

    @classmethod
    def all(cls, root: Optional[str] = None, **kwargs) -> Set[str]:
        raise NotImplementedError

    @classmethod
    def validate(cls, url: str) -> bool:
        return utils.validate_url(url, r2_base_url=cls.CONFIG.R2_BASE_URL)

    @classmethod
    def exists(cls, sub_location: str, root: Optional[str] = None) -> Optional[str]:
        sub_location = f"{root}/{sub_location}" if root else sub_location
        full_url = f"{cls.CONFIG.R2_BASE_URL}/{sub_location}"
        return full_url if cls.validate(full_url) else None

    def available(self) -> Dict[UrlTypes, ObjectSvc]:
        return {
            UrlTypes.R2: self,
            UrlTypes.GCS: ObjectSvcGCS(self._gcs_url)
        }

    def download(self,
                 local_file: BinaryIO,
                 start: Optional[int] = None,
                 end: Optional[int] = None) -> BinaryIO:
        return utils.download_file(self.user_url, local_file)

    def download_as_bytes(self,
                          start: Optional[int] = None,
                          end: Optional[int] = None) -> bytes:
        return NotImplemented

    def delete(self):
        raise NotImplementedError

    @property
    def info(self):
        if not self.__info_cache:
            self.__info_cache = utils.get_url_json_or_error(self.url, self.auth_header)
        return self.__info_cache

    @property
    def user_url(self) -> str:
        return self.info.get('location')

    def user_upload_url(self, **kwargs) -> str:
        raise NotImplementedError

    @property
    def _gcs_url(self) -> str:
        return 'gs://' + '/'.join(self.user_url.split('?')[0].split('/')[3:])

    def refresh_info(self) -> Dict[str, str]:
        self.__info_cache = utils.get_url_json_or_error(self.url, self.auth_header)
        return self.__info_cache
