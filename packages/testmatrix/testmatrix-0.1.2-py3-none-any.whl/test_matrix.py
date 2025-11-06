#!/usr/bin/env python3
#
# Matrix server sanity checker
# ©Sebastian Spaeth & contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import logging
import sys
from pathlib import Path

# if we run from the source directory, make use of the local package
local_pkg_path = Path(__file__).parent / Path('src')
if (local_pkg_path / Path('testmatrix')).is_dir():
    # Running from local source installation, use local src package
    sys.path.insert(0, str(local_pkg_path))

from testmatrix import __version__, MatrixServer


def handle_cmd_opts() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A matrix server sanity tester. Credentials are only needed if you want to test MatrixRTC setups.")
    # no debug output
    parser.add_argument('-q', '--quiet', action='store_true', help="Less verbose debug output")
    parser.add_argument('-u', '--user', metavar='MXID', help=
                        """user for the MatrixRTC testing, either as
                        @USER:DOMAIN.COM or as USER. In the latter case,
                        the user belongs to the server being tested.""")
    parser.add_argument('-t', '--token', help="auth token to be used for <MXID> for MatrixRTC testing")
    parser.add_argument('--anonymize', action='store_true',
                        help="(Try to) obfuscate domain names in log output")
    parser.add_argument('-V', '--version',  action='version',
                        version=__version__,
                        help="Just report current version")
    parser.add_argument('servername')
    args = parser.parse_args()
    if args.user and not args.user.startswith('@'):
        if ':' not in args.user:
            args.user = "@" + args.user + ":" + args.servername
        else:
            logging.error("Invalid local username '%s' given-", args.user)
            sys.exit(1)
    return args

def main():
    logging.basicConfig(datefmt="", format="{message}",
                        style="{",
                        level=logging.DEBUG)
    diagnostics = True
    args = handle_cmd_opts()
    if args.quiet:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        diagnostics = False
    tms = MatrixServer(args.servername, args, diagnostics=diagnostics)
    tms.test()

if __name__ == "__main__":
    main()
