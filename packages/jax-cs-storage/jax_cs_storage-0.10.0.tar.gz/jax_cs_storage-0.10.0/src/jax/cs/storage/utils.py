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

"""Utility methods used by this package internally."""

import importlib
import logging

from types import ModuleType
from typing import Tuple, List, Optional

# TODO: Remove when reviewed for external package use
# from typing import List
# def try_to_add_import(to_add_to: List, module_name: str):
#     import importlib
#     try:
#         mod = importlib.import_module(module_name)
#         to_add_to.append(mod)
#     except ImportError:
#         pass
#     return to_add_to


def opt_get_module(module_name) -> Optional[ModuleType]:
    """Silently fail on module imports.

    :param module_name: The name of the module to import.
    :return: The module, if imported otherwise None.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        logging.error(e)
        return None


def get_available_svcs(services: List[Tuple[str, str]]) -> List:
    """Import and return only the items whose import doesn't cause an ImportError or AttributeError.

    :param services: The first item in the tuple is the python import style module location, and
    the second is the name of the item to import from that module.
    :return: A list of the services that could be imported from their corresponding module.
    """
    ret = []
    for svc in services:
        mod_name, svc_name = svc
        try:
            mod = opt_get_module(mod_name)
            ret.append(getattr(mod, svc_name))
        except (ImportError, AttributeError):
            logging.warning(f"jax.cs.storage could not import service: {svc_name}")
            continue
    return ret
