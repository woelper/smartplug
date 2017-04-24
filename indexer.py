import os
import sys
import platform
import subprocess
import json
import logging

LOG_FILENAME = 'index.log'
logging.info('Startup')

def list_drives():
    """
    Get a list of removable drives.
    """
    drives = []
    ### WINDOWS
    if platform.system() == 'Windows':
        cmd = ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid,', 'volumename,', 'VolumeSerialNumber']
        result = subprocess.check_output(cmd)
        if 'DeviceID' in result:
            # collapse whitespace and get rid of multiple carriage returns. Omit first line.
            result = [' '.join(line.split()).split() for line in result.splitlines() if line.strip()][1:]
            for mountpoint, label, serial in result:
                d = Drive()
                d.root = mountpoint
                d.label = label
                d.id = serial
                drives.append(d)
            return drives
        else:
            return []



class Drive(object):
    def __init__(self):
        self.root = None
        self.label = None
        self.id = None


class Ingestor():
    def __init__(self):
        self.conf_path = 'config.json'
        self.filetypes = []

        with open(self.conf_path) as conffile:
            conf_data = json.load(conffile)
            self.filetypes = conf_data['config']['filetypes']
            # print conf_data

        self.run()

    def iterate_files(self, rootpath):
        for root, subdirs, files in os.walk(rootpath):
            for f in files:
                if not self.filetypes:
                    yield os.path.join(root, f)
                else:
                    if os.path.splitext(f)[1] in self.filetypes:
                        yield os.path.join(root, f)

    def run(self):
        drives = list_drives()
        for d in drives:
            for f in self.iterate_files(d.root):
                print f







i = Ingestor()