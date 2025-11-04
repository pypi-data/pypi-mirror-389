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

"""The configuration class and default settings for the jax.cs.storage package."""

import base64
from typing import Optional

from pydantic import AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    """The pydantic configuration class definition for the jax.cs.storage package."""

    LOG_LEVEL: str = 'DEBUG'

    GCS_CREDENTIALS_B64_DECODE: bool = True
    GCS_CREDENTIALS_CONTENTS: Optional[str] = None

    GCS_BUCKET: Optional[str] = None
    GCS_PREFIX_DIR: Optional[str] = None
    GCS_URL_EXPIRE_HOURS: int = 24
    GCS_URL_UPLOAD_EXPIRE_HOURS: int = 1
    GCS_CHECK_BLOB_EXISTS: bool = False

    R2_BASE_URL: AnyHttpUrl = AnyHttpUrl('https://r2.jax.org')
    IO_FILE_ROOT: Optional[str] = '/'

    @model_validator(mode="after")
    def base64_decode_gcs_credentials(self):
        """Decode the GCS credentials if the flag is set."""
        if self.GCS_CREDENTIALS_B64_DECODE and self.GCS_CREDENTIALS_CONTENTS:
            self.GCS_CREDENTIALS_CONTENTS = base64.b64decode(self.GCS_CREDENTIALS_CONTENTS).decode('utf-8')
        return self

    model_config = SettingsConfigDict(
        env_prefix='JAX_CS_STORAGE_',
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


default_settings = StorageConfig()
