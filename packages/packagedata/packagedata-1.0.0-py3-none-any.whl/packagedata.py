# Copyright (C) 2025 KuraLabs S.R.L
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Compatibility module for pkg_resources deprecation.

Use of pkg_resources is deprecated as an API in favor of importlib.resources.

The problem is that importlib.resources is only available in Python 3.9+, so
if you maintain a package that needs compatibility with an earlier version of
Python, you need to install the backported version importlib-resources:

In your requirements.txt or equivalent:

    importlib-resources; python_version < "3.9"
    importlib-metadata; python_version < "3.9"

This package provides those requirements, library selection and a compatibility
layer to ease the migration from pkg_resources.

The pkg_resources package is slated for removal as early as 2025-11-30.
You may pin to setuptools<81 to avoid breakage until you can migrate.

See https://setuptools.pypa.io/en/latest/pkg_resources.html.
"""

from contextlib import contextmanager

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources  # backport

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # backport


def read_text(package, resource, encoding='utf-8'):
    """
    Read a text resource from the package.

    :param str package: The package name.
    :param str resource: The resource path.
    :param str encoding: The text encoding to use.

    :return: The contents of the resource as a string.
    :rtype: str

    Usage::

        # Replace old calls:
        #
        # from pkg_resources import resource_string
        # txt = resource_string(
        #     __package__,
        #     'data/config.toml'
        # ).decode('utf-8')
        #
        # With:
        import packagedata as pkgdata
        text = pkgdata.read_text(
            __package__,
            'data/config.toml',
            encoding='utf-8'
        )
    """
    ref = importlib_resources.files(package).joinpath(resource)
    return ref.read_text(encoding=encoding)


def read_bytes(package, resource):
    """
    Read a binary resource from the package.

    :param str package: The package name.
    :param str resource: The resource path.

    :return: The contents of the resource as bytes.
    :rtype: bytes

    Usage::

        # Replace old calls:
        #
        # from pkg_resources import resource_string
        # data = resource_string(
        #     __package__,
        #     'data/mybinaryfile.bin'
        # )
        # With:
        import packagedata as pkgdata
        data = pkgdata.read_bytes(__package__, 'data/mybinaryfile.bin')
    """
    ref = importlib_resources.files(package).joinpath(resource)
    return ref.read_bytes()


@contextmanager
def as_path(package, resource):
    """
    Context manager that yields a pathlib.Path to a resource file.

    :param str package: The package name.
    :param str resource: The resource path.

    :yield: A pathlib.Path to the resource file.

    Usage::

        # Replace old calls:
        #
        # from pkg_resources import resource_filename
        # path = resource_filename(
        #     __package__,
        #     'data/myresource'
        # )
        # do_something_with(path)
        #
        # With:
        import packagedata as pkgdata
        with pkgdata.as_path(__package__, 'data/myresource') as path:
            do_something_with(path)
    """
    ref = importlib_resources.files(package).joinpath(resource)
    with importlib_resources.as_file(ref) as path:
        yield path


def entry_points(group):
    """
    Retrieve entry points for a given entrypoint.

    :param str group: The entrypoint group name.

    :return: An iterable of entry points.
    :rtype: Iterable[importlib.metadata.EntryPoint]

    Usage::

        # Replace old calls:
        #
        # from pkg_resources import iter_entry_points
        # for ep in iter_entry_points(group='my_entrypoint_group'):
        #     print(ep.name, ep.value)
        #     obj = ep.load()
        #
        # With:
        import packagedata as pkgdata
        for ep in pkgdata.entry_points('my_entrypoint_group'):
            print(ep.name, ep.value)
            obj = ep.load()
    """
    eps = importlib_metadata.entry_points()

    # Python 3.10+, entry_points() return and EntryPoints instance
    # EntryPoints has a select() method
    if hasattr(eps, 'select'):
        return eps.select(group=group)

    # For Python 3.8–3.9 backport compatibility
    # In these versions, entry_points() returns a dict-like object
    return eps.get(group, [])


__all__ = [
    'read_text',
    'read_bytes',
    'as_path',
    'entry_points',
]
