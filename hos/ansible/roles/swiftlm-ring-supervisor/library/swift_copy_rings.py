#!/usr/bin/python
#
# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
DOCUMENTATION = '''
---
module: swift_copy_rings
short_description: Copy Swift ring files
description:
  - This module copies Swift ring files from a source directory to a
    target directory (usually /etc/swift).
  - It only copies files if they have changed. It determines this by comparing
    sha1 check sums.
  - If the destination directory contains a ring file that is not in the
    source directory, the file is (optionally) removed.
  - The ownership and mode of the files can also be optionally set. It
    sets these attributes whether or not a file is copied.
  - Only ring files are copied (.builder and .ring.gz). The object storage
    policy has special handling. If the source files are called
    object-0.builder or object-0.ring.gz, they are copied to
    object.builder and object.ring.gz (i.e. the "-0" is removed from the name)
  - Ring files in subdirectories (i.e., backups) are also copied.
options:
    src:
        description:
            - Source directory path to copy files from.
        required: true
        default: null
        choices: []
        aliases: []
    dest:
       description:
            - Directory path where files are copied to.
        required: true
        default: null
        choices: []
        aliases: []
    mode:
       description:
            - Mode of file in destination directory
        required: no
        default: null
        choices: []
        aliases: []
    owner:
       description:
            - name of the user that should own the file
        required: no
        default: null
        choices: []
        aliases: []
    group:
       description:
            - name of the group that should own the file
        required: no
        default: null
        choices: []
    remove:
       description:
            - Remove files from destination if not in source
        required: no
        default: no
        choices: []
'''

EXAMPLES = '''
- swift_copy_files src=/etc/d dest=/etc/swift
  remove=no owner=swift group=swift mode=0400
'''

RETURN = '''
changes:
    description: List of actions taken on source files
    returned: success
    type: array
    sample: "['copy /etc/d/account.builder to /etc/swift/account.builder]"
'''

import json
import hashlib
import grp
import pwd
import os
import shutil
import sys
import shlex


RING_NAMES = ['account', 'container', 'object']
COPY_TYPES = ['.ring.gz', '.builder']


def is_bool(value):
    if value.lower() in ['yes', 'true', '1']:
        return True
    return False


def is_ringfile(name):
    prefix_ok = False
    ext_ok = False
    for prefix in RING_NAMES:
        if name.startswith(prefix):
            prefix_ok = True
    for ext in COPY_TYPES:
        if name.endswith(ext):
            ext_ok = True
    return prefix_ok and ext_ok


# The next two functions manage mapping object-0.<ext> in source directory
# to object.<ext> in destination directory. If the ring is not object-0, the
# name is unchanged.
def rm0(name):
    if name.startswith('object-0.'):
        return 'object.' + name[len('object-0.'):]
    else:
        return name


def add0(name):
    if name.startswith('object.'):
        return 'object-0.' + name[len('object.'):]
    else:
        return name


def checksum(dirname, name):
    m = hashlib.sha1()
    filename = os.path.join(os.path.realpath(dirname), name)
    try:
        fd = open(filename, 'r')
        for chunk in fd.read(64*1024):
            m.update(chunk)
        cksum = repr(m.digest())
    except IOError:
        cksum = 0
    return cksum


def remove(actions, dirname, name):
    filename = os.path.join(os.path.realpath(dirname), name)
    os.remove(filename)
    actions.append('remove %s' % filename)


def copy(changes, src, sname, dest,  dname):
    srcname = os.path.join(os.path.realpath(src), sname)
    destname = os.path.join(os.path.realpath(dest), dname)
    shutil.copy(srcname, destname)
    shutil.copystat(srcname, destname)
    changes.append('copy %s to %s' % (srcname, destname))


def set_owner_mode(actions, dirname, name, owner, group, mode):
    filename = os.path.join(os.path.realpath(dirname), name)
    stat = os.stat(filename)
    if owner:
        owner = pwd.getpwnam(owner).pw_uid
        if stat.st_uid == owner:
            owner = -1  # Already same owner
    else:
        owner = -1
    if group:
        group = grp.getgrnam(group).gr_gid
        if stat.st_gid == group:
            group = -1  # Already same group
    if owner >= 0 or group >= 0:
        os.chown(filename, owner, group)
        actions.append('chown %s to %s %s' % (filename, owner, group))
    if mode:
        orig_mode = str(oct(stat.st_mode))[-4:]
        if mode != orig_mode:
            os.chmod(filename, int(mode, 8))
            actions.append('chmod %s to %s' % (filename, mode))


def main():
    dest_files = []
    src = ''
    dest = ''
    ret = {}
    owner = None
    group = None
    mode = None
    do_removes = False
    changes = []
    file_actions = []
    try:
        args_file = sys.argv[1]
        args_data = file(args_file).read()
        arguments = shlex.split(args_data)
    except (IndexError, IOError):
        arguments = sys.argv  # Running interactively

    try:
        for arg in arguments:
            if "=" in arg:
                (key, value) = arg.split('=')
                if key == 'src':
                    src = value
                elif key == 'dest':
                    dest = value
                elif key == 'remove':
                    do_removes = is_bool(value)
                elif key == 'owner':
                    owner = value
                elif key == 'group':
                    group = value
                elif key == 'mode':
                    mode = value
                else:
                    raise Exception('Invalid argument: %s' % key)  # noqa

        # Find files in src and dest directories
        src_file_names = []
        for _, _, files in os.walk(os.path.realpath(src), topdown=True):
            src_file_names = files
            break
        dest_file_names = []
        for _, _, files in os.walk(os.path.realpath(dest), topdown=True):
            dest_file_names = files
            break

        # Compare files and work out actions for each file. Actions are:
        # same: files are same; no action needed
        # copy: files are different, or missing in dest; copy src to dest
        # remove: file in dest, but not src; remove file from dest
        no_ringfiles = True
        for name in src_file_names:
            if is_ringfile(name):
                no_ringfiles = False
                src_checksum = checksum(src, name)
                if rm0(name) in dest_file_names:
                    dest_checksum = checksum(dest, rm0(name))
                else:
                    dest_checksum = 0  # dest is missing
                if src_checksum == dest_checksum:
                    # src/dest are same checksum
                    file_actions.append({'name': name, 'action': 'same'})
                else:
                    # src/dest different, or missing from dest
                    file_actions.append({'name': name, 'action': 'copy'})
                dest_files.append(name)
        if no_ringfiles:
            raise Exception('No ring files in %s' % src)  # noqa
        for name in dest_file_names:
            if is_ringfile(name):
                if add0(name) not in src_file_names:
                    # dest file no longer in src
                    if do_removes:
                        file_actions.append({'name': name, 'action': 'remove'})
                    else:
                        file_actions.append({'name': name, 'action': 'left'})

        # Perform copy/remove actions
        for file_action in file_actions:
            name = file_action.get('name')
            action = file_action.get('action')
            if action == 'same':
                pass
            elif action == 'remove':
                remove(changes, dest, rm0(name))
            elif action == 'copy':
                copy(changes, src, name, dest, rm0(name))
                src_checksum = checksum(src, name)
                dest_checksum = checksum(dest, rm0(name))
                if src_checksum != dest_checksum:
                    raise Exception('File %s: post-copy checksums'
                                    ' do not match' % os.path.join(src, name))
            if action in ['same', 'copy', 'left']:
                set_owner_mode(changes, dest, rm0(name), owner, group, mode)

        ret['failed'] = False
        ret['rc'] = 0
    except (IOError, OSError, Exception) as err:  # noqa
        ret['failed'] = True
        ret['rc'] = 1
        ret['msg'] = str(err)

    ret['changes'] = changes
    ret['changed'] = False
    if changes:
        ret['changed'] = True
    print(json.dumps(ret))


if __name__ == '__main__':
    main()
