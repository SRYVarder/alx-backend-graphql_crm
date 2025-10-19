#!/usr/bin/env python
import os, sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise
    execute_from_command_line(sys.argv)
