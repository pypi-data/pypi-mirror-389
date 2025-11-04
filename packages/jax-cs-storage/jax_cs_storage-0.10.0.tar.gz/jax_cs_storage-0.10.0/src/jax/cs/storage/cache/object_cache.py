"""A default object cache implementation."""

import os
import pickle
import typing


from jax.cs.storage import init
from jax.cs.storage.object.services.gcs import ObjectIngestSvcGCS
from jax.cs.storage.object.services.io import ObjectIngestSvcIO
from jax.cs.storage.config import StorageConfig


class ObjectCache:
    """Class for saving and loading objects from a cache."""

    def __init__(self, use_gcs: bool = True,
                 wrapper_config: typing.Optional[typing.Dict] = None):
        """Initialize a new or existing cache.

        :param use_gcs: if True, use Google Cloud Storage backend
        :param wrapper_config: optional parameter to configure the
        jax-cs-filewrapper backend used for storing the cache files. By
        default, the configuration is set through a .env file or environment
        variables.
        """
        self._use_gcs = use_gcs

        # configure the default ingestion service for the filewrapper module
        ingestion_svc = ObjectIngestSvcGCS if use_gcs else ObjectIngestSvcIO

        if wrapper_config is None:
            # get the configuration from the environment
            self._FileWrapper, self._FileIngester = init(
                ingestion_svc=ingestion_svc
            )
        else:
            # optional dict with configuration values for jax.cs.filewrapper
            # has been passed for has been passed in. use that to manually
            # configure file wrapper
            self._FileWrapper, self._FileIngester = init(
                StorageConfig.parse_obj(wrapper_config),
                ingestion_svc=ingestion_svc
            )

        self._BackendFileSvc = self._FileIngester.resulting_svc()

        # if using local, make sure the directory exists
        if use_gcs:
            if self._BackendFileSvc.CONFIG.GCS_BUCKET is None:
                raise RuntimeError("JAX_CS_STORAGE_GCS_BUCKET "
                                   "environment variable not defined")

        elif not os.path.exists(self._BackendFileSvc.CONFIG.IO_FILE_ROOT):
            raise RuntimeError("Local object cache directory does not exist")

    def save(self, obj: object, filename: str) -> None:
        """Save an object to the cache.

        :param obj: Python object to save (must be 'pickleable')
        :param filename: filename to save the object to in the cache
        :return: None
        """
        self._FileIngester(pickle.dumps(obj), from_memory=True).ingest(
            filename=filename, content_type='application/octet-stream')

    def load(self, filename: str) -> typing.Any:
        """Load an object from the cache.

        :param filename: filename for the object in the cache
        :return: Python object
        :raises: FileNotFound error if filename does not exist in cache
        """
        path = self._BackendFileSvc.exists(filename)
        if path is None:
            raise FileNotFoundError

        wrapped = self._FileWrapper(path)
        return pickle.loads(wrapped.download_as_bytes())

    def delete(self, filename: str) -> None:
        """Delete a file from the cache.

        :param filename: filename to delete
        :return: None
        """
        # TODO at the time of development, jax-cs-filewrapper hasn't implemented
        #  the delete method
        # delete not yet implemented in cs-file-wrapper
        pass

    def check_if_exists(self, filename: str) -> bool:
        """Check if a file exists in the object cache.

        :param filename: filename of cached object
        :return: true of file found in cache, false otherwise
        """
        return self._BackendFileSvc.exists(filename) is not None

    def cache_listing(self) -> typing.Set[str]:
        """List objects in the cache.

        :return: The objects in the cache.
        """
        listing = self._BackendFileSvc.all()
        if not self._use_gcs:
            # for local files we want to remove the fully qualified path and
            # have just the files relative to the root directory
            root_dir = self._BackendFileSvc.CONFIG.IO_FILE_ROOT
            if not root_dir.endswith(os.path.sep):
                root_dir = root_dir + os.path.sep

            listing = {
                f.replace(root_dir, '') for f in listing
            }
        return listing
