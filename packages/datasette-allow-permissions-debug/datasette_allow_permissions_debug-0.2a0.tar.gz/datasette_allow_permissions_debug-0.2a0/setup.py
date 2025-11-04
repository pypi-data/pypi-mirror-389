from setuptools import setup
import os

VERSION = "0.2a0"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-allow-permissions-debug",
    description="Always allow access to /-/permissions, for debugging",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-allow-permissions-debug",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-allow-permissions-debug/issues",
        "CI": "https://github.com/simonw/datasette-allow-permissions-debug/actions",
        "Changelog": "https://github.com/simonw/datasette-allow-permissions-debug/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_allow_permissions_debug"],
    entry_points={
        "datasette": ["allow_permissions_debug = datasette_allow_permissions_debug"]
    },
    install_requires=["datasette>=1.0a20"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx"]},
    tests_require=["datasette-allow-permissions-debug[test]"],
)
