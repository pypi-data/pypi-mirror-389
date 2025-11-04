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

"""A namespace of exceptions used by this package.

WARNING: This is likely to change as this interface redesigned and refactored!

TODO: Redesign and refactor this file to better reflect how exceptions should be
    handled throughout the rest of the package. Make sure to document the ABCs
    as to how they expect their implementations to handle exceptions.
"""


class BaseError(BaseException):
    """The root of all exceptions in this package."""


class ApiError(BaseError):
    """Used for when the package runs into an error connecting to another service."""


class NotFoundError(ApiError):
    """For when a referenced object can't be found."""


class ApiAuthError(BaseError):
    """For when a referenced object can't be accessed due to auth problems."""
