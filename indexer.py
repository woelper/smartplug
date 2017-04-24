import os
import sys
import platform
import subprocess
import json
import logging

LOG_FILENAME = 'index.log'
# logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logging.info('Startup')

def list_drives():
    """
    Get a list of removable drives.
    """
    drives = []

    ### WINDOWS
    if platform.system() == 'Windows':
        logging.info('Windows detected')
        cmd = ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid,', 'volumename,', 'VolumeSerialNumber']
        result = subprocess.check_output(cmd)
        if 'DeviceID' in result:
            # collapse whitespace and get rid of multiple carriage returns. Omit first line.
            result = [' '.join(line.split()).split() for line in result.splitlines() if line.strip()][1:]
            for mountpoint, label, serial in result:
                logging.debug('{} {} {}'.format(mountpoint, label, serial))
                d = Drive()
                d.root = mountpoint
                d.label = label
                d.id = serial
                d.index()
                drives.append(d)
            return drives
        else:
            return []



class Drive(object):
    def __init__(self):
        self.root = None
        self.label = None
        self.id = None
        self.files = []
        # self.index()

    def __repr__(self):  
        output = '\n{} class\n'.format(self.__class__.__name__)
        for k, v in self.__dict__.iteritems():
            output += '\t{}: {}\n'.format(k, v)
        return output

    def index(self):
        if self.root is None:
            logging.error('Can not index, no root for drive')
            return
        for root, subdirs, files in os.walk(self.root):
            for f in files:
                self.files.append(os.path.join(root, f))


# class Job(object):


class JobRunner():
    def __init__(self):
        self.conf_path = 'config.json'
        
        with open(self.conf_path) as conffile:
            self.config = json.load(conffile)

        self.run()

    # def iterate_files(self, rootpath):
    #     for root, subdirs, files in os.walk(rootpath):
    #         for f in files:
    #             if not self.filetypes:
    #                 yield os.path.join(root, f)
    #             else:
    #                 if os.path.splitext(f)[1] in self.filetypes:
    #                     yield os.path.join(root, f)

    def run(self):
        drives = list_drives()
        # print self.config
        for drive in drives:
            # print d
            for job in self.config['jobs']:

                drive_filters = [n.lower() for n in job['drive_name_filters']]
                if drive_filters:
                    if drive.label.lower() not in drive_filters:
                        logging.info('Drive rejected by name filters')
                        return

                if job['per_drive']:
                    logging.error('Not implemented')
                    return

            for f in drive.files:
                if os.path.splitext(f)[1].lower() in [fn.lower() for fn in job['file_ext_filters']]:
                    # print f
                    # run command on file
                    cmd = job['command'].replace('{PATH}', f)
                    res = subprocess.check_output(cmd, shell=True)
                    print res


i = JobRunner()