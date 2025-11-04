#!/usr/bin/env python3
"""
CLI for initializing new Python projects.
"""

import argparse
import sys
from .generator import initialize_project

def main():
    """Main entry point for project initialization."""
    parser = argparse.ArgumentParser(
        description='Initialize a new Python project with PyPI publishing workflow.'
    )
    parser.add_argument('--package-name', required=True, help='The name of the package')
    parser.add_argument('--author', required=True, help='The name of the author')
    parser.add_argument('--author-email', required=True, help='The email of the author')
    parser.add_argument('--description', required=True, help='A short description of the package')
    parser.add_argument('--url', required=True, help='The URL of the project')
    parser.add_argument('--command-name', required=True, help='The name of the command-line entry point')

    args = parser.parse_args()

    try:
        result = initialize_project(
            package_name=args.package_name,
            author=args.author,
            author_email=args.author_email,
            description=args.description,
            url=args.url,
            command_name=args.command_name
        )
        print(result['message'])
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
