# Matrix server sanity checker
# ©Sebastian Spaeth & contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Optional
import re
# User Agent and possibly other required headers that we need for all requests
req_headers = {"User-Agent": "Mozilla/5.0 (Linux; x64)"}
DOMAIN = re.compile(r"(?P<prefix>https://.*?)\w*\.\w{2,}(?P<URL>/)",
                    re.IGNORECASE)

def anonymize(logoutput:str, servername:Optional[str]=None) -> str:
    """strip out domain names"""
    if servername:
        return logoutput.replace(servername, "CENSORED.COM")
    else:
        return DOMAIN.sub(r"\g<1>CENSORED.COM\g<2>", logoutput)
