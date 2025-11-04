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

"""Module to hold implementations of object service classes."""


import json
import datetime
from typing import BinaryIO, Union, Set, Tuple, Optional

from google.cloud.storage import Client, Bucket, Blob
from google.oauth2.service_account import Credentials


def get_client_credential_content(credential) -> Client:
    """Get a client object for GCS, using environment variable credentials.

    :param credential: The credential content to use.
    """
    credential_data = json.loads(credential)
    creds = Credentials.from_service_account_info(credential_data)
    return Client(credentials=creds)


def get_client(credential_content: Optional[str] = None) -> Client:
    """Get a client object for GCS, using environment variable credentials.

    :param credential_content: The credential content to use, otherwise uses
                                GOOGLE_APPLICATION_DEFAULT.
    :return: A Google storage client instance.
    """
    if credential_content is not None:
        storage_client = get_client_credential_content(credential_content)
    else:
        storage_client = Client()
    return storage_client


def get_bucket(bucket_name: str, client: Client) -> Bucket:
    """Get a bucket object for GCS.

    :param bucket_name: The name of the bucket to get (without the gs://)
    :param client: a Google storage client instance
    :return: A Google storage bucket instance.
    """
    return client.bucket(bucket_name)


def get_bucket_and_client(bucket_name: str,
                          credential_content: Optional[str] = None
) -> Tuple[Bucket, Client]:
    """Get a bucket and client object for GCS.

    :param bucket_name: The name of the bucket to get (without the gs://)
    :param credential_content: The credential content to use, otherwise uses
                                GOOGLE_APPLICATION_DEFAULT.
    :return: tuple of (bucket, client)
    """
    storage_client = get_client(credential_content)
    bucket = get_bucket(bucket_name, storage_client)
    return bucket, storage_client


def validate_url(gs_uri: str,
                 check_exists=None,
                 client: Optional[Client] = None) -> bool:
    """Validate that a given url is a GCS url.

    :param gs_uri: the path to validate
    :param check_exists: flag to check if the path actually exists
    :param client: a Google storage client instance
    """
    if gs_uri.startswith('gs://'):
        if check_exists is True:
            return check_gs_path_exists(gs_uri, client)
        else:
            return True
    else:
        return False


def check_gs_path_exists(gs_uri: str, client: Optional[Client] = None):
    """Check that a provided google cloud storage url refers to an object that exists.

    :param gs_uri: the path to validate
    :param client: a Google storage client instance
    :return: true if an object exists at the url, false otherwise
    """
    bucket_exists = False
    storage_client = Client() if client is None else client

    try:
        bucket_name, file_name, blob_name = split_gs_uri(gs_uri)
    except AttributeError:
        return bucket_exists

    bucket = storage_client.bucket(bucket_name)

    try:
        bucket_exists = bucket.exists()
    except ValueError:
        pass

    if bucket_exists and file_name:
        blob = bucket.get_blob(blob_name)
        return blob is not None
    else:
        return bucket_exists


# TODO: Evaluate the necessity of this method and if it should be removed
# def check_blob_exists(bucket_name, blob_name, client=None):
#     storage_client = Client() if client is None else client
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.get_blob(blob_name)
#     return blob.exists()


def split_gs_uri(gs_uri: str) -> Tuple[str, str, str]:
    """Split a gs uri into (bucket, filename, blob).

    :param gs_uri: the uri to split
    """
    try:
        split = gs_uri.split('/')
        return split[2], split[-1], '/'.join(split[3:])
    except IndexError:
        raise AttributeError("Provided url could not be split as a gs url")


# TODO: Evaluate the necessity of this method and if it should be removed
# def download_blob_from_url(client: Client, url: str, dst_file_path: str):
#     with open(dst_file_path) as dst:
#         client.download_blob_to_file(url, dst)


def gs_path_from_blob(blob: Blob) -> str:
    """Determine the full gs URI of a blob.

    :param blob: The blob we want the URI for.
    :return: The blob's full URI.
    """
    return f"gs://{blob.bucket.name}/{blob.name}"


def upload_string_to_bucket_loaction(bucket: Bucket,
                                     data: Union[str, bytes],
                                     content_type: str,
                                     destination_blob_name: str,
                                     **kwargs) -> str:
    """Upload a string/bytes obj to a GCS bucket.

    :param bucket: the GCS bucket object to upload the file to
    :param data: the data to upload, something like `response.content`
    :param content_type: the content type, same as `response.headers['content-type']`
    :param destination_blob_name: what to name the file in the bucket
    :return:
    """
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(data, content_type=content_type, **kwargs)
    return gs_path_from_blob(blob)


def upload_file_to_bucket_location(bucket: Bucket,
                                   source_file_name: str,
                                   destination_blob_name: str,
                                   **kwargs) -> str:
    """Upload an io file to a GCS bucket.

    :param bucket: the GCS bucket object to upload the file to
    :param source_file_name: the path location of the io file
    :param destination_blob_name: what to name the file in the bucket
    :return: the GCS path of the uploaded file
    """
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name, **kwargs)
    return gs_path_from_blob(blob)


def copy_object_within_gcs(src_bucket: Bucket, src_blob_name: str,
                           dst_bucket: Bucket, dst_blob_name: str, delete=False) -> str:
    """Copy an Object from one GCS location to another.

    :param src_bucket: The bucket containing the source object
    :param src_blob_name: The blob name of the source object
    :param dst_bucket: The bucket to contain the destination object
    :param dst_blob_name: The name of the object to be created in the destination bucket
    :param delete: Flag to delete the source file upon copy completion.
    :return:
    """
    src_blob = src_bucket.blob(src_blob_name)
    dst_blob = src_bucket.copy_blob(src_blob, dst_bucket, dst_blob_name)
    if delete:
        src_bucket.delete_blob(src_blob_name)
    return gs_path_from_blob(dst_blob)


def move_object_within_gcs(src_bucket: Bucket, src_blob_name: str,
                           dst_bucket: Bucket, dst_blob_name: str, **kwargs) -> str:
    """Move an Object from one GCS location to another.

    This is an alias for `copy_object_within_gcs(*args, delete=True)`

    :param src_bucket: The bucket containing the source object
    :param src_blob_name: The blob name of the source object
    :param dst_bucket: The bucket to contain the destination object
    :param dst_blob_name: The name of the object to be created in the destination bucket
    :return:
    """
    return copy_object_within_gcs(src_bucket, src_blob_name,
                                  dst_bucket, dst_blob_name, delete=True)


def generate_signed_url(blob: Blob, expiration=None) -> str:
    """Generate a v4 signed URL for uploading a blob using HTTP PUT.

    Note that this method requires a service account key file. You can not use
    this if you are using Application Default Credentials from Google Compute
    Engine or from the Google Cloud SDK.

    See:
     - https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#upload-object

    :param blob:
    :param expiration:
    :return:
    """
    expiration = expiration or 24
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=expiration),
        method="GET"
    )


def generate_signed_upload_url(blob: Blob,
                               expiration: Optional[int] = None,
                               content_type: Optional[str] = None):
    """Return a user consumable url for uploading data to the storage object.

    :param expiration: How long the signed url is valid for, in hours.
    :param content_type: The content type of the data to upload, client must set this
    to match.
    :return: A url that the user can use to upload data with a PUT request.
    """
    expiration = expiration or 1
    content_type = content_type or 'application/octet-stream'
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=expiration),
        method="PUT",
        content_type=content_type
    )

# TODO: Evaluate the necessity of this method and if it should be removed
# def download_blob(bucket: Bucket, blob_name, local_file: BinaryIO) -> BinaryIO:
#     bucket.blob(blob_name).download_to_file(local_file)
#     return local_file


def download_blob_by_uri(client: Client,
                         uri: str,
                         local_file: BinaryIO,
                         start: Optional[int] = None,
                         end: Optional[int] = None) -> BinaryIO:
    """Download a blob with nothing but a URI and local file instance.

    :param client: a Google storage client instance
    :param uri: The URI of the Google cloud storage object to download
    :param local_file: The IO to download to
    :param start: the first byte in a range to be downloaded
    :param end: the last byte in a range to be downloaded
    :return: The provided IO after downloading
    """
    client.download_blob_to_file(uri, local_file, start=start, end=end)
    return local_file


def download_as_bytes(client: Client,
                      gs_uri: str,
                      start: Optional[int] = None,
                      end: Optional[int] = None) -> bytes:
    """Given a client and a gs_uri, download and return the contents of the gs_uri as bytes.

    :param client: a Google storage client instance
    :param gs_uri: the absolute gs uri of the object to download
    :param start: the first byte in a range to be downloaded
    :param end: the last byte in a range to be downloaded
    :return: the contents of the object at the gs_uri as bytes
    """
    bucket_name, file_name, blob_name = split_gs_uri(gs_uri)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes(start=start, end=end)


def all_files(bucket_name,
              prefix=None,
              full_gs_path=True,
              client: Optional[Client] = None) -> Set[str]:
    """List all files at the provided location.

    :param bucket_name: Name of the bucket
    :param prefix: Prefix to apply to the objects
    :param full_gs_path: The full path to search for.
    :return: A set of all the objects at the location.
    :param client: a Google storage client instance
    """
    storage_client = Client() if client is None else client
    if full_gs_path:
        return {f"gs://{bucket_name}/{blob.name}" for blob in
                storage_client.list_blobs(bucket_name, prefix=prefix)}
    else:
        return {blob.name for blob in
                storage_client.list_blobs(bucket_name, prefix=prefix)}


def delete_blob(blob: Blob):
    """Delete a blob from GCS.

    :param blob: The blob to delete.
    """
    blob.delete()


# TODO: Evaluate the necessity of this method and if it should be removed
# def find_subfolder(bucket_name, prefix=None):
#     folders = set()
#
#     storage_client = Client()
#     blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
#     for blob in blobs:
#         # print(blob.name)
#         name = blob.name
#         parts = name.split('/')
#         folder_name = parts[0] if prefix is None else parts[1]
#         folders.add(folder_name)
#
#     return folders


# TODO: Evaluate the necessity of this method and if it should be removed
# def find_file(bucket_name, metadata_file_name, prefix=None):
#     metadata_files = []
#
#     storage_client = Client()
#     blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
#     prefix_len = len(prefix)
#     for blob in blobs:
#         name = blob.name
#         if name.endswith(metadata_file_name):
#             if prefix is None:
#                 metadata_files.append(name)
#             else:
#                 metadata_files.append(name[prefix_len:])
#     return metadata_files


# TODO: Evaluate the necessity of this method and if it should be removed
# def find_file_startswith(bucket_name, file_name_startswith, bucket_folder_prefix=None):
#     files = []
#
#     storage_client = Client()
#     blobs = storage_client.list_blobs(bucket_name, prefix=bucket_folder_prefix)
#     prefix_len = len(bucket_folder_prefix)
#     for blob in blobs:
#         name = blob.name
#         if name.endswith("/"):
#             continue
#         parts = name.split("/")
#         last = parts[-1]
#
#         if last and last.startswith(file_name_startswith):
#             files.append(name)
#     return files
