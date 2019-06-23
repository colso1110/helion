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
#!/usr/bin/env python3
import sys
import yaml
import string
import os.path
import argparse
from html.parser import HTMLParser

DEFAULT = "\033[0m"
GREEN = "\033[00;32m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"

# Colorful output
def red(msg, *args, **kwargs):
    printc(RED, msg, *args, **kwargs)
def yellow(msg, *args, **kwargs):
    printc(YELLOW, msg, *args, **kwargs)
def blue(msg, *args, **kwargs):
    printc(BLUE, msg, *args, **kwargs)
def green(msg, *args, **kwargs):
    printc(GREEN, msg, *args, **kwargs)
def die(msg=None, *args, **kwargs):
    if not msg: red("die die die")
    else: red(msg, *args, **kwargs)
    sys.exit()
def printc(color, msg, *args, **kwargs):
    end = "\n"
    if 'end' in kwargs: end = kwargs['end']
    try:
        if msg is string:
            print(color + msg.format(*args), end=end)
        else:
            print(color + str(msg), end=end)
    finally:
        print(DEFAULT, end='')

class Entry():
    se = "se"               # Service
    fd = "fd"               # Foundation
    ex = ".ex"              # Rotation is handled externally but still need to track centralized logging
    json = "json"
    rawjson = "rawjson"
    daily = "daily"
    daily = "weekly"
    daily = "monthly"

    def __init__(self, service=None, sub_service=None, logfile=None):
        self.service = service          # 0: The service or component name
        self.sub_service = sub_service  # 1: The sub-service or sub-component name
        self.status = None              # 2: Save the status of the
        self.hostgroups = []            # 3: The hostgroups that the sub_service is found in
        self.logfile = logfile          # 4: The log files that we are working with
        self.logged = None              # 5: Centrally log the log or not
        self.frequency = None           # 5: How often or frequent rotate should run to monitor logs
        self.maxsize = None             # 6: How large the files are allowed to grow before being rotated
        self.retention = None           # 7: How many logs to keep before deleting them
        self.create_user = None         # 8: User to use for creating new log files
        self.create_group = None        # 9: Group to use for creating new log files
        self.su_user = None             #
        self.su_group = None            #

        # HOS data
        self.format = None
        self.notifempty = False

    def __str__(self):
        result = "{: <18} ".format(str(self.service))
        result += "{: <18} ".format(str(self.sub_service))
        result += "{: <13} ".format(str(self.status))
        result += "{: <15} ".format(','.join(self.hostgroups))
        result += "{: <58} ".format(str(self.logfile))
        result += "{: <6} ".format(str(self.logged))
        result += "{: <7} ".format(str(self.frequency))
        result += "{: >4} ".format(str(self.maxsize))
        result += "{: >3} ".format(str(self.retention))
        result += "{: >9} ".format(str(self.format))
        result += "{: >13} ".format(str(self.create_user))
        result += "{: >13}".format(str(self.create_group))
        return result

# Parse the Services HTML data
class Parser(HTMLParser):
    entries = []

    def __init__(self, debug):
        """Initialize the parser
        :debug: provide debug output if set
        """
        HTMLParser.__init__(self)
        self._debug = debug

        self._index = -1
        self._dindex = -1

        self._th = 0
        self._entry = None
        self._start = False

    def handle_starttag(self, tag, attrs):

        # Count header to determine when to start tracking data
        if tag == "th": 
            self._th += 1
            if self._th == 9: self._start = True

        # Create new entries and handle indexing data
        elif self._start:
            if tag == "tr":
                self._index = self._dindex = -1 
                self._entry = Entry()
            elif tag == "td": self._index += 1

    def handle_endtag(self, tag):

        # Stop tracking data once the end of the table is reached
        if self._start and tag == "table": self._start = False

        # Save off entries and handle null data
        if self._start and self._entry:
            if tag == "tr":
                self.entries.append(self._entry)

            # Handle null data as data call back doesn't get called in this case
            elif tag == "td" and self._index != self._dindex:
                self._dindex += 1
                self.set_data(None, self._dindex)

    def handle_data(self, data):
        if self._start and self._index != -1:

            # Multiple lines in a single cell will come in as separate data callbacks
            # so don't increment data index if equal to index
            if self._dindex < self._index: self._dindex += 1

            self.set_data(data, self._dindex)

    def set_data(self, data, index):
        if index == 0:
            if not data and len(self.entries) > 0: data = self.entries[-1].service
            self._entry.service = data.strip() if data else data
            if self._debug: print("0: {}".format(self._entry.service))
        elif index == 1:
            if not data and len(self.entries) > 0: data = self.entries[-1].sub_service
            self._entry.sub_service = data.strip() if data else data
            if self._debug: print("1: {}".format(self._entry.sub_service))
        elif index == 2:
            if not data and len(self.entries) > 0: data = self.entries[-1].status
            self._entry.status = data.lower().strip() if data else data

            # Abort if non supported status detected
            if self._entry.status not in (Entry.se, Entry.fd) and Entry.ex not in self._entry.status:
                self._entry = None
                self._start = False
            if self._debug and self._entry: print("2: {}".format(self._entry.status))
        elif index == 3:
            if not data and len(self.entries) > 0:
                self._entry.hostgroups = self.entries[-1].hostgroups
            else: self._entry.hostgroups.append(data.strip() if data else data)
            if self._debug: print("3: {}".format(self._entry.hostgroups))
        elif index == 4:
            self._entry.logfile = data.strip() if data else data
            if self._debug: print("4: {}".format(self._entry.logfile))
        elif index == 5:
            self._entry.logged = True if data and 'x' in data.strip().lower() else False
            if self._debug: print("5: {}".format(self._entry.logged))
        elif index == 6:
            if not data and len(self.entries) > 0: data = self.entries[-1].frequency
            self._entry.frequency = data.strip() if data else data
            if self._debug: print("6: {}".format(self._entry.frequency))
        elif index == 7:
            if not data and len(self.entries) > 0: data = self.entries[-1].maxsize
            self._entry.maxsize = data.strip() if data else data
            if self._debug: print("7: {}".format(self._entry.maxsize))
        elif index == 8:
            if not data and len(self.entries) > 0: data = self.entries[-1].retention
            self._entry.retention = data.strip() if data else data
            if self._debug: print("8: {}".format(self._entry.retention))
        elif index == 9:
            self._entry.create_user = data.strip() if data else data
            if self._debug: print("9: {}".format(self._entry.create_user))
        elif index == 10:
            self._entry.create_group = data.strip() if data else data
            if self._debug: print("10: {}".format(self._entry.create_group))

# Validate Wiki data against yml
class KronosUtil(HTMLParser):

    true = "true"
    false = "false"
    
    def __init__(self, debug, wiki, hos_files):
        """ Initialize
        :debug: provide debug output if set
        :wiki: html file containing wiki data
        :hos_files: list of files to validate data against
        """
        self._debug = debug

        # Parse entries
        self.hos_entries = []
        self.wiki_entries = None

        # Load data from HTML
        with open(wiki, "r") as strm:
            html = strm.read()
            parser = Parser(self._debug)
            parser.feed(html)
            self.wiki_entries = parser.entries

        # Load host group mappings
        hostgroup_mappings = {}
        hostgroup_file = os.path.join(os.path.dirname(hos_files[0]) + "../../../kronos-producer-configure.yml")
        with open(hostgroup_file, "r") as f:
            for entry in [x["include"] for x in yaml.load(f) if "include" in x]:
                pieces = entry.split(" ")
                target_hosts = pieces[1][pieces[1].find("=")+1:]
                vars_file = pieces[2][pieces[2].find("=")+1:pieces[2].find("-clr.yml")]
                if vars_file not in hostgroup_mappings:
                    hostgroup_mappings[vars_file] = []
                hostgroup_mappings[vars_file].append(target_hosts)

        # Load HOS logging files data
        for hos_file in hos_files:
            with open(hos_file, "r") as strm:
                sub_service = yaml.load(strm)["sub_service"]

                # Create entry per log
                for option in sub_service["logging_options"]:
                    for logfile in option["files"]:

                        # 0 - Service
                        entry = Entry(sub_service["service"])

                        # 1 - Sub-Service
                        entry.sub_service = sub_service["name"]

                        # 2 - Status

                        # 3 - Host Groups
                        if sub_service["name"] in hostgroup_mappings:
                            entry.hostgroups = hostgroup_mappings[sub_service["name"]]

                        # 4 - Logfile
                        entry.logfile = logfile

                        # Central logging options
                        #----------------------------------------------
                        # 5 - Logged
                        #print(logfile)
                        if "centralized_logging" in option:
                            entry.logged = option["centralized_logging"]["enabled"]
                            entry.format = option["centralized_logging"]["format"]

                        # Log rotate options
                        #----------------------------------------------
                        if "log_rotate" in option:
                            log_rotate = option["log_rotate"]

                            # 6 - Frequency
                            if "daily" in log_rotate: entry.frequency = "daily"
                            if "weekly" in log_rotate: entry.frequency = "weekly"
                            if "monthly" in log_rotate: entry.frequency = "monthly"

                            # 7 - Maxsize
                            try:
                                entry.maxsize = next(x[x.find('maxsize') + 8:] for x in log_rotate if 'maxsize' in x)
                            except: pass

                            # 8 - Retention
                            try:
                                entry.retention = next(x[x.find('rotate') + 7:] for x in log_rotate if 'rotate' in x)
                            except: pass

                            # 9 - Create User
                            try:
                                entry.create_user = next(x.split(" ")[2] for x in log_rotate if 'create' in x)
                            except: pass
                            
                            # 10 - Create Group
                            try:
                                entry.create_group = next(x.split(" ")[3] for x in log_rotate if 'create' in x)
                            except: pass

                            # 9 - Su User
                            try:
                                entry.su_user = next(x.split(" ")[2] for x in log_rotate if 'su' in x)
                            except: pass
                            
                            # 10 - Su Group
                            try:
                                entry.su_group = next(x.split(" ")[3] for x in log_rotate if 'su' in x)
                            except: pass

                        # Fail if listed more than once
                        if len(list(filter(lambda x: x == "notifempty", log_rotate))) > 1:
                            print("{:.<60} multiple notifempty in '{}'".format(entry.logfile, entry.sub_service))
                            sys.exit()
                        if 'notifempty' in log_rotate: entry.notifempty = True

                        self.hos_entries.append(entry)

    def first(self, func, iterable):
        """Get the first item that matches the func or return None
        :returns: first matching item else None
        """
        result = None
        if type(iterable) == dict:
            for k, v in iterable.items():
                if func(k, v):
                    result = iterable[k]
                    break
        else:
            for x in iterable:
                if func(x):
                    result = x
                    break

        return result

    def validate(self, all, service, service_names, hostgroups, users, rotate_freq, rotate_maxsize, rotate_retention):
        """Validate the given paramters against HOS using Wiki data
        :all: validate all
        :service: validate the given service only
        :service_names: validate the service name
        :hostgroups: validate the service's hostgroups are correct
        :users: validate the logfiles have the correct users and groups set
        :rotate_freq: validate that all logs have correct frequency
        :rotate_maxsize: validate that all logs have correct maxsize
        :rotate_retention: validate that all logs have correct retention
        """
        # Filter down to just the service we are interested in if given
        hos_entries = self.hos_entries
        wiki_entries = self.wiki_entries
        if service:
            blue("<[={:-^85}=]> ".format(service))
            hos_entries = self.first(lambda x, y: service in x, self.group_by_service(self.hos_entries))
            wiki_entries = self.first(lambda x, y: service in x, self.group_by_service(self.wiki_entries))

        # Validate services names are correct
        if all or service or service_names:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating service names"), end="")

            # Validate all wiki entries exist in the code
            for wiki_entry in wiki_entries:
                hos_entry = self.first(lambda x: x.sub_service == wiki_entry.sub_service, hos_entries)
                if not hos_entry: 
                    if result: red("[failure]")
                    print("{:.<60}doesn't exist".format(wiki_entry.sub_service))
                    result = False

            # Validate all host entries exist on the wiki
            for hos_entry in hos_entries:
                wiki_entry = self.first(lambda x: x.sub_service == hos_entry.sub_service, wiki_entries)
                if not wiki_entry: 
                    if result: red("[failure]")
                    print("{:.<60}shouldn't exist".format(hos_entry.sub_service))
                    result = False
            if result: green("[success]")

        # Validate hostgroups are correct
        if all or service or hostgroups:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating service hostgroups"), end="")
            for wiki_entry in wiki_entries:
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                for x in wiki_entry.hostgroups:
                    if hos_entry and x not in hos_entry.hostgroups:
                        if result: red("[failure]")
                        print("{:.<60}hostgroups {} not found".format(wiki_entry.logfile, str(wiki_entry.hostgroups)))
                        result = False
                if hos_entry:
                    for x in hos_entry.hostgroups:
                        if x not in wiki_entry.hostgroups:
                            if result: red("[failure]")
                            print("{:.<60}hostgroups {} shouldn't exist".format(wiki_entry.logfile, str(x)))
                            result = False
            if result: green("[success]")

        # Validate Wiki entries intended to be logged are logged and nothing else
        if all or service:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating logging"), end="")
            for wiki_entry in wiki_entries:
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if not hos_entry:
                    if result: red("[failure]")
                    print("{:.<60}doesn't exist".format(wiki_entry.logfile))
                    result = False
                elif not hos_entry.logged and wiki_entry.logged:
                    if result: red("[failure]")
                    print("{:.<60}not logged".format(wiki_entry.logfile))
                    result = False
                        
            for hos_entry in hos_entries:
                if hos_entry.logged:
                    wiki_entry = self.first(lambda x: x.logfile == hos_entry.logfile, wiki_entries)
                    if not wiki_entry or not wiki_entry.logged:
                        if result: red("[failure]")
                        print("{:.<60}being logged and shouldn't be".format(hos_entry.logfile))
                        result = False

            if result: green("[success]")

        # Validate create users and groups are correct
        if all or service or users:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating create users and groups"), end="")
            for wiki_entry in wiki_entries:
                if Entry.ex in wiki_entry.status: continue
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if hos_entry and hos_entry.create_user != wiki_entry.create_user:
                    if result: red("[failure]")
                    print("{:.<60}user '{}' should be '{}'".format(wiki_entry.logfile, str(hos_entry.create_user), str(wiki_entry.create_user)))
                    result = False
                if hos_entry and hos_entry.create_group != wiki_entry.create_group:
                    if result: red("[failure]")
                    print("{:.<60}group '{}' should be '{}'".format(wiki_entry.logfile, str(hos_entry.create_group), str(wiki_entry.create_group)))
                    result = False
            if result: green("[success]")

        # Validate all logs are being rotated correctly
        if all or service or rotate_freq or rotate_maxsize or rotate_retention:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating all logs are being rotated"), end="")
            for wiki_entry in wiki_entries:
                if Entry.ex in wiki_entry.status: continue
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if not hos_entry:
                    if result: red("[failure]")
                    print("{:.<60}not rotated".format(wiki_entry.logfile))
                    result = False
                    sys.exit()

            for hos_entry in hos_entries:
                wiki_entry = self.first(lambda x: x.logfile == hos_entry.logfile, wiki_entries)
                if not wiki_entry:
                    if result: red("[failure]")
                    print("{:.<60}rotated but not on Wiki".format(hos_entry.logfile))
                    result = False
                    sys.exit()
                elif Entry.ex in wiki_entry.status and any((hos_entry.frequency, hos_entry.retention, hos_entry.maxsize)):
                    if result: red("[failure]")
                    print("{:.<60}rotated but external on Wiki".format(hos_entry.logfile))
                    result = False
                    sys.exit()

            if result: green("[success]")

        # Validate rotate frequency
        if all or service or rotate_freq:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating logging rotate frequency"), end="")
            for wiki_entry in wiki_entries:
                if Entry.ex in wiki_entry.status: continue
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if hos_entry.frequency != wiki_entry.frequency:
                    if result: red("[failure]")
                    print("{:.<60}frequency '{}' should be '{}'".format(wiki_entry.logfile, str(hos_entry.frequency), str(wiki_entry.frequency)))
                    result = False

            if result: green("[success]")

        # Validate rotate retention
        if all or service or rotate_retention:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating logging rotate retention"), end="")
            for wiki_entry in wiki_entries:
                if Entry.ex in wiki_entry.status: continue
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if hos_entry.retention != wiki_entry.retention:
                    if result: red("[failure]")
                    print("{:.<60}retention '{}' should be '{}'".format(wiki_entry.logfile, str(hos_entry.retention), str(wiki_entry.retention)))
                    result = False

            if result: green("[success]")

        # Validate rotate maxsize
        if all or service or rotate_maxsize:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating logging rotate maxsize"), end="")
            for wiki_entry in wiki_entries:
                if Entry.ex in wiki_entry.status: continue
                hos_entry = self.first(lambda x: x.logfile == wiki_entry.logfile, hos_entries)
                if hos_entry.maxsize != wiki_entry.maxsize:
                    if result: red("[failure]")
                    print("{:.<60}maxsize '{}' should be '{}'".format(wiki_entry.logfile, str(hos_entry.maxsize), str(wiki_entry.maxsize)))
                    result = False

            if result: green("[success]")

        # Validate notifempty logrotate setting
        if all or service:
            result = True
            yellow("<[={:-^85}=]> ".format("Validating logging rotate notifempty"), end="")
            for hos_entry in hos_entries:
                if not hos_entry.notifempty:
                    if result: red("[failure]")
                    print("{:.<60}notifempty not set in '{}'".format(hos_entry.logfile, hos_entry.sub_service))
                    result = False

            if result: green("[success]")


    def disk_usage(self, service=None, hos=False):
        """Calculate disk usage for all services
        :service: validate the given service only
        :hos: base calculations off hos entries
        """
        size_fd = 0                 # Disk consumption sum
        size_se = 0                 # Disk consumption sum

        max_disk = 65000            # 13% of 500G = 65G
        reserve = 3250              # 5% of 65G = 3.25G
        alloc_fd = 6500           # 10% of 65G = 6.5G
        services = 55000            # 85% of 65G = 55G
        alloc_per_se = 2500          # 55G/22 services = 2.5GB ea.
        compression = 1 - 0.80      # 80% compression ratio means multiply by 20%

        # Filter by service if needed
        hos_entries = self.hos_entries
        wiki_entries = self.wiki_entries
        if service:
            hos_entries = self.first(lambda x, y: service in x, self.group_by_service(self.hos_entries))
            wiki_entries = self.first(lambda x, y: service in x, self.group_by_service(self.wiki_entries))

        # Compute disk usage based off wiki or hos files
        #--------------------------------------------------------------------------------
        entries = wiki_entries
        if hos: entries = hos_entries
        for entry in entries:
            maxsize = int(entry.maxsize[:-1])
            if entry.maxsize[-1] == "K": maxsize = maxsize/1024
            retention = int(entry.retention)

            # Allow for one full maxsize log 
            # Allow for a compression ration savings
            # Allow for current plus # of retention logs
            # Total = maxsize + (maxsize * retention * compression)
            val = int(maxsize + (maxsize * retention * compression))

            # Adjustments
            if entry.service == "ceph": val *= 6  # ceph actually has 6 logs

            # Aggregate all services
            if not hos:
                if Entry.fd in entry.status:
                    size_fd += val
                elif Entry.se in entry.status:
                    size_se += val
            else:
                size_se += val

        # Validate foundation disk usage
        #--------------------------------------------------------------------------------
        if not service:
            yellow("<[={:-^85}=]> ".format("Validating foundation disk quotas"), end="")
            if size_fd > alloc_fd: red("[failure]")
            else: green("[success]")
            for entry in [x for x in wiki_entries if Entry.fd in x.status]:
                maxsize = int(entry.maxsize[:-1])
                if entry.maxsize[-1] == "K": maxsize = maxsize/1024
                retention = int(entry.retention)
                val = int(maxsize + (maxsize * retention * compression))

                if size_fd > alloc_fd:
                    print("{:.<60}Maxsize: {}, Retention: {} = {}M".format(entry.logfile,
                        str(entry.maxsize), str(entry.retention), str(val)))

            print("{:.<60}".format("Results for ['{}']".format("foundation")), end="")
            if size_fd > alloc_fd: red("Total: {}m, Quota: {}m".format(str(size_fd), str(alloc_fd)))
            else: green("Total: {}M, Quota: {}M".format(str(size_fd), str(alloc_fd)))

        # Validate services disk usage
        #--------------------------------------------------------------------------------
        yellow("<[={:-^85}=]> ".format("Validating service disk quotas"), end="")
        if size_se > services: red("[failure]")
        else: green("[success]")

        # Display per service quotas
        entries = wiki_entries
        if hos: entries = hos_entries
        grouped_by_service = self.group_by_service(entries)
        for service_name, entries in sorted(grouped_by_service.items()):
            if not hos and not any([x for x in entries if Entry.se in x.status]): continue

            msg = ""
            size_per_se = 0
            if service:
                msg += "<[={:-^85}=]> \n".format("{} - disk usage".format(service_name))
            else: msg += "<[={:-^85}=]> \n".format(service_name)
            for entry in entries:
                maxsize = int(entry.maxsize[:-1])
                if entry.maxsize[-1] == "K": maxsize = maxsize/1024
                retention = int(entry.retention)
                val = int(maxsize + (maxsize * retention * compression))

                # Adjustments
                if service_name == "ceph": val *= 6  # ceph actually has 6 logs

                size_per_se += val
                msg += "{:.<60}Maxsize: {}, Retention: {} = {}M\n".format(entry.logfile,
                    str(entry.maxsize), str(entry.retention), str(val))

            if size_per_se > alloc_per_se: print(msg)
            print("{:.<60}".format("Results for ['{}']".format(entry.service)), end="")
            if size_per_se > alloc_per_se: red("Total: {}M, Quota: {}M".format(str(size_per_se), str(alloc_per_se)))
            else: green("Total: {}M, Quota: {}M".format(str(size_per_se), str(alloc_per_se)))

        print("{0:-<91}\n{0:-<91}\n{1:.<60}".format("", "Services total results"), end="")
        if size_se > services: red("Total: {}M, Quota: {}M".format(str(size_se), str(services)))
        else: green("Total: {}M, Quota: {}M".format(str(size_se), str(services)))

    def group_by_service(self, entries):
        """Sort log files by service first (e.g. /var/log/neutron)
        :entries: entries to sort by service
        :results: sorted entries by service
        """
        # Sort log files by service
        grouped_by_service = {}
        for entry in entries:
            if entry.service not in grouped_by_service:
                grouped_by_service[entry.service] = []
            grouped_by_service[entry.service].append(entry)
        return grouped_by_service

#----------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = 'kronos-util'
    version = '0.0.1'
    examples = "Validate all: python3 tools/{}.py --wiki ~/services.htm --all\n".format(app)
    examples = "Validate service: python3 tools/{}.py --wiki ~/services.htm --service=octavia\n".format(app)
    examples += "Validate disk usage: python3 tools/{}.py --wiki ~/services.htm --disk-usage\n".format(app)
    examples += "Validate service names: python3 tools/{}.py --wiki ~/services.htm --service-names\n".format(app)
    title = ("{0}_v{1}\n---------------------------------------------------------------------------------".format(app, version))
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--debug', action="store_true", help="Validate all parameters")
    parser.add_argument('--wiki', help="Wiki HTML data to parse and validate")
    parser.add_argument('--hos', help="Directory to search for HOS files")
    parser.add_argument('--all', action="store_true", help="Validate all parameters")
    parser.add_argument('--service', help="Validate service names")
    parser.add_argument('--service-names', dest="service_names", action="store_true", help="Validate service names")
    parser.add_argument('--hostgroups', action="store_true", help="Validate service's hostgroups")
    parser.add_argument('--users', action="store_true", help="Validate service's logfile users")
    parser.add_argument('--rotate-freq', dest="rotate_freq", action="store_true", help="Validate rotate frequency")
    parser.add_argument('--rotate-maxsize', dest="rotate_maxsize", action="store_true", help="Validate rotate maxsize")
    parser.add_argument('--rotate-retention', dest="rotate_retention", action="store_true", help="Validate rotate retention")
    parser.add_argument('--list-wiki', dest="list_wiki", action="store_true", help="List the wiki entries")
    parser.add_argument('--list-hos', dest="list_hos", action="store_true", help="List the HOS entries")
    parser.add_argument('--disk-usage', dest="disk_usage", action="store_true", help="Calculate disk usage for services")
    parser.add_argument('--disk-usage-hos', dest="disk_usage_hos", action="store_true", help="Calculate disk usage for services base on hos values")

    parser.add_argument('--rename', action="store_true", help="Rename HOS logrotate vars")

    args = parser.parse_args()

    # Execute
    validOpts = False
    result = True

    if args.wiki:
        print(title)
        validOpts = True

        # Set path correctly
        if not args.hos: args.hos = os.getcwd()
        if os.path.basename(args.hos) == "logging-ansible":
            args.hos = os.path.join(args.hos, 'roles/logging-common/vars')
        elif os.path.basename(args.hos) == "tools":
            args.hos = os.path.join(args.hos, '../roles/logging-common/vars')
        else:
            die("Error: incorrect hos source directory, run from logging-ansible")
        os.chdir(args.hos)

        hos_files = [x for x in os.listdir(args.hos) if ((os.path.basename(x).endswith('.yml')) \
                and os.path.basename(x) != 'services.yml')]
        kronos_util = KronosUtil(args.debug, args.wiki, hos_files)

        # List out the wiki entries
        if args.list_wiki:
            for x in sorted(kronos_util.wiki_entries, key=lambda y: y.service): print(x)

        # List out the hos entries
        elif args.list_hos:
            for x in sorted(kronos_util.hos_entries, key=lambda y: y.service): print(x)

        # Calculate disk usage for services
        elif args.disk_usage:
            kronos_util.disk_usage(args.service, args.disk_usage_hos)
        else:
            kronos_util.validate(args.all, args.service, args.service_names, args.hostgroups,
                args.users, args.rotate_freq, args.rotate_maxsize, args.rotate_retention)
            if args.all or args.service: kronos_util.disk_usage(args.service, args.disk_usage_hos)

    else:
        red("Error: You must specify the wiki file to scan (i.e. download the servies wiki page as html and specify its location with --wiki)")

    # Print out application usage, version and help
    if not validOpts:
        yellow(title)
        green(examples)
        parser.print_help()
