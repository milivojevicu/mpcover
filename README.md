# MPCover: Album cover display for [MPD](https://github.com/MusicPlayerDaemon/MPD)

[![Code QC](https://github.com/milivojevicu/mpcover/actions/workflows/check.yml/badge.svg)](https://github.com/milivojevicu/mpcover/actions/workflows/check.yml)

Python program for displaying album covers of music currently playing through MPD using tkinter.

## Installation

Install the package from PyPI using `pip`:

```bash
pip install mpcover
```

## Configuration

The configuration file should be located in the user home directory with the name ".mpcover.init".

For more information on where the user home directory is,
reference [`os.path.expanduser`](https://docs.python.org/3/library/os.path.html#os.path.expanduser).

Example configuration file:

```ini
[connection]
# Connection settings. The password is optional, to leave it unset simply remove
# the "password = ..." line from the configuration file.
port = 6600
host = localhost
password = example_password

[logging]
level = info

[binds]
# The values should be `tkinter` key bind strings.
refresh = r
```

