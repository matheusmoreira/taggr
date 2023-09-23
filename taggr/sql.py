# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright © 2023 Matheus Afonso Martins Moreira
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from types import SimpleNamespace

pragma = SimpleNamespace()
create = SimpleNamespace()
create.table = SimpleNamespace()
create.index = SimpleNamespace()
select = SimpleNamespace()
insert = SimpleNamespace()

pragma.encoding = \
'''
PRAGMA encoding = 'UTF-8';
'''

pragma.foreign_keys = \
'''
PRAGMA foreign_keys = ON;
'''

pragma.all = [
    pragma.encoding,
    pragma.foreign_keys,
]

create.table.data = \
'''
CREATE TABLE IF NOT EXISTS data (
    id INTEGER NOT NULL PRIMARY KEY,
    bytes BLOB UNIQUE
);
'''

create.table.tag = \
'''
CREATE TABLE IF NOT EXISTS tag (
    parent_id INTEGER REFERENCES tag(id),
    id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL
);
'''

create.tables = [
    create.table.data,
    create.table.tag,
]

create.index.unique_root_tags = \
'''
CREATE UNIQUE INDEX IF NOT EXISTS unique_root_tags
ON tag(name)
WHERE tag.parent_id IS NULL;
'''

create.index.unique_tag_in_parent = \
'''
CREATE UNIQUE INDEX IF NOT EXISTS unique_tag_in_parent
ON tag(name, parent_id)
WHERE tag.parent_id IS NOT NULL;
'''

create.indexes = [
    create.index.unique_root_tags,
    create.index.unique_tag_in_parent,
]
