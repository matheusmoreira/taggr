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
transaction = SimpleNamespace()
create = SimpleNamespace()
create.table = SimpleNamespace()
create.index = SimpleNamespace()
select = SimpleNamespace()
select.tags = SimpleNamespace()
insert = SimpleNamespace()
insert.data = SimpleNamespace()

pragma.encoding = \
'''
PRAGMA encoding = 'UTF-8';
'''

pragma.foreign_keys = \
'''
PRAGMA foreign_keys = ON;
'''

pragma.trusted_schema = \
'''
PRAGMA trusted_schema = OFF;
'''

pragma.synchronous = \
'''
PRAGMA synchronous = EXTRA;
'''

pragma.secure_delete = \
'''
PRAGMA secure_delete = ON;
'''

pragma.optimize = \
'''
PRAGMA optimize;
'''

pragma.all = [
    pragma.encoding,
    pragma.foreign_keys,
    pragma.trusted_schema,
    pragma.synchronous,
    pragma.secure_delete,
]

transaction.begin = \
'''
BEGIN;
'''

transaction.commit = \
'''
COMMIT;
'''

transaction.rollback = \
'''
ROLLBACK;
'''

create.table.data = \
'''
CREATE TABLE IF NOT EXISTS data (
    id INTEGER NOT NULL PRIMARY KEY,
    bytes BLOB,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

create.table.tag = \
'''
CREATE TABLE IF NOT EXISTS tag (
    parent_id INTEGER REFERENCES tag(id),
    id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

create.table.data_tag = \
'''
CREATE TABLE IF NOT EXISTS data_tag (
    id INTEGER NOT NULL PRIMARY KEY,
    data_id INTEGER NOT NULL REFERENCES data(id),
    tag_id INTEGER NOT NULL REFERENCES tag(id),
    value,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

create.tables = [
    create.table.data,
    create.table.tag,
    create.table.data_tag,
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

create.index.unique_tag_for_data = \
'''
CREATE UNIQUE INDEX IF NOT EXISTS unique_tag_for_data
ON data_tag(data_id, tag_id)
WHERE data_tag.value IS NULL;
'''

create.index.unique_key_value_pair_for_data = \
'''
CREATE UNIQUE INDEX IF NOT EXISTS unique_key_value_pair_for_data
ON data_tag(data_id, tag_id, value)
WHERE data_tag.value IS NOT NULL;
'''

create.indexes = [
    create.index.unique_root_tags,
    create.index.unique_tag_in_parent,
    create.index.unique_tag_for_data,
    create.index.unique_key_value_pair_for_data,
]

select.tags.one = \
'''
SELECT parent_id, id, name FROM tag WHERE tag.id = $1;
'''

select.tags.all = \
'''
SELECT parent_id, id, name FROM tag;
'''

select.tags.root = \
'''
SELECT parent_id, id, name FROM tag WHERE tag.parent_id IS NULL;
'''

select.tags.children = \
'''
SELECT parent_id, id, name FROM tag WHERE tag.parent_id = $1;
'''

select.tags.descendants = \
'''
WITH RECURSIVE descendants (parent_id, id, name) AS (
    SELECT tag.parent_id, tag.id, tag.name
    FROM tag
    WHERE tag.parent_id = $1

    UNION ALL

    SELECT tag.parent_id, tag.id, tag.name
    FROM tag
    JOIN descendants ON descendants.id = tag.parent_id
)

SELECT * FROM descendants;
'''

select.tags.parent = \
'''
SELECT parent.parent_id, parent.id, parent.name
FROM tag parent
JOIN tag child
ON parent.id = child.parent_id
WHERE child.id = $1;
'''

select.tags.ancestors = \
'''
WITH RECURSIVE ancestors (parent_id, id, name) AS (
    SELECT parent.parent_id, parent.id, parent.name
    FROM tag parent
    JOIN tag child
    ON parent.id = child.parent_id
    WHERE child.id = $1

    UNION ALL

    SELECT tag.parent_id, tag.id, tag.name
    FROM tag
    JOIN ancestors ON tag.id = ancestors.parent_id
)

SELECT * FROM ancestors;
'''

insert.data.template = \
'''
INSERT INTO data (bytes) VALUES ({})
ON CONFLICT DO UPDATE SET updated_at = CURRENT_TIMESTAMP
RETURNING data.id;
'''

insert.data.directly = insert.data.template.format('$1')
insert.data.zeroed = insert.data.template.format('zeroblob($1)')

insert.tag = \
'''
INSERT INTO tag (name, parent_id) VALUES ($1, $2)
ON CONFLICT DO UPDATE SET updated_at = CURRENT_TIMESTAMP
RETURNING tag.id;
'''

insert.data_tag = \
'''
INSERT INTO data_tag (data_id, tag_id, value) VALUES ($1, $2, $3)
ON CONFLICT DO UPDATE SET updated_at = CURRENT_TIMESTAMP
RETURNING data_tag.id;
'''
