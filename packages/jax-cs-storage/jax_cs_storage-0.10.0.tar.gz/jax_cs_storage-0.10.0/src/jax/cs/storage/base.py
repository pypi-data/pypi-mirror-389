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

"""The base namespace for interacting with this package.

Provides wrapper and factory classes to provide an abstraction to the underlying ObjectSvc
implementations.
"""

import logging
from typing import Type, Dict, BinaryIO, Optional, List, Union
from google.auth.exceptions import DefaultCredentialsError

from jax.cs.storage.object.abstract import ObjectSvc, UrlTypes, ObjectIngestSvc
from jax.cs.storage.object.services.gcs import ObjectIngestSvcGCS
from jax.cs.storage.object.services.io import ObjectSvcInMemory
from jax.cs.storage.utils import get_available_svcs

__all__ = ['StorageObject', 'StorageObjectIngest']


class StorageObject:
    """A wrapper around storage services to make various storage services look the same.

    A Facade for ObjectSvc classes that automates the selection and creation of the concrete
    ObjectSvc implementations.
    """

    SVCS = get_available_svcs(
        [
            ('jax.cs.storage.object.services.gcs', 'ObjectSvcGCS'),
            ('jax.cs.storage.object.services.io', 'ObjectSvcIO'),
        ]
    )
    DEFAULT_SVC = SVCS[0]

    def __init__(self,
                 url: str,
                 file_svc: Optional[Union[ObjectSvc, Type[ObjectSvc]]] = None,
                 file_svcs: Optional[List[Type[ObjectSvc]]] = None,
                 content_type: Optional[str] = None,
                 **kwargs):
        """Create a wrapped storage object with the storage object wrapper.

        :param url: The url of the storage object to wrap
        :param file_svc: manually override service selection by providing an instantiated service
        :param file_svcs: manually override priority or service selection by providing a
        list of uninstantiated ObjectSvc classes to use ordered by priority.
        :param content_type: The content type of the file (optional)
        :param kwargs: All kwargs will be passed to underlying storage object service creation
        """
        self._url = url
        self._kwargs = kwargs
        self._svc_list = file_svcs or self.SVCS
        _svc = file_svc or self.get_svc(url, self._svc_list)

        # This bit of code checks to see if the svc is instantiated or not. If it is not,
        # the default case, then it is instantiated here. Otherwise, it is used as is.
        if isinstance(_svc, type) and issubclass(_svc, ObjectSvc):
            self.svc: ObjectSvc = _svc(url, content_type=content_type, **kwargs)
        elif not isinstance(_svc, type) and isinstance(_svc, ObjectSvc):
            self.svc = _svc
        else:
            raise AttributeError("Provided file_svc must be either a subclass of "
                                 "ObjectSvc or an instance of a subclass of ObjectSvc")

    @classmethod
    def get_svc(cls,
                url: str,
                svc_list: Optional[List[Type[ObjectSvc]]] = None,
                default_svc: Optional[Type[ObjectSvc]] = None) -> Type[ObjectSvc]:
        """Select a suitable storage object service.

         Checks the url against each services' `.validate` method.

        :param url: The url of the storage object to select a service for
        :param svc_list: manually override priority or service selection by providing a list of
        uninstantiated ObjectSvc classes to use ordered by priority.
        :param default_svc: manually override  default service selection by providing an
        uninstantiated service
        :return: The selected uninstantiated service
        """
        found = False
        svc = default_svc or cls.DEFAULT_SVC
        svcs = svc_list or cls.SVCS
        for s in svcs:
            try:
                if s.validate(url):
                    svc = s
                    found = True
                    break
            except (OSError, DefaultCredentialsError) as e:
                logging.warning(f"Unable to validate {s.__name__} for {url}: {e}")
                continue
        if not found:
            logging.error(f"No suitable file service found, defaulting to {cls.DEFAULT_SVC}")
        return svc

    @classmethod
    def validate(cls,
                 url: str,
                 svc_list: Optional[List[Type[ObjectSvc]]] = None,
                 default_svc: Optional[Type[ObjectSvc]] = None) -> bool:
        """Test if the service handle the provided url.

        :param url: The url to validate
        :param svc_list: An optional alternate list of ObjectSvc implementations to validate against
        :param default_svc: An optional alternate default service to use when no others match
        :return: A boolean value representing if at least one of the available services can handle
        the provided url
        """
        return cls.get_svc(url, svc_list, default_svc).validate(url)

    def available(self) -> Dict[UrlTypes, str]:
        """Return the available ways that the underlying ObjectSvc can provide the file."""
        return self.format_available_hook(self.svc.available())

    def format_available_hook(self,
                              available_items: Dict[UrlTypes, ObjectSvc]) -> Dict[UrlTypes, str]:
        """Templated hook method to allow a developer to customize the availability dictionary.

        :param available_items: The result of calling the `available` method on the underlying
        ObjectSvc implementation.
        :return: a mapping from jax.cs.storage.enum.UrlTypes a string representation of the
        storage object
        """
        return {k: v.url for k, v in available_items.items()}

    def download(self, local_file: BinaryIO) -> BinaryIO:
        """Download an instance of a storage object to a provided BinaryIO instance.

        Each service should download the file according to the implemented downloader and return the
         new location of the downloaded file.
        :param local_file: a file like object to download to
        """
        return self.svc.download(local_file)

    def download_as_bytes(self) -> bytes:
        """Download and return the storage object as bytes.

        :return: The contents of the storage object as bytes
        """
        return self.svc.download_as_bytes()

    def delete(self):
        """Delete the underlying data represented by this storage object instance."""
        self.svc.delete()

    def replace(self, replacement: Union[str, 'StorageObject']):
        """Replace the underlying data represented by this storage object instance."""
        if isinstance(replacement, str):
            replacement = StorageObject(replacement)

        self.svc.replace(replacement.svc)

    @property
    def url(self) -> str:
        """Return the full url representation of the storage object.

        :return: The full url
        """
        return self.svc.url

    @property
    def user_url(self) -> str:
        """Return a user consumable url for the storage object.

        :return: User consumable url for the storage object
        """
        return self.svc.user_url

    def user_upload_url(self, **kwargs) -> str:
        """Return a user consumable url for uploading data to the storage object.

        :return: A url that the user can use to upload data with a PUT request.
        """
        return self.svc.user_upload_url(**kwargs)

    @property
    def user_name(self) -> str:
        """Return a user consumable name for the storage object.

        :return: User consumable name for the storage object
        """
        name = self.info.get('name')
        return name.split('/')[-1] if name else 'NO_NAME'

    @property
    def info(self) -> Dict[str, str]:
        """Information about the storage object.

        A proxy method for the underlying ObjectSvc .info method.

        :return: A dictionary of all information the underlying service knows about the storage
        object
        """
        return self.svc.info

    def refresh_info(self) -> Dict[str, str]:
        """Refresh the information about the storage object.

        A proxy method for the underlying ObjectSvc .refresh_info method.

        :return: A dictionary of all information the underlying service knows about the storage
        object
        """
        return self.svc.refresh_info()


class StorageObjectIngest(StorageObject):
    """A default implementation of a File Ingestion Facade.

    This Facade extends the StorageObject facade to include a factory method for StorageObject
    instances that need to be imported/ingested into the system. Note that this class inherits from
    StorageObject, and thatit is fully usable as astorage object wrapper on the remote storage
    object.

    Non-system File -> Ingester(Non-system File) -> Wrapper(System File)
    """

    INGESTION_SERVICE: Type[ObjectIngestSvc] = ObjectIngestSvcGCS

    def __init__(self,
                 url: str,
                 file_svc: Optional[ObjectSvc] = None,
                 file_svcs: Optional[List[Type[ObjectSvc]]] = None,
                 from_memory: bool = False,
                 **kwargs):
        """Create and instance of a storage object ingestion class.

        Extension of the `jax.cs.storage.base.StorageObject` constructor to include a `from_memory`
        kwarg flag. This flag will treat the url as the object contents rather than the object
        location, which is useful to create new files from content generated within an application.

        :param url: The url of the storage object to wrap
        :param file_svc: manually override service selection by providing an instantiated service
        :param file_svcs: manually override priority or service selection by providing a list of
        uninstantiated ObjectSvc classes to use ordered by priority.
        :param from_memory: If the url provided should be treated as memory. If so, the content of
         the provided url argument will be used as the content of the new ingested file.
        :param kwargs: All kwargs will be passed to underlying storage object service creation
        """
        if from_memory:
            file_svc = ObjectSvcInMemory(url=url, **kwargs)
        super().__init__(url, file_svc=file_svc, file_svcs=file_svcs, **kwargs)

    def ingest(self, **kwargs) -> StorageObject:
        """Create a StorageObject instance from ingesting the provided object.

        This method is a Factory for StorageObject instances.

        The ingest method of a ObjectIngestSvc is a factory for ObjectSvc instances.
        """
        self.svc = self._call_ingestion_svc(**kwargs)
        return self._create_new_file_wrapper()

    def _call_ingestion_svc(self, **kwargs) -> ObjectSvc:
        """Intended as a template method that can be overridden if needed."""
        return self.INGESTION_SERVICE().ingest(self.svc, **{**self._kwargs, **kwargs})

    def _create_new_file_wrapper(self, **kwargs):
        """Intended as a template method that can be overridden if needed."""
        return StorageObject(self.svc.url, file_svc=self.svc, **kwargs)

    @classmethod
    def resulting_svc(cls) -> Type[ObjectSvc]:
        """Return the uninstantiated class that the `ingest()` method will return an instance of."""
        return cls.INGESTION_SERVICE().base_svc
