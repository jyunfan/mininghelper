#!/usr/bin/env python
# Miner Guard - Ensure your miners are always working
# This program starts cgminer in background and monitors the hashrates.
# When hashrates below specified thresholds, cgminer will be restared.
# If hashrates are not back to normal after restarting, the system is rebooted.

import ConfigParser
import logging
import os
import re
import signal
import socket
import sys
import subprocess
import time
from distutils.dir_util import mkpath

logger = logging.getLogger( __name__ )

# IP and port of cgminer
HOST, PORT = 'localhost', 4028

# Interval in seconds
MONITOR_INTERVAL = 60

# Get hash rates via cgminer API
def get_hashrates():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        sock.sendall('devs\n')
        received = sock.recv(4096)

        # Parse result
        hashrates = [int(x) for x in re.findall('5s=(\d+)', received)]
    except:
        hashrates = []
    return hashrates

def startminer(cmd):
    logger.info('starting cgminer')
    p = subprocess.Popen(cmd)
    # Wait cgminer starts
    time.sleep(MONITOR_INTERVAL)
    return p

def main(settings):
    thresholds = [int(x) for x in settings['hashrate_thresholds']]

    p = startminer(settings['cgminer'])
    if p.poll() != None:
        error_exit('cannot start miner')
    error_status = False

    try:
        while True:
            # Check if cgminer is still running
            if p.poll() != None:
                logger.warn('cgminer is not running.')
                if error_statue:
                    # Fatal error.  Restart the system.
                    logger.error('cgminer is not running.  Reboot the system to resolve this problem.')
                    #os.system('reboot')
                    sys.exit(1)

                error_count = True
                logger.error('cgminer is not running.  Try restarting cgminer.')
                # Restart cgminer
                p = startminer(settings['cgminer'])
                continue

            error_status = False

            hashrates = get_hashrates()
            if hashrates == []:
                logger.warn('Cannot get hash rates')
            logger.info('Hash rates: %s' % ','.join(str(x) for x in hashrates))

            # Compare hash rates
            if len(hashrates) != len(thresholds):
                logger.warn('Expect get %d hashrates but only get %d.  Restart cgminer.' % (len(thresholds), len(hashrates)))
                p.kill()
                time.sleep(MONITOR_INTERVAL)
                p = startminer(settings['cgminer'])
                continue
            satisfied = True
            for real,expect in zip(hashrates, thresholds):
                if real < expect:
                    satisfied = False
                    logger.warn('Hash rate %d < expected hash rate %d.  Restart cgminer.' % (real, expect))
                    break
            if satisfied == False:
                p.kill()
                time.sleep(MONITOR_INTERVAL)
                p = startminer(settings['cgminer'])
                continue

            time.sleep(MONITOR_INTERVAL)
    finally:
        logger.info('stop cgminer')
        p.kill()

def error_exit(msg):
    logger.error(msg)
    sys.stderr.writelines(msg)
    sys.exit(1)

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    app_path = os.path.join(os.environ.get('HOME', ''), '.minerguard')
    mkpath(app_path)

    log_file = os.path.join(app_path, 'log')
    logging.basicConfig(level=logging.DEBUG,
                        filename=log_file,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    conf_file = os.path.join(app_path, 'config')

    # Generate an example if the config file does not exist.
    if not os.path.exists(conf_file):
        msg = 'Config file does not exist.  Automatically created one at %s.  Please change the setting to fit your environment.' % conf_file
        with open(conf_file, 'w') as f:
            f.write("[settings]\ncgminer=mock_cgminer\nhashrate_thresholds=1\n")
        f.close()
        error_exit(msg)

    config = ConfigParser.ConfigParser()
    try:
        config.read(conf_file)
    except:
        msg = 'Cannot read %s correctly.  Please make sure the file exists and contains correct settings.' % conf_file
        error_exit(msg)
    if not 'settings' in config._sections.keys():
        error_exit('The [settings] section is missing.')
    settings = config._sections['settings']
    for key in ['cgminer', 'hashrate_thresholds']:
        if not key in settings:
            error_exit('key %s is missing' % key)
        settings[key] = settings[key].split()

    logger.debug('Minerguard starting')
    main(settings)
