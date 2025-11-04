# Don't manually change, let poetry-dynamic-versioning-plugin handle it.
__version__ = "1.2.0"

__all__ = [
    "CannotDeriveNameError",
    "CannotRegisterPythonBuiltInError",
    "InvalidNameError",
    "KeyCollisionError",
    "ModuleAliasError",
    "Registry",
    "RegistryError",
    "RegistryMeta",
    "InternalError",
]

from ._registry import Registry, RegistryMeta
from .exceptions import (
    CannotDeriveNameError,
    CannotRegisterPythonBuiltInError,
    InternalError,
    InvalidNameError,
    KeyCollisionError,
    ModuleAliasError,
    RegistryError,
)
