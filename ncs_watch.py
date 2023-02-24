#! /usr/bin/env python3
"""
NCS Watch - Capture CLI commands to monitor NCS-55xx devices

"""
import re
import sys

from src.ncs_watch.__main__ import main

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
