# testmatrix [![PyPI version](https://badge.fury.io/py/testmatrix.svg)](https://pypi.org/project/testmatrix/) [![Matrix](https://img.shields.io/matrix/testmatrix:sspaeth.de?server_fqdn=chat.sspaeth.de&fetchMode=summary&link=https://matrix.to/#/#testmatrix:sspaeth.de)](https://matrix.to/#/#testmatrix:sspaeth.de)

A matrix server sanity tester. Relased under the GNU AGPLv3+.

## Usage

See `python3 test_matrix.py --help` for possible options (or `testmatrix -h` if you have it
properly installed).

Credentials are only needed if you want to test an underlying livekit
MatrixRTC setup (a.k.a. Element Call).

If you have installed the package via pip (or other means), the
installed command will be named `testmatrix` and not test_matrix.py.

**Note:** There is an `--anonymize` switch, which will attempt to clean
up domain names in the log output. However, there is no guarantee that
it will work 100%. So do double-check your output before submitting
somewhere if you are using this.

### Installation

Currently, you do not need to install anything, as long as you have all
requirements (see below) installed, you can directly run the
`test_matrix.py` script.

Alternatively, you can install this by issueing: `pip install testmatrix`

Or even better: install the cool [uvenv](https://pypi.org/project/uvenv/) package manager and install into a separate venv via:
`uvenv install testmatrix`

### Requirements

Requires python and python-requests.

You can install all requirements on your system by running
`pip install -r requirements.txt`

## Discussion

Matrix chatroom: [#testmatrix:sspaeth.de](https://matrix.to/#/#testmatrix:sspaeth.de)

## Development

### Build an installable package

To build an installable package, you need to have python3-build
installed. Running `python3 -m build` in the git root will create
packages in the `dist` directory.

### How to upload to pypi:
Note to self: `twine upload dist/* --verbose`