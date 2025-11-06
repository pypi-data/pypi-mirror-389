"""
Coremail SDK for Python
A library for interacting with Coremail XT API
"""
from .client import CoremailClient
from .typings import *

__version__ = "0.1.0"
__all__ = [
    "CoremailClient",
    "TokenResponse",
    "AuthenticateResponse", 
    "GetAttrsResponse",
    "UserAttributes",
    "CoremailConfig",
    "AddAliasResponse",
    "DeleteAliasResponse",
    "GetAliasResponse"
]