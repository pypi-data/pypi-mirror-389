#!/usr/bin/env python3
"""
CLI for PyPI Workflow Generator.

This module provides the command-line interface for generating
GitHub Actions workflows.
"""

import argparse
import json
import sys
from .generator import generate_workflow

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate a GitHub Actions workflow for Python package publishing.'
    )

    # CLI mode arguments
    parser.add_argument(
        '--python-version',
        default='3.11',
        help='The version of Python to use in the workflow (default: 3.11)'
    )
    parser.add_argument(
        '--output-filename',
        default='pypi-publish.yml',
        help='The name for the generated workflow file (default: pypi-publish.yml)'
    )
    parser.add_argument(
        '--release-on-main-push',
        action='store_true',
        help='Initiate the release on every main branch push'
    )
    parser.add_argument(
        '--test-path',
        default='.',
        help='The path to the tests (default: .)'
    )
    parser.add_argument(
        '--verbose-publish',
        action='store_true',
        help='Enable verbose mode for publishing actions'
    )
    parser.add_argument(
        '--skip-release-workflow',
        action='store_true',
        help='Do not generate the create-release.yml workflow (only generate pypi-publish.yml)'
    )

    # Legacy MCP mode argument (kept for backward compatibility)
    parser.add_argument(
        '--mcp-input',
        help='[DEPRECATED] Use MCP server mode instead. JSON string containing input parameters.'
    )

    args = parser.parse_args()

    if args.mcp_input:
        # Legacy MCP mode (deprecated but supported for backward compatibility)
        print("Warning: --mcp-input is deprecated. Use 'mcp-pypi-workflow-generator' for MCP server mode.", file=sys.stderr)
        try:
            mcp_params = json.loads(args.mcp_input)
            python_version = mcp_params.get('python_version', '3.11')
            output_filename = mcp_params.get('output_filename', 'pypi-publish.yml')
            release_on_main_push = mcp_params.get('release_on_main_push', False)
            test_path = mcp_params.get('test_path', '.')
            verbose_publish = mcp_params.get('verbose_publish', False)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON string provided for --mcp-input: {e}", file=sys.stderr)
            return 1
    else:
        # CLI mode
        python_version = args.python_version
        output_filename = args.output_filename
        release_on_main_push = args.release_on_main_push
        test_path = args.test_path
        verbose_publish = args.verbose_publish

    try:
        result = generate_workflow(
            python_version=python_version,
            output_filename=output_filename,
            release_on_main_push=release_on_main_push,
            test_path=test_path,
            verbose_publish=verbose_publish,
            include_release_workflow=not args.skip_release_workflow
        )
        print(result['message'])
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
