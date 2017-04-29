import os
import sys
import platform
import subprocess
import json
import logging
import time
import plistlib

LOG_FILENAME = 'index.log'
# logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.info('Startup')

def list_drives():
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
                drives.append(d)
            return drives
        else:
            return []

    if platform.system() == 'Darwin':
        logging.debug('MacOS detected')
        # gather disk info with diskutil
        cmd = ['diskutil', 'list', '-plist']
        result = subprocess.check_output(cmd)
        
        disks = plistlib.readPlistFromString(result)
        for disk in disks['AllDisks']:
            infocmd = ['diskutil', 'info', '-plist', disk]
            try:
                inforesult = subprocess.check_output(infocmd)
            except subprocess.CalledProcessError as err:
                logging.error('Could not access disk ' + disk)
                continue
            diskinfo = plistlib.readPlistFromString(inforesult)
            if diskinfo['Internal'] == False and diskinfo['MountPoint'] != '':
                d = Drive()
                d.root = diskinfo['MountPoint']
                d.id = diskinfo['VolumeUUID']
                d.label = diskinfo['VolumeName']
                drives.append(d)
        return drives

            
            
        #diskutil info -plist <disk>
        
        # for disk in plist['AllDisksAndPartitions']:
        #     for key, value in disk.iteritems():
        #         print key, '\t', value
    

    return []

class Drive(object):
    def __init__(self):
        self.root = None
        self.label = None
        self.id = None
        self.files = []
        self.timestamp = time.time()
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
        logging.info('Indexing ' + self.label)
        for root, subdirs, files in os.walk(self.root):
            for f in files:
                self.files.append(os.path.join(root, f))


# class Job(object):


class JobRunner():
    def __init__(self):
        self.conf_path = 'config.json'
        self.interval = 5
        self.drives = []

        self.time_threshold = 40

        # load config file
        with open(self.conf_path) as conffile:
            self.config = json.load(conffile)

        self.daemon()
        # self.run()

    def daemon(self):
        while True:
            time.sleep(self.interval)

            drives_to_process = []

            for drive in list_drives():
                if drive.id not in [d.id for d in self.drives]:
                    logging.info('Drive change: Media ' + drive.label + ' added')
                    drives_to_process.append(drive)
                    self.drives.append(drive)

            for drive in self.drives:
                timedelta = time.time() - drive.timestamp
                if timedelta > self.time_threshold:
                    drives_to_process.append(drive)
                    print 'too old:', drive.label
                    # reset
                    drive.timestamp = time.time()


            print 'Process:', drives_to_process

            # run jobs
            self.run(drives_to_process)
                

    def run_cmd(self, cmd):
        #TODO catch stderr and log errors
        res = subprocess.check_output(cmd, shell=True)
        return res.rstrip()

    def run(self, drives):

        for drive in drives:
            drive.index()
            logging.info('Running job(s) on ' + drive.label)
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