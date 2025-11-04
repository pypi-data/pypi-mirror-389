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

import logging
import shutil
import requests
from enum import Enum
from typing import Type, BinaryIO
from urllib.parse import urlparse


from jax.cs.storage.exceptions import ApiAuthError


def get_url_json_or_error(url, auth_header):
    """Return the json from a GET on a url, ohterwise raise a standard error.

    A helper method to return json of a response if the status is not in the 4xx or 5xx range.
    :param url:  The url to get
    :param auth_header: The auth header to use
    :raises ApiAuthError: if the response status != 200
    :return: The json of the response
    """
    resp = requests.get(url, headers=auth_header)
    if resp.ok:
        return resp.json()
    raise ApiAuthError(f'R2 returned status [{resp.status_code}] on GET: {resp.content}')


def get_file_from_fileset_by_name(file_set, name_contains: str, auth_header: dict):
    """Get the first file in a file_set where `name_contains` is in the file's name.

    :param file_set: The array of file urls
    :param name_contains: The string the file name should contain
    :param auth_header: The auth header to use
    :return: file url if found, otherwise None
    """
    file_url = None
    for file_url in file_set:
        resp = get_url_json_or_error(file_url, auth_header)
        if name_contains in resp.get('name', ''):
            file_url = file_url
            break
    return file_url


def get_file_from_data_object_by_name(dataobject_url, name_contains: str, auth_header: dict):
    """Get the first file in a data_object where `name_contains` is in the file's name.

    :param dataobject_url: The array of file urls
    :param name_contains: The string the file name should contain
    :param auth_header: The auth header to use
    :return: file url if found, otherwise None
    """
    resp = get_url_json_or_error(dataobject_url, auth_header)
    file_url = get_file_from_fileset_by_name(resp.get('file_set', []),
                                             name_contains=name_contains,
                                             auth_header=auth_header)
    if not file_url:
        logging.error(f"Data object has no file with {name_contains} in the name")
        raise ApiAuthError(f"Data object has no file with {name_contains} in the name")

    return file_url


# NOTE: name_enum is of type Type[Enum] to specify that the input is a subclass of Enum
# - https://www.python.org/dev/peps/pep-0484/#the-type-of-class-objects
def get_files_from_fileset_by_name(file_set, name_enum: Type[Enum], auth_header: dict):
    """Get all files in a file_set where one of `name_enum.values()` is in the file's name.

    Quits when it's looked at all the files, or has a file for each enum.
    :param file_set: The array of file urls
    :param name_enum: An enum whose values are used to match the name, the
    matched enum is returned in a tuple with along with the file_url
    :param auth_header: The auth header to use
    :return: list of tuples of the file url and enum type, if found, otherwise None
    """
    file_urls = []
    enum_values = [v.value for v in name_enum.__members__.values()]

    for file_url in file_set:
        resp_dict = get_url_json_or_error(file_url, auth_header)
        name = resp_dict['name']
        for v in enum_values:
            if v in name:
                file_urls.append((file_url, v))
                break
        if len(file_urls) == len(name_enum):
            break

    return file_urls


def get_files_from_data_object_by_name(dataobject_url, name_enum: Type[Enum], auth_header: dict):
    """Get files from a data object.

    A convenience method to get files from a data object, will call `get_url_json_or_error` and
    `get_files_from_fileset_by_name`.
    :param dataobject_url: The url of the data object with the file_set of files to get
    :param name_enum: An enum whose values are used to match the name, the
    matched enum is returned in a tuple with along with the file_url
    :param auth_header: The auth header to use
    :return: list of tuples of the file url and enum type, if found, otherwise None
    """
    resp = get_url_json_or_error(dataobject_url, auth_header)
    return get_files_from_fileset_by_name(resp.get('file_set', []),
                                          name_enum=name_enum,
                                          auth_header=auth_header)


def validate_url(url, r2_base_url):
    """Validate that a string is a url.

    :param url: Url to validate
    :return: bool representing if the string was a url
    """
    result = urlparse(url)
    netloc = urlparse(r2_base_url).netloc
    return all(
        [result.scheme, result.scheme == 'https', result.netloc == netloc])


def download_file(https_url: str, local_file: BinaryIO):
    """Download the contents of an https location to an io instance.

    :param https_url: The url location of the file to download
    :param local_file: The io instance to download to
    :return: The provided io instance
    """
    logging.info(f"Downloading {https_url}")
    with requests.get(https_url, stream=True) as request:
        shutil.copyfileobj(request.raw, local_file)
    return local_file
