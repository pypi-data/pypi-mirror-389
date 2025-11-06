# Mautrix server sanity checker
# ©Sebastian Spaeth & contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import argparse
import logging
import requests
from typing import Optional

from .utils import req_headers, anonymize


class JWTAuth:
    """A JWT Auth server"""
    def __init__(self, baseurl: str, anon: bool=False):
        assert baseurl.startswith("https://"), \
            "JWT auth baseurl should always start with 'https://'"
        self.baseurl = baseurl
        # Function that can be used to anonymize domain output
        if anon:
            self.loganon = anonymize
        else:
            #NOP, just return log unchanged
            self.loganon = lambda logoutput, servername=None: logoutput


    def test_health(self) -> bool:
        try:
            url = f"{self.baseurl}/healthz"
            r = requests.get(url, headers = req_headers)
        except requests.exceptions.SSLError as e:
            logging.error("𐄂 SSL error connecting to %s: %s", url, e)
        except requests.exceptions.ConnectionError as e:
            if ("[Errno 11001] getaddrinfo failed" in str(e) or     # Windows
                "[Errno -2] Name or service not known" in str(e) or # Linux
                "[Errno 8] nodename nor servname " in str(e)):      # OS X
                s = f"𐄂 DNS Error resolving host {self.baseurl}"
                logging.error(s)
        else:
            logging.debug("  JWTauth healtz url: %s", self.loganon(self.baseurl))
            if r.status_code == 404:
                logging.warning("𐄂 jwtauth healthz endpoint does not exist at %s (404)",
                                self.loganon(url))
            elif r.status_code != 200:
                logging.error("𐄂 jwtauth healthz http error %s",
                              r.status_code)
            else:
                #status code 200, all is well!
                if not "Access-Control-Allow-Origin" in r.headers:
                    logging.debug("  jwt has no CORS header (that is OK)")
                logging.info("✔ JWTauth responds")
                return True
        return False

    def test_sfuget(self, mserver: Optional['MatrixServer'] = None, # type: ignore
                    token: Optional[str] = None) -> bool:
        """token is the Openid token"""
        res = True

        # First test as unauthed user
        try:
            url = f"{self.baseurl}/sfu/get"
            r = requests.get(url, headers = req_headers)
        except requests.exceptions.SSLError as e:
            logging.error("SSL error connecting to %s: %s", url, e)
            res = False
        except requests.exceptions.ConnectionError as e:
            # 1) Windows 2) # Linux 3) # OS X
            if ("[Errno 11001] getaddrinfo failed" in str(e) or
                "[Errno -2] Name or service not known" in str(e) or
                "[Errno 8] nodename nor servname " in str(e)):
                s = f"𐄂 DNS Error resolving host {self.loganon(self.baseurl)}"
                logging.error(s)
                res = False
        else:
            if not "Access-Control-Allow-Origin" in r.headers:
                logging.debug("  jwt has no CORS header (that is OK)")
            if r.status_code == 405:
                logging.debug("✔ jwt /sfu/get without auth returns (405). This is good!")
            else:
                logging.error("𐄂 jwt /sfu/get without aut returns (%d)",
                              r.status_code)
                res = False

        if not res:
            logging.warning("𐄂 jwt /sfu/get (unauth) failed (BAD), not trying anything else")
            return res
        elif not (mserver and token):
            logging.debug("  jwt: no credentials passed, not trying authed requests")
            return res

        # Next, test as authed user
        data = {"room":f"!DFGDFG:{mserver.servername}",
                "openid_token":
                  {"access_token": token,
                   "expires_in":3600,
                   "matrix_server_name": mserver.servername,
                   "token_type":"Bearer"},
                  "device_id":"1234"}
        try:
            url = f"{self.baseurl}/sfu/get"
            r = requests.post(url, headers = req_headers, json=data)
        except requests.exceptions.ConnectionError as e:
            if ("[Errno 11001] getaddrinfo failed" in str(e) or     # Windows
                "[Errno -2] Name or service not known" in str(e) or # Linux
                "[Errno 8] nodename nor servname " in str(e)):      # OS X
                s = f"𐄂 DNS Error resolving host {self.loganon(self.baseurl)}"
                logging.error(s)
                res = False
        else:
            if r.status_code != 200:
                logging.error("𐄂 /sfu/get (auth) returned unexpected result (%d): %s", r.status_code, r.text)
                return False
            # YAY! success
            s="✔ /sfu/get succeeded. Use the below information to test your livekit SFU on https://livekit.io/connection-test\n  %s"
            logging.info(s, r.text)
        return res
