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

"""The abstract class definitions for ObjectSvc and ObjectIngestSvc implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type, Dict, BinaryIO, ClassVar, Optional, Set

from jax.cs.storage.config import StorageConfig, default_settings
from jax.cs.storage.enums import UrlTypes


class ObjectSvc(ABC):
    """The base abstract class for all storage service backends.

    A ObjectSvc implementation should provide these methods to a specific file backend
    (e.g. gcs, s3, ftp). This allows the StorageObject to use a consistent interface for file
    interaction with the service. A concrete implementation of this abstract class can be used
    to configure the StorageObject to handle files of that specific file backend.
    """

    CONFIG: ClassVar[StorageConfig] = default_settings

    def __init__(self, url: str, content_type: Optional[str] = None, **kwargs):
        """Create an instance of an ObjectSvc.

        The url represents the location of the storage object.
        :param url: The url of the object the service will handle
        :param content_type: The content type of the file
        :param kwargs: keyword arguments to be used when handling the file
        :return: None
        """
        self.url = url
        self.content_type = content_type or 'text/plain'
        self.kwargs = kwargs

    @classmethod
    @abstractmethod
    def validate(cls, url: str, **kwargs) -> bool:
        """Validate that the service handle the provided url.

        :param url: The url to be validated
        :param kwargs: keyword args to be used by the underlying file service
        :return: True: the url can be handled, False: the url cannot be handled
        """

    @classmethod
    @abstractmethod
    def all(cls, root: Optional[str] = None, **kwargs) -> Set[str]:
        """Return a list of urls representing files in the service.

        :param root: A base directory to list from
        :param kwargs: keyword args to be used by the underlying file service
        :return: A set of all urls that the service can determine it contains
        """

    @classmethod
    @abstractmethod
    def exists(cls, sub_location: str, root: Optional[str] = None, **kwargs) -> Optional[str]:
        """Check if an object exists.

        Given a filename/path within the service, return the full uri if it exists or None otherwise
        :param sub_location: The path of the file without the scoping of the service
                                e.g. 'blob_path.txt' instead of 'gs://bucket/blob_path.txt'
                                       or
                                     'subdir/myfile.txt' instead of '/basedir/subdir/myfile.txt'
        :param root: Convenience arg to search only below a specific root.
                                e.g. sub_location = 'blob_path.txt' and root = 'my_gcs_dir' then
                                    the method will search for 'my_gcs_dirt/blob_path.txt' within
                                    the backing file service and return the fully qualified path if
                                    found.
        :param kwargs: keyword args to be used by the underlying file service
        :return: full uri (e.g. 'gs://bucket/blob_path.txt') if it exists or None otherwise
        """

    @abstractmethod
    def available(self, **kwargs) -> Dict[UrlTypes, ObjectSvc]:
        """Return the available ways that the service can provide the file.

        A method that returns the available ways that the underlying ObjectSvc can provide the file.
        :param kwargs: keyword args to be used by the underlying file service
        :return: A dictionary mapping UrlTypes to ObjectSvc instances
        """

    @abstractmethod
    def download(self,
                 local_file: BinaryIO,
                 start: Optional[int] = None,
                 end: Optional[int] = None,
                 **kwargs) -> BinaryIO:
        """Download an instance of a storage object to a provided BinaryIO instance.

        Each service should download the file according to the implemented downloader and return
        the new location of the downloaded file.

        Some services might support downloading only part of the object, in which case they should
        use the optional `start` and `end` parameters to determine which part of the object to
        download.

        :param local_file: a file like object to download to
        :param start: (if supported) the first byte in a range to be downloaded
        :param end: (if supported) the last byte in a range to be downloaded
        :param kwargs: keyword args to be used by the underlying file service
        :return: The io file with content written to it
        """

    @abstractmethod
    def download_as_bytes(self,
                          start: Optional[int] = None,
                          end: Optional[int] = None,
                          **kwargs) -> bytes:
        """Retrieve the contents of the file as bytes.

        Some services might support downloading only part of the object, in which case they should
        use the optional `start` and `end` parameters to determine which part of the object to
        download.

        :param start: (if supported) the first byte in a range to be downloaded
        :param end: (if supported) the last byte in a range to be downloaded
        :param kwargs: keyword args to be used by the underlying file service
        :return: The file as bytes
        """

    def replace(self, replacement: ObjectSvc, **kwargs):
        """Replace the content of the storage object with another storage object.

        Replaces the underlying data represented by this storage object svc instance
        with the data from another storage object svc instance.

        :param replacement: The replacement storage object.
        :param kwargs: keyword args to be used by the underlying file service
        :return: None
        """

    @abstractmethod
    def delete(self, **kwargs) -> None:
        """Delete the underlying data represented by this storage object instance.

        :param kwargs: keyword args to be used by the underlying file service
        :return: None
        """

    @property
    @abstractmethod
    def user_url(self) -> str:
        """Return a user consumable url for downloading the storage object.

        :return: A url representation of the file location for the user
        """

    def user_upload_url(self, **kwargs) -> str:
        """Return a user consumable url for uploading data to the storage object.

        :param kwargs: keyword args to be used by the underlying file service
        :return: A url that the user can use to upload data with a PUT request.
        """

    @property
    @abstractmethod
    def info(self) -> Dict[str, str]:
        """Information about the storage object.

        :return: A dictionary of all information the service can determine about the storage object
        """

    @abstractmethod
    def refresh_info(self, **kwargs) -> Dict[str, str]:
        """Refresh the information about the storage object.

        :param kwargs: keyword args to be used by the underlying file service
        :return: A dictionary of all information the service can determine about the storage object
        """


class ObjectIngestSvc(ABC):
    """An ObjectSvc that ingests and builds instances of ObjectSvc.

    A special factory class for ObjectSvc instances that handles moving files into a specific
    ObjectSvc backend using the `.ingest()` method.
    """

    BASE_SVC: Type[ObjectSvc]

    def __init__(self, base_svc: Optional[Type[ObjectSvc]] = None):
        """Construct an ingestion service class.

        The constructor takes a base ObjectSvc which can be passed by the end-user, or dynamically
        with a call to super().

        :param base_svc: Optionally override the base service (note: it is up to the developer to
        determine that the ObjectSvc implementation works with the ObjectIngestSvc implementation).
        """
        self._base_svc: Type[ObjectSvc]

        if base_svc is not None:
            self._base_svc = base_svc

    @property
    def base_svc(self) -> Type[ObjectSvc]:
        """Return the service class of which an instance will be built when ingest is called.

        :return: The ObjectSvc class the file will be moved to
        """
        return self._base_svc

    @abstractmethod
    def ingest(self, ext_file: ObjectSvc, **kwargs) -> ObjectSvc:
        """Build an ObjectSvc instance from the provided ObjectSvc arg and return it.

        A factory method to build a ObjectSvc representing a file that is internal to the system
        from a ObjectSvc instance representing a file external to the system.

        :param ext_file:
        :param kwargs: keyword args to be used by the ingestion service
        :return: An instance of a ObjectSvc after representing the file after being moved
        """

    def generate_internal_name(self,
                               filename: Optional[str] = None,
                               **kwargs) -> str:
        """Format the name of the ingested object.

        A template method to override generation of internal file names

        :param filename: The base filename prior to ingestion of the file
        :param kwargs: To be used to pull in extra information to be used in the naming process
        :return: The internal name of the file to use
        """
