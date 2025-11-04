import os
import uuid
from contextlib import contextmanager
from typing import Type, Optional, Sequence, BinaryIO, List

from .abstract import FileSvc

class NoOpDownloader(FileSvc):
    """
    An extension of Downloader class that matches all files. Used as the default downloader for
    files that match no other configured downlaoder.
    """

    @classmethod
    def validate(cls, location: str):
        """
        All files are valid for the NoOpDownloader.
        :param location: the uri/url of the file to validate
        """
        return True


class Localizer:
    """
    A class to help organize the downloads of multiple types files in a single arbitrarily nested
    python datasetructure.
    """

    FILE_JOIN_CHAR = '_'

    def __init__(self,
                 root: str,
                 downloaders: Sequence[Type[FileSvc]],
                 no_match: Optional[Type[FileSvc]] = None,
                 **kwargs
                 ):
        self.root = root
        self.downloaders = downloaders
        self.kwargs = kwargs
        self.no_match_downloader = NoOpDownloader if no_match is None else no_match

    def localize_json_dict(self, inputs: dict):
        """
        Given a python dictionary representing a json object, iterate through it to localize each
        file that it references.
        """
        for k, v in inputs.items():
            inputs[k] = self.smart_process(k, v)
        return inputs

    def smart_process(self, key, value, keychain: Sequence = None):
        """
        Given a value that's either a list, a dict, a string, or something else, determine what
        should be done with it. All values are processed further except for "something else" which
        is returned as is.
        """
        keychain = [] if keychain is None else keychain
        if type(value) is list:
            return [i for i in self.process_list(value, keychain)]
        elif type(value) is dict:
            return {k: v for k, v in self.process_dict(value, keychain)}
        elif type(value) is str:
            return self.process_str(key, keychain)
        else:
            return key, value

    def process_list(self, item: list, keychain: List):
        """
        Given a list with nested input files to download, iterate over the list
        and process the items within it
        :param keychain:
        :param item: a python list with nested input files to be downloaded
        """
        for elem in item:
            yield self.smart_process(elem, keychain + ['1'])

    def process_dict(self, item: dict, keychain: List):
        """
        Given a dict with nested input files to download, iterate over the dict
        and process the items within it
        :param keychain:
        :param item: a python dict with nested input files to be downloaded
        """
        for k, v in item.items():
            yield k, self.smart_process(v, keychain + [k])

    def process_str(self, item: str, keychain: List):
        """
        Given a string representation of an item location, download it
        :param keychain:
        :param item: The string location of the item to process
        """
        d = self.select_downloader(item)(item, **self.kwargs)
        # return d.download(self.__get_file_io())

    def select_downloader(self, item: str) -> Type[FileSvc]:
        """
        Given a uri/url item location, select the first downloader defined
        in this instance that validates the item.
        :param item: The string location of the item to select downloader for
        """
        downloader = self.no_match_downloader
        for d in self.downloaders:
            if d.validate(item):
                downloader = d
                break

        return downloader

    def download(self, item: str):
        """
        An alias for `process_str`
        :param item: The string location of the item to download
        """
        return self.process_str(item)

    # @classmethod
    # def generate_local_name(cls, keychain: List[str], file_info: Optional[dict] = None):
    #     kc = keychain.copy()
    #     try:
    #         kc.append(file_info['name'])
    #     except KeyError:
    #         kc.append(uuid.uuid4().hex)
    #     f_name = cls.FILE_JOIN_CHAR.join(keychain)
    #     r_name = file_info.get('name')
    #     if r_name:
    #         f_name =
    #     return os.path.join(self.root, )
    #     ...

    # @contextmanager
    # def file_io(self, file_path=None) -> BinaryIO:
    #     file_path = self.__generate_local_name() if file_path is None else file_path
    #     try:
    #         yield ...
    #     finally:
    #
    #     ...
