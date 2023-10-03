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
import hashlib
from threading import Thread
from queue import Queue
from types import SimpleNamespace

from taggr import Taggr

hash_function = SimpleNamespace()

hash_function.hashlib_to_tag = {
    'md5':        'MD5',
    'sha1':       'SHA.1',
    'sha224':     'SHA.2.224',
    'sha256':     'SHA.2.256',
    'sha384':     'SHA.2.384',
    'sha512':     'SHA.2.512',
    'sha512_224': 'SHA.2.512.224',
    'sha512_256': 'SHA.2.512.256',
    'sha3_224':   'SHA.3.224',
    'sha3_256':   'SHA.3.256',
    'sha3_384':   'SHA.3.384',
    'sha3_512':   'SHA.3.512',
}

hash_function.choices = hashlib.algorithms_available.intersection(set(hash_function.hashlib_to_tag))

def hash_function_applicator(function, input, output):
    hash = hashlib.new(function)
    while (data := input.get()) is not None:
        hash.update(data)
        input.task_done()
    output.put(hash)

def create_hashing_threads_for(functions):
    threads = {}

    for function in functions:
        input, output = Queue(), Queue()
        target = hash_function_applicator
        arguments = (function, input, output)
        name = f'Thread hash_function_applicator({function})'

        thread = Thread(target=target, args=arguments, name=name)
        thread.start()
        threads[function] = (thread, input, output)

    return threads

def submit_data_for_hashing(threads, *objects):
    for data in objects:
        for function, (thread, input, output) in threads.items():
            input.put(data)

def collect_hashes(threads):
    hashes = {}

    for function, (thread, input, output) in threads.items():
        hashes[function] = output.get()

    return hashes

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
    return last

def insert_tags(taggr, arguments):
    with taggr.transaction():
        for tag in arguments.tags:
            insert_nested(taggr, tag)

def insert_data(taggr, arguments):
    with taggr.transaction():
        with arguments.file as file:
            threads = create_hashing_threads_for(arguments.hash_functions)
            size = determine_stream_size(file)

            if size is None:
                # couldn't calculate size, stream not seekable
                # gonna have to read entire thing into memory
                contents = file.read()
                data_id = taggr.insert_data(contents)
                submit_data_for_hashing(threads, contents, None)
            else:
                data_id = taggr.insert_data(size=size)
                with taggr.open_data_blob(data_id) as blob:
                    while chunk := file.read(arguments.buffer_size):
                        blob.write(chunk)
                        submit_data_for_hashing(threads, chunk)
                    submit_data_for_hashing(threads, None)

            hashes = collect_hashes(threads)
            for function, hash in hashes.items():
                tag_id = insert_nested(taggr, hash_function.hashlib_to_tag[function])
                taggr.insert_metadata(data_id, tag_id, hash.digest())

def list_tags(taggr, arguments):
    if arguments.tags:
        roots = arguments.tags
    else:
        roots = [id for (parent_id, id, name) in taggr.select_root_tags()]

    for root_tag_id in roots:
        for (parent_id, id, name), depth in taggr.walk(root_tag_id):
            indent = arguments.tab * depth
            print(f'{indent}{name}')

def cli(arguments):
    with Taggr(arguments.database) as taggr:
        arguments.function(taggr, arguments)

def main():
    arguments = preprocess_arguments(parser.parse_args())
    cli(arguments)

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

list_command = subparsers.add_parser(
    'list',
    aliases=['ls'],
    description='Browse the data and metadata contained in the database.',
    help='list data or metadata'
)
list_subparsers = list_command.add_subparsers(
    title='listing commands',
    metavar='list-command',
    description='What kind of data or metadata to list.',
    dest='list',
    required=True
)

list_tags_command = list_subparsers.add_parser(
    'tags',
    aliases=['tag'],
    description='List tags from the database.',
    help='list tags'
)
list_tags_command.set_defaults(
    function=list_tags
)
list_tags_command.add_argument(
    'tags',
    nargs='*',
    help='the tag to list',
    metavar='tag'
)
list_tags_command.add_argument(
    '--indent-with',
    dest='tab',
    default='\t',
    required=False,
    help='characters to use for indentation',
    metavar='TEXT'
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
insert_data_command.add_argument(
    '-H', '--hash',
    dest='hash_functions',
    action='append',
    default=[], # sha256
    choices=hash_function.choices,
    required=False,
    help='hash function to apply to the data',
    metavar='FUNCTION'
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

def preprocess_arguments(arguments):
    if hasattr(arguments, 'hash_function'):
        if not arguments.hash_functions:
            arguments.hash_functions.append('sha256')

    return arguments
