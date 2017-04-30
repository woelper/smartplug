import os
import platform
import subprocess
from subprocess import Popen, PIPE
import json
import logging
import time
import plistlib
import hashlib
import re

LOG_FILENAME = 'index.log'
# logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.info('Startup')

def hash_file(path, method):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

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
    # MACOS
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


    if platform.system() == 'Linux':
        logging.warning('Linux is not implemented yet')
        partitionsFile = open("/proc/partitions")
        lines = partitionsFile.readlines()[2:]#Skips the header lines
        for line in lines:
            words = [x.strip() for x in line.split()]
            minorNumber = int(words[1])
            deviceName = words[3]
            if minorNumber % 16 == 0:
                path = "/sys/class/block/" + deviceName
                if os.path.islink(path):
                    if os.path.realpath(path).find("/usb") > 0:
                        print "/dev/%s" % deviceName

    # if all fails, return an empty list
    return []


class Drive(object):
    """
    The drive class, holding all info necessary for
    a drive.
    """
    def __init__(self):
        self.root = None
        self.label = None
        self.id = None
        self.capacity = None
        self.available_space = None
        self.files = []
        self.timestamp = time.time()

    def __repr__(self):
        output = '\n{} class\n'.format(self.__class__.__name__)
        for k, v in self.__dict__.iteritems():
            output += '\t{}: {}\n'.format(k, v)
        return output

    def index(self):
        """
        Gather all files for the drive's mountpoint
        """
        if self.root is None:
            logging.error('Can not index, no root for drive')
            return
        logging.info('Indexing ' + self.label)
        for root, subdirs, files in os.walk(self.root):
            for f in files:
                self.files.append(os.path.join(root, f))



class JobRunner():
    def __init__(self):
        self.conf_path = 'config.json'
        # how often to poll for new drives
        self.interval = 5
        self.drives = []
        # the time in seconds until a drive is considered old and jobs
        # will be re-run
        self.time_threshold = 600


        # load config file
        with open(self.conf_path) as conffile:
            self.config = json.load(conffile)

        self.daemon()

    def daemon(self):
        while True:
            time.sleep(self.interval)

            drives_to_process = []

            for drive in list_drives():
                if drive.id not in [d.id for d in self.drives]:
                    logging.info('Drive change: Media ' + drive.label + ' added')
                    drives_to_process.append(drive)
                    self.drives.append(drive)
                else:
                    logging.info('Drive already known: ' + drive.label + ' ' + drive.id)


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
        """
        Executes a command
        """

        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        #TODO catch stderr and log errors
        # res = subprocess.check_output(cmd, shell=True)
        print stderr
        if stderr:
            logging.error(stderr)
        return stdout.rstrip()

    def run(self, drives):

        for drive in drives:
            drive.index()
            logging.info('Running job(s) on ' + drive.label)
            # print d
            for job in self.config['jobs']:
                logging.info('Running job ' + '"' + job['description'] + '"')
                # make filters case insensitive
                drive_filters = [n.lower() for n in job['drive_name_filters']]
                # same for labels
                drive_label = drive.label.lower()
                if drive_filters:
                    if not any(f in drive_label for f in drive_filters):
                        logging.info('Drive rejected by name filters: {} {}'.format(drive_label, drive_filters))
                        continue

                if job['drive_id_filters']:
                    if not drive.id in job['drive_id_filters']:
                        logging.info('Drive id filters specified, but id not in filter')
                        print drive.id, 'in', job['drive_id_filters']
                        continue

                if job['per_drive']:
                    logging.error('Not implemented')
                    continue

                for filename in drive.files:
                    if job['file_ext_filters']:
                        if not os.path.splitext(filename)[1].lower() in [fn.lower() for fn in job['file_ext_filters']]:
                            continue

                    # run job's command on file
                    # replace keywords
                    cmd = job['command'].replace('{PATH}', filename)
                    cmd = cmd.replace('{ID}', drive.id)
                    cmd = cmd.replace('{ROOT}', drive.root)
                    if '{MD5}' in cmd:
                        cmd = cmd.replace('{MD5}', hash_file(filename, 'md5'))

                    print self.run_cmd(cmd)



def main():
    i = JobRunner()


if __name__ == '__main__':
    main()