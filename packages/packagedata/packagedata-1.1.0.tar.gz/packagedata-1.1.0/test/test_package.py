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

import packagedata as pkgdata


def test_import():
    import testpkg
    assert testpkg.test() == 'This is a test function from testpkg.'

def test_read_text():
    text = pkgdata.read_text('testpkg', 'data/test.txt')
    assert text == 'This is a sample text file.\n'


def test_read_bytes():
    data = pkgdata.read_bytes('testpkg', 'data/test.bin')
    assert data == b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'


def test_as_path():
    with pkgdata.as_path('testpkg', 'data/test.txt') as path:
        text = path.read_text(encoding='utf-8')
        assert text == 'This is a sample text file.\n'


def test_entry_points():

    found = 0
    for ep in pkgdata.entry_points('testpkg.plugins'):
        assert ep.name in ['plugin1', 'plugin2']
        assert ep.load()() == f'Hello from testpkg plugin {ep.name}!'
        found += 1

    assert found == 2, f'Expected 2 entry points, found {found}'
