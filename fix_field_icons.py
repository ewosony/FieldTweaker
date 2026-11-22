"""Compatibility command for refreshing FIELD application icons.
Usage: python fix_field_icons.py
"""
import sys
from download_app_icons import main

if __name__ == '__main__':
    sys.argv = [sys.argv[0], '--refresh', '--bundle']
    main()
