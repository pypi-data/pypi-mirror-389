# Matrix server sanity checker
# ©Sebastian Spaeth & contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from .matrixserver import MatrixServer
from .jwtauth import JWTAuth

__version__ = "0.2.0"
__all__ = ["MatrixServer", "JWTAuth"]

# User Agent and possibly other required headers that we need for all requests
req_headers = {"User-Agent": "Mozilla/5.0 (Linux; x64)"}

