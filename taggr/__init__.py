# SPDX-License-Identifier: AGPL-3.0-or-later
#
# taggr - add hierarchical tags and key-value pairs to anything
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

import sqlite3
from taggr import sql

class Taggr:
    class Transaction:
        def __init__(self, connection):
            self.connection = connection

        def __enter__(self):
            self.connection.execute(sql.transaction.begin)

        def __exit__(self, exception_type, exception_value, exception_traceback):
            if exception_value is None:
                self.connection.execute(sql.transaction.commit)
            else:
                self.connection.execute(sql.transaction.rollback)

    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.connect()
        with self.transaction():
            self.create_tables()
            self.create_indexes()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.connection.execute(sql.pragma.optimize)
        self.close()

    def connect(self):
        self.connection = sqlite3.connect(self.database, isolation_level=None)
        self.execute_pragmas()

    def close(self):
        self.connection.close()

    def transaction(self):
        return Taggr.Transaction(self.connection)

    def cursor(self):
        return self.connection.cursor()

    def execute_pragmas(self):
        cursor = self.cursor()
        for pragma in sql.pragma.all:
            cursor.execute(pragma)

    def create_tables(self):
        cursor = self.cursor()
        for table in sql.create.tables:
            cursor.execute(table)

    def create_indexes(self):
        cursor = self.cursor()
        for index in sql.create.indexes:
            cursor.execute(index)

    def open_data_blob(self, data_id, *arguments, **keywords):
        return self.connection.blobopen('data', 'bytes', data_id, *arguments, *keywords)

    def insert_and_fetch_id(self, insert_statement, row):
        return self.cursor().execute(insert_statement, row).fetchone()[0]

    def insert_data(self, blob=None, size=None):
        if blob is None:
            if size is None:
                statement = sql.insert.data.directly
                parameter = None
            else:
                statement = sql.insert.data.zeroed
                parameter = size
        else:
            statement = sql.insert.data.directly
            parameter = blob

        return self.insert_and_fetch_id(statement, (parameter,))

    def insert_tag(self, name, parent=None):
        return self.insert_and_fetch_id(sql.insert.tag, (name, parent))

    def insert_metadata(self, data_id, tag_id, value=None):
        return self.insert_and_fetch_id(sql.insert.data_tag, (data_id, tag_id, value))

    def select_tag(self, tag_id):
        return self.cursor().execute(sql.select.tags.one, (tag_id,)).fetchone()

    def select_all_tags(self):
        return self.cursor().execute(sql.select.tags.all)

    def select_root_tags(self):
        return self.cursor().execute(sql.select.tags.root)

    def select_children_of(self, tag_id):
        return self.cursor().execute(sql.select.tags.children, (tag_id,))

    def select_descendants_of(self, tag_id):
        return self.cursor().execute(sql.select.tags.descendants, (tag_id,))

    def select_parent_of(self, tag_id):
        return self.cursor().execute(sql.select.tags.parent, (tag_id,)).fetchone()

    def select_ancestors_of(self, tag_id):
        return self.cursor().execute(sql.select.tags.ancestors, (tag_id,))

    def walk(self, tag_id):
        def walk_tag(self, tag, depth=0):
            yield tag, depth
            for child in self.select_children_of(tag[1]):
                yield from walk_tag(self, child, depth + 1)

        yield from walk_tag(self, self.select_tag(tag_id))
