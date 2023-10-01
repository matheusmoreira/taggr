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

import os
import shutil

from taggr import Taggr

def determine_stream_size(file):
    if file.seekable():
        original_position = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(original_position, os.SEEK_SET)
        return size
    else:
        return None

def split_nested(tag, separator='.'):
    return tag.split(separator)

def insert_nested(taggr, tag):
    components = split_nested(tag)
    last = None
    for component in components:
        last = taggr.insert_tag(component, last)

def insert_tags(taggr, arguments):
    with taggr.transaction():
        for tag in arguments.tags:
            insert_nested(taggr, tag)

def insert_data(taggr, arguments):
    with taggr.transaction():
        with arguments.file as file:
            size = determine_stream_size(file)
            if size is None:
                # couldn't calculate size, stream not seekable
                # gonna have to read entire thing into memory
                data_id = taggr.insert_data(file.read())
            else:
                data_id = taggr.insert_data(size=size)
                with taggr.open_data_blob(data_id) as blob:
                    shutil.copyfileobj(file, blob, arguments.buffer_size)

def cli(arguments):
    with Taggr(arguments.database) as taggr:
        arguments.function(taggr, arguments)

def main():
    cli(parser.parse_args())

import argparse

parser = argparse.ArgumentParser(
    description='Tag anything with hierarchical tags and key/value pairs.',
    epilog='Copyright © 2023 Matheus Afonso Martins Moreira - GNU AGPLv3+',
    allow_abbrev=False
)

parser.add_argument(
    'database',
    help='metadata database to work with'
)

subparsers = parser.add_subparsers(
    title='commands',
    metavar='command',
    description='What to do.',
    dest='command',
    required=True
)

insert_command = subparsers.add_parser(
    'insert',
    description='Insert data or metadata into the database.',
    help='Insert data or metadata'
)
insert_subparsers = insert_command.add_subparsers(
    title='insertion commands',
    metavar='insert-command',
    description='What to insert into the database.',
    dest='insert',
    required=True
)

insert_data_command = insert_subparsers.add_parser(
    'data',
    description='Insert data into the database.',
    help='Insert data'
)
insert_data_command.set_defaults(
    function=insert_data
)
insert_data_command.add_argument(
    'file',
    type=argparse.FileType('rb'),
    help='path to file or "-" for standard input'
)
insert_data_command.add_argument(
    '--buffer-size',
    type=int,
    default=None,
    required=False,
    help='I/O buffer size in bytes',
    metavar='SIZE'
)

insert_tags_command = insert_subparsers.add_parser(
    'tag',
    aliases=['tags'],
    description='Insert one or more tags into the database.',
    help='Insert tags'
)
insert_tags_command.set_defaults(
    function=insert_tags
)
insert_tags_command.add_argument(
    'tags',
    metavar='tag',
    nargs='+',
    help='tag to insert'
)
