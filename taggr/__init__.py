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

class Taggr:

    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def connect(self):
        self.connection = sqlite3.connect(self.database)

    def close(self):
        self.connection.close()

    def cursor(self):
        return self.connection.cursor()
