
from setuptools import setup, find_packages
import os

def local_scheme(version):
    if os.environ.get("IS_PULL_REQUEST"):
        return f".dev{os.environ['GITHUB_RUN_ID']}"
    else:
        return ""

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = ""

setup(
    name='pypi-workflow-generator',
    author='Vinayak Menon',
    author_email='vinayakmenon+pypi@users.noreply.github.com',
    description='Dual-mode tool (MCP server + CLI) for generating GitHub Actions workflows for Python package publishing',
    url='https://github.com/hitoshura25/pypi-workflow-generator',
    use_scm_version={"local_scheme": local_scheme},
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Jinja2>=3.0',
    ],
    python_requires='>=3.8',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Build Tools",
    ],
    entry_points={
        'console_scripts': [
            # CLI mode (existing)
            'pypi-workflow-generator=pypi_workflow_generator.main:main',
            'pypi-workflow-generator-init=pypi_workflow_generator.init:main',
            'pypi-release=pypi_workflow_generator.create_release:main',
            'pypi-workflow-generator-release=pypi_workflow_generator.release_workflow:main',

            # MCP mode (new)
            'mcp-pypi-workflow-generator=pypi_workflow_generator.server:main',
        ],
    },
)
