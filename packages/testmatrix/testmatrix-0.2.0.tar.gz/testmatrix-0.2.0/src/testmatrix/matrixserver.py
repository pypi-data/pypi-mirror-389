# Matrix server sanity checker
# ©Sebastian Spaeth & contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import argparse
import logging
import requests
from os import urandom
from typing import Optional

from .utils import req_headers, anonymize
from .jwtauth import JWTAuth

class MatrixServer:
    """
    A Matrix server (that we want to test)

    notable instance attributes:
        .servername
        .federation_baseurl
        .client_baseurl
        .client_version: _matrix/client/versions as dict
        .livekits: list of livekit JWTAuth servers (or None)
    """
    livekits: Optional[list['JWTAuth']] = None # overriden by instance
    # suppress overly verbose python requests logging
    logging.getLogger("urllib3").setLevel(logging.INFO)

    def __init__(self, servername: str,
                 args: Optional[argparse.Namespace] = None,
                 diagnostics: bool = False) -> None:
        """params:
          servername:   (`str`) name of the server that we represent
          args: argsparse args which we can use (see test_matrix.py)
          diagnostics: whether we should output nice logs that inform the user
                       about results of our sanity checks.
        """
        self.args = args
        self.servername: str = servername.lower()
        self.federation_baseurl: str = ""
        self.client_baseurl: str = ""
        # result of client/versions as dict
        self.client_versions: Optional[dict] = None
        self.diagnostics = diagnostics
        self.livekits: Optional[list['JWTAuth']]
        # Function that can be used to anonymize domain output
        if args and args.anonymize:
            self.loganon = anonymize
        else:
            #NOP, just return log unchanged
            self.loganon = lambda logoutput, servername=None: logoutput

    @staticmethod
    def get_mxid_localpart(mxid: str):
        """Return the localpart of a full MXID"""
        if mxid[0] != "@":
            raise ValueError("MXID '{mxid}' does not start with @")
        return mxid[1:].split(':')[0]

    @staticmethod
    def get_mxid_servername(mxid: str):
        """Return the servername of a full MXID"""
        return mxid.split(':')[1]

    def parse_livekit_json(self, livekit_json: Optional[list]) \
            -> Optional[bool]:
        """Parses client well-known livekit parts and initiates self.livekits

        Returns True (success), False (no Livekit) or None (Error)"""
        self.livekits = []
        if livekit_json is None:
            self.livekits = None
            return False
        #json of wellknown_client["org.matrix.msc4143.rtc_foci"]
        for livekit in livekit_json:
            if type(livekit) != dict:
                logging.error("𐄂 well-known livekit entry is no array of dicts but a %s ?! Fishy", type(livekit))
                return None
            if not "type" in livekit or livekit["type"]!="livekit":
                logging.info("𐄂 non-Livekit SFU configured (type "
                              "'%s' !='livekit') ?!", livekit.get("type", ""))
                continue
            if not "livekit_service_url" in livekit:
                logging.info("𐄂 MatrixRTC SFU misses livekit_service_url")
                continue
            anon: bool = (self.args is not None) and self.args.anonymize
            self.livekits.append(JWTAuth(livekit["livekit_service_url"], anon))
            logging.debug("  Adding livekit service URL: %s",
                          livekit["livekit_service_url"])
        return len(self.livekits) > 0

    def get_server_baseurl(self) -> Optional[str]:
        """Queries federation endpoint base URL

        Returns and also stores the resulting baseurl in self.server_baseurl
        This should not be throwing exceptions, but returns None in case of
        failure"""
        wellknown_server = None
        try:
            url = f"https://{self.servername}/.well-known/matrix/server"
            r = requests.get(url, headers = req_headers)
            r.raise_for_status() # raise e.g. on 404
            wellknown_server = r.json()
        except requests.exceptions.SSLError as e:
            logging.error("𐄂 SSL error connecting to %s: %s", url, e)
            raise(e)
        except requests.exceptions.ConnectionError as e:
            if ("[Errno 11001] getaddrinfo failed" in str(e) or     # Windows
                "[Errno -2] Name or service not known" in str(e) or # Linux
                "[Errno 8] nodename nor servname " in str(e)):      # OS X
                s = "DNS Error resolving host %s" % \
                    self.loganon(self.servername, self.servername)
                logging.error(s)
                self.federation_baseurl = ""
                return self.federation_baseurl
        except requests.exceptions.HTTPError as e:
            if self.diagnostics:
                if e.response.status_code == 404:
                    logging.warning("𐄂 No server well-known exists (404)")
                else:
                    logging.error("𐄂 Server well-known error %s", str(e))
        except requests.exceptions.JSONDecodeError as e:
            if self.diagnostics:
                logging.error("𐄂 Server well known is no valid json")
        else:
            self.federation_baseurl = "https://" + wellknown_server["m.server"]
            if self.diagnostics:
                logging.debug("  Federation url: %s",
                              self.loganon(self.federation_baseurl,
                                           self.servername))
                logging.info("✔ Server well-known exists")

        # use default address in case of failed well-known
        if not self.federation_baseurl:
            self.federation_baseurl = f"https://{self.servername}:8448"
            if self.diagnostics:
                logging.info("  Assuming federation url: %s",
                             self.loganon(self.federation_baseurl,
                                          self.servername))

        return self.federation_baseurl


    def get_client_baseurl(self) -> str:
        """Queries client endpoint base URL

        Returns and also stores the resulting baseurl in self.client_baseurl
        This should not be throwing exceptions, but returns None in case of
        failure"""
        wellknown_client: dict = {}
        self.client_baseurl = ""
        try:
            url = f"https://{self.servername}/.well-known/matrix/client"
            # The .well-known file could sit behind redirects, and we need to
            # manually check the CORS headers for each redirect step. Standard
            # requests does not do this, so we need to do that manually. Sigh.
            # TODO: a candidate for factoring out.
            r = requests.get(url, headers = req_headers)
            r.raise_for_status() # raise on status 400-600
            if self.diagnostics:
                i = 0
                for redirect in r.history:
                    i += 1
                    if not "Access-Control-Allow-Origin" in redirect.headers:
                        logging.error("𐄂 Client well-known redirect #%d has no CORS header", i)
                    elif redirect.headers["Access-Control-Allow-Origin"] != "*":
                        logging.error("𐄂 Client well-known redirect #%d has no proper CORS header: '%s'",
                                      i,
                                      redirect.headers["Access-Control-Allow-Origin"])
                    else:
                        logging.info("✔ Client well-known redirect #%d has proper CORS header", i)
                if not "Access-Control-Allow-Origin" in r.headers:
                    logging.error("𐄂 Client well-known has no CORS header")
                elif r.headers["Access-Control-Allow-Origin"] != "*":
                    logging.error("𐄂 Client well-known has no proper CORS header: '%s'",
                                  r.headers["Access-Control-Allow-Origin"])
                else:
                    logging.info("✔ Client well-known has proper CORS header")

            wellknown_client = r.json()
        except requests.exceptions.ConnectionError as e:
            if ("[Errno 11001] getaddrinfo failed" in str(e) or     # Windows
                "[Errno -2] Name or service not known" in str(e) or # Linux
                "[Errno 8] nodename nor servname " in str(e)):      # OS X
                s = f"DNS Error resolving host {self.loganon(self.servername, self.servername)}"
                logging.error(s)
                return self.client_baseurl
        except requests.exceptions.HTTPError as e:
            if self.diagnostics and e.response.status_code == 404:
                logging.warning("𐄂 No client well-known exists (404)")
            elif self.diagnostics:
                logging.error("𐄂 Client well-known error %s", str(e))
        except requests.exceptions.JSONDecodeError as e:
            if self.diagnostics:
                logging.error("𐄂 Client well known is no valid json")
        else:
            self.client_baseurl = wellknown_client["m.homeserver"]["base_url"]
            if self.diagnostics:
                logging.debug("  Client url: %s",
                              self.loganon(self.client_baseurl,
                                           self.servername))

        if not self.client_baseurl:
            # use default address in case of previous error
            self.client_baseurl = f"https://{self.servername}"
            if self.diagnostics:
                logging.info("  Assuming client url: %s",
                             self.loganon(self.client_baseurl,
                                          self.servername))

        # warn if the client base_url is wrong (no https://)
        if not self.client_baseurl.lower().startswith("https://"):
            logging.warning("𐄂 Client well-known base_url "
                    f"'{self.client_baseurl}' does not start with https://")

        # Retrieve array of livekit instances or None
        livekit_json = wellknown_client.get("org.matrix.msc4143.rtc_foci",
                                            None)
        self.parse_livekit_json(livekit_json)
        return self.client_baseurl

    def get_server_version(self) -> str:
        try:
            url = f"{self.federation_baseurl}/_matrix/federation/v1/version"
            r = requests.get(url, headers = req_headers)
            r.raise_for_status() # raise e.g. on 404
            server_version = r.json()
            if self.diagnostics and not "Access-Control-Allow-Origin" in r.headers:
                logging.error("𐄂 Server version endpoint has no CORS header")
            elif self.diagnostics and r.headers["Access-Control-Allow-Origin"] != "*":
                logging.error("𐄂 Server version endpoint has no proper CORS header: '%s'",
                              r.headers["Access-Control-Allow-Origin"])
        except requests.exceptions.HTTPError as e:
            if self.diagnostics:
                if e.response.status_code == 404:
                    logging.warning("𐄂 No server version document exists (404)")
                else:
                    logging.error("𐄂 Server version error %s", str(e))
            return ""
        except requests.exceptions.JSONDecodeError as e:
            if self.diagnostics:
                logging.error("𐄂 Server version response is no valid json")
            return ""

        # server_version is "server" dict with a dict "name", "version".
        server_version = server_version.get("server", None)
        if self.diagnostics:
            logging.info("✔ Server version: %s (%s)", server_version["name"],
                         server_version["version"])
            logging.info("✔ Federation API endpoints seem to work fine")

        return f"{server_version['name']} ({server_version['version']})"

    def test_server_keys(self) -> bool:
        """Tests that server keys server name matches"""
        server_keys: dict = {}
        try:
            url = f"{self.federation_baseurl}/_matrix/key/v2/server"
            r = requests.get(url, headers = req_headers)
            r.raise_for_status() # raise e.g. on 404
            server_keys = r.json()
            if self.diagnostics and not "Access-Control-Allow-Origin" in r.headers:
                logging.error("𐄂 Server version endpoint has no CORS header")
            elif self.diagnostics and r.headers["Access-Control-Allow-Origin"] != "*":
                logging.error("𐄂 Server version endpoint has no proper CORS header: '%s'",
                              r.headers["Access-Control-Allow-Origin"])
        except requests.exceptions.HTTPError as e:
            if self.diagnostics:
                if e.response.status_code == 404:
                    logging.warning("𐄂 No server keys exist (404)")
                else:
                    logging.error("𐄂 Server keys retrieval error %s", str(e))
            return False
        except requests.exceptions.JSONDecodeError as e:
            if self.diagnostics:
                logging.error("𐄂 Server keys response is no valid json")
            return False

        server_key_name = server_keys.get("server_name", "").lower()
        if self.servername != server_key_name:
            if self.diagnostics:
                logging.error("𐄂 Configured server name mismatch! "\
                              f"{self.servername}!={server_key_name}")
            return False
        server_sigs = server_keys.get("signatures", {})
        if self.servername not in server_sigs.keys():
            if self.diagnostics:
                logging.error(f"𐄂 No server key for server name "\
                              f"'{self.servername}' in /_matrix/key/v2/server")
            return False
        return True


    def test_client_endpoint(self) -> bool:
        """Tests a client endpoint to see if that works well"""
        res = True # Success result
        client_versions: Optional[dict] = None
        try:
            url = f"{self.client_baseurl}/_matrix/client/versions"
            r = requests.get(url, headers = req_headers)
            r.raise_for_status() # raise e.g. on 404
            client_versions = r.json()
            if self.diagnostics and not "Access-Control-Allow-Origin" in r.headers:
                logging.error("𐄂 Client version endpoint has no CORS header")
            elif self.diagnostics and r.headers["Access-Control-Allow-Origin"] != "*":
                logging.error("𐄂 Client version endpoint has no proper CORS header: '%s'", r.headers["Access-Control-Allow-Origin"])
        except requests.exceptions.HTTPError as e:
            if self.diagnostics:
                if e.response.status_code == 404:
                    logging.warning("𐄂 No Client versions document exists (404)")
                else:
                    logging.error("𐄂 Client versions document error %s", str(e))
            res = False
        except requests.exceptions.JSONDecodeError as e:
            if self.diagnostics:
                logging.error("𐄂 Client version response is no valid json")
            res = False
        if res:
            self.client_versions = client_versions
            if self.diagnostics:
                logging.info("✔ Client API endpoints seem to work fine")
        elif self.diagnostics:
            logging.info("𐄂 Client API endpoint problem (no versions document)")
        return res

    def test_qrcode_login(self) -> bool:
        """Returns true if QRcode login is setup (msc4108)"""
        res:bool = False # qrcode has been setup
        client_rendevouz: Optional[dict] = None
        try:
            url = f"{self.client_baseurl}/_matrix/client/unstable/org.matrix.msc4108/rendezvous"
            headers = {"content-type": "text/plain"}
            headers.update(req_headers)
            data="INIITIAL" * 128
            r = requests.post(url, headers = headers, data = data)
            client_rendevouz = r.json()
            r.raise_for_status() # raise e.g. on 404
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.info("  QR code login is disabled (MSC 4108)")
        except requests.exceptions.JSONDecodeError as e:
                logging.error("𐄂 Client rendevouz response is no valid json")
        else:
            if r.status_code == 201:
                res = True
                logging.info("✔ QR code login is enabled (MSC 4108)")
                if not "url" in client_rendevouz or not "ETag" in r.headers:
                    logging.error("𐄂 Malformed client rendevouz response "
                                  "(no URLor no ETag)")
        return res

    def test_room_directory(self) -> bool:
        """Returns true if there is a room directory"""
        res:bool = False # room dir exists
        try:
            url = f"{self.client_baseurl}/_matrix/client/v3/publicRooms"
            params = {'limit': '1'}
            r = requests.get(url, headers = req_headers, params = params)
            r.raise_for_status() # raise e.g. on 404
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                res = False
                logging.info("  Public room directory is disabled")
        else:
            if r.status_code == 200:
                res = True
                logging.info("  Public room directory is enabled")
        return res

    def get_user_openid_token(self) -> Optional[str]:
        """POST /_matrix/client/v3/user/{userId}/openid/request_token"""
        assert self.args and "user" in self.args and "token" in self.args, \
            "No user and token credentials"

        try:
            url = f"{self.client_baseurl}/_matrix/client/v3/user/{self.args.user}/openid/request_token"
            headers = {"Authorization": f"Bearer {self.args.token}"}
            headers.update(req_headers)
            data: dict = {}
            r = requests.post(url, json = data, headers = headers)
            r.raise_for_status() # raise e.g. on 404
            response = r.json()
        except requests.exceptions.HTTPError as e:
            logging.error("Error when trying to retrieve a user Openid token, response was %s", e.response.text)
            raise e
        else:
            # Success, return openid access token
            return response.get("access_token", None)

    def test_rtc(self) -> bool:
        """Test MatrixRTC setup"""
        res = True
        rtcuserServer: Optional[MatrixServer] = None
        openid_token = None # only unauth testing if we don't get one

        if self.livekits:
            logging.info("✔ MatrixRTC SFU configured")
        else:
            logging.info("  No MatrixRTC SFU configured")

        if self.args is None or self.args.user is None or self.args.token is None:
            # No credentials given, only testing unauthed request
            rtcuserServer = None
        else:
            # retrieve valid openid token
            # Retrieve a valid user's openid token for use with the jwt service
            m_server = MatrixServer.get_mxid_servername(self.args.user)
            rtcuserServer = MatrixServer(m_server, args=self.args)
            rtcuserServer.get_server_baseurl()
            rtcuserServer.get_client_baseurl()
            openid_token = rtcuserServer.get_user_openid_token()

        if self.livekits is None:
            return True # nothing to do
        for jwtauth in self.livekits:
            jwtauth.test_health()
            if not jwtauth.test_sfuget(mserver = rtcuserServer,
                                       token = openid_token):
                res = False

        # Are delayed event supported? Bad things will happen otherwise
        if self.diagnostics:
            delayed_events = False
            if self.client_versions:
                features = self.client_versions['unstable_features']
                delayed_events = features.get('org.matrix.msc4140', False)
            if not delayed_events:
                logging.warning("𐄂 MatrixRTC configured but delayed events "
                                "turned off (MSC4140). BAD!")
            else:
                logging.debug("✔ MatrixRTC configured and delayed events work")

        #Test for MSC3266 (room summaries, needed for MatrixRTC, among others)
        msc3266_support = False
        m_versions = []
        if self.client_versions is not None:
            m_versions = self.client_versions.get("versions", [])
        if m_versions and "v1.15" in m_versions:
            # Stable room summary support claimed, test it
            msc3266_support = True
            logging.debug("✔ Room summaries (MSC3266) support in matrix compat v1.15")
            url = f"{self.client_baseurl}/_matrix/client/v1/room_summary/%23element-web:matrix.org"
            params = {'via':'matrix.org'}
            try:
                r = requests.get(url, headers = req_headers, params = params)
                r.raise_for_status() # raise e.g. on 404
            except requests.exceptions.HTTPError as e:
                logging.error("𐄂 Room summaries support claimed but failed")
                logging.error("  HTTP error '{} ({})'"\
                                 .format(e.response.text, e.response.status_code))
            else:
                msc3266_support = True
                logging.debug("✔ Room summaries stable support works")

        if not msc3266_support: # test for unstable support
            url = f"{self.client_baseurl}/_matrix/client/unstable/im.nheko.summary/summary/%23element-web:matrix.org"
            try:
                r = requests.get(url, headers = req_headers)
                r.raise_for_status() # raise e.g. on 404
            except requests.exceptions.HTTPError as e:
                if r.status_code == 404:
                    logging.info("  No room summaries (MSC3266) (unstable) support")
                else:
                    # Complain in other cases, e.g. when this endpoint actually
                    # needs authentication as stated per the spec
                    logging.info("  HTTP error '{} ({})' returned when testing " \
                                 "for room summaries (MSC3266) support (?)"\
                                 .format(e.response.text, e.response.status_code))
            else:
                msc3266_support = True
                logging.debug("✔ Room summaries (MSC3266) (unstable) support")
        return res

    def test_open_reg(self) -> bool:
        """Tests if the server is open for registration and complain

        We don't do very deep testing though.
        returns False if open registration or guest access seems possible"""
        res = True
        r: Optional[requests.Response]= None
        try:
            url = f"{self.client_baseurl}/_matrix/client/v3/register"
            data: dict = {'password':'1234',
                          'username': str(urandom(12).hex())}
            r = requests.post(url, json = data, headers = req_headers)
            r.raise_for_status() # raise e.g. on 403
        except requests.exceptions.HTTPError as e:
            if r is not None and r.status_code != 403:
                logging.warning("𐄂 Direct open registration might not be forbidden!")
                res = False
        # Next test for guest access
        try:
            url = f"{self.client_baseurl}/_matrix/client/v3/register"
            params: dict = {'kind':'guest'}
            data = {'password':'1234',
                          'username': str(urandom(12).hex())}
            r = requests.post(url, params = params, json = data,
                              headers = req_headers)
        except requests.exceptions.HTTPError as e:
            pass
        if r is not None and r.status_code != 403:
            logging.warning("𐄂 Guest access might not be forbidden (returned %d)!",
                            r.status_code)
            res = False
        if res:
            logging.debug("✔ Direct registration and guest access forbidden per se 👍")
        return res

    def test(self) -> bool:
        logging.debug("Testing server %s", self.loganon(self.servername,
                                                        self.servername))
        if self.get_server_baseurl() is None:
            return False
        self.get_client_baseurl()
        self.test_server_keys()
        self.get_server_version()
        self.test_client_endpoint()
        if self.diagnostics:
            self.test_qrcode_login()
            self.test_room_directory()
        self.test_rtc()
        self.test_open_reg()
        return True
