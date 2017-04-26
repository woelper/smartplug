import os
import sys
import platform
import subprocess
import json
import logging
import time

LOG_FILENAME = 'index.log'
# logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.info('Startup')

def list_drives(index=True):
    """
    Get a list of removable drives.
    """
    drives = []

    ### WINDOWS
    if platform.system() == 'Windows':
        logging.debug('Windows detected')
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
                if index:
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
        self.interval = 5
        self.drives = list_drives(index=False)

        # load config file
        with open(self.conf_path) as conffile:
            self.config = json.load(conffile)

        self.daemon()
        # self.run()

    def daemon(self):
        while True:
            time.sleep(self.interval)
            cur_ids = [d.id for d in list_drives(index=False)]
            cached_ids = [d.id for d in self.drives]
            print 'cached', cached_ids, 'current', cur_ids
            
            if not cur_ids:
                self.drives = list_drives(index=False)
            # if set(cur_ids) in set(cached_ids)
            new_drives = list(set(cur_ids).difference(set(cached_ids)))

            if new_drives:
                logging.info('drive change')
                self.drives = list_drives(index=False)
                

            # if len(list_drives()) != len(self.drives):
            #     logging.info('drive change')
            #     self.drives = list_drives()
                

    def run_cmd(self, cmd):
        #TODO catch stderr and log errors
        res = subprocess.check_output(cmd, shell=True)
        return res.rstrip()

    def run(self):
        drives = list_drives()
        # print self.config
        for drive in drives:
            # print d
            for job in self.config['jobs']:
                # make filters case insensitive
                drive_filters = [n.lower() for n in job['drive_name_filters']]
                # same for labels
                drive_label = drive.label.lower()
                if drive_filters:
                    if not any(f in drive_label for f in drive_filters):
                        logging.info('Drive rejected by name filters: {} {}'.format(drive_label, drive_filters))
                        return

                if job['per_drive']:
                    logging.error('Not implemented')
                    return

                for filename in drive.files:
                    if os.path.splitext(filename)[1].lower() in [fn.lower() for fn in job['file_ext_filters']]:

                        # run job's command on file
                        cmd = job['command'].replace('{PATH}', filename)
                        print self.run_cmd(cmd)


i = JobRunner()