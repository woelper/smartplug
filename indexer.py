import os
import sys
import platform
import subprocess
import json

class Drive(object):
    def __init__(self):
        self.root = None
        self.label = None

# wmic logicaldisk where drivetype=2 get deviceid, volumename, description



def list_drives():
    drives = []

    if platform.system() == 'Windows':
        # cmd = ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid,', 'volumename,', 'description']
        cmd = ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid,', 'volumename']
        result = subprocess.check_output(cmd)
        if 'DeviceID' in result:
            # collapse whitespace and get rid of multiple carriage returns. Omit first line.
            result = [' '.join(line.split()).split() for line in result.splitlines() if line.strip()][1:]
            for mountpoint, label in result:
                d = Drive()
                d.root = mountpoint
                d.label = label
                drives.append(d)
                # print mountpoint, label
            return drives
        else:
            return []


class Ingestor():

    def __init__(self):
        self.conf_path = 'config.json'
        self.filetypes = []


        with open(self.conf_path) as conffile:
            conf_data = json.load(conffile)
            self.filetypes = conf_data['config']['filetypes']
            print conf_data

        self.run()

    def run(self):

        drives = list_drives()

        for d in drives:
            for root, subdirs, files in os.walk(d.root):
                for f in files:
                    if not self.filetypes:
                        print os.path.join(root, f)
                    else:
                        if os.path.splitext(f)[1] in self.filetypes:
                            print os.path.join(root, f)

i = Ingestor()