#!/usr/bin/python3
import logging, time, os, subprocess

from systemd import journal
import RPi.GPIO as GPIO

# constants
LEVER_PIN = 4
LOG_FILE = '/var/log/veni-sh/remote_access-block.log'
SSH_TUNNEL_CMD = ['/usr/bin/ssh', '-N', '-F', '/home/veni-sh/.ssh/config', 'sanvewxyz-rpi-veni000-ssh-tunnel']
SSH_TUNNEL_CONNECT_TIMEOUT = 2

# logger setup
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=LOG_FILE,
    level=logging.INFO,
)
os.chmod(LOG_FILE, 0o640)
logging.getLogger().addHandler(journal.JournaldLogHandler())

# Classes
class SSHTunnel:
    '''
    Simple class to manage ssh tunnel process state.
    '''

    def __init__(self):
        self.process = None

    def open(self):
        '''
        Returns tunnel status (boolean)
        '''
        self.process = subprocess.Popen(
            SSH_TUNNEL_CMD,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        time.sleep(SSH_TUNNEL_CONNECT_TIMEOUT)
        if self.process.poll() is not None:
            logging.error(self.process.stderr.read())
            logging.error(f'SSH remote tunnel wasn\'t opened!:(')
        logging.info(f'SSH remote tunnel was opened!')

    def close(self):
        self.process.terminate()
        logging.info('Remote tunnel was closed!')

def main():
    logging.info('\'Remote access blocker\' has started!')

    # gpio setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LEVER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    tunnel = SSHTunnel()
    prev_val = GPIO.input(LEVER_PIN)
    logging.info(f"Initial value of GPIO_{LEVER_PIN} is {'HIGH (open)' if prev_val else 'LOW (close)'}")
    # init
    not prev_val and tunnel.open()
    while True:
        if GPIO.input(LEVER_PIN) != prev_val:
            if GPIO.input(LEVER_PIN) == GPIO.HIGH:
                logging.info(f'GPIO_{LEVER_PIN} is HIGH (open)')
                tunnel.close()
                prev_val = GPIO.HIGH
            else:
                logging.info(f'GPIO_{LEVER_PIN} is LOW (closed)')
                tunnel.open()
                prev_val = GPIO.LOW
        time.sleep(.01)

# MAIN
try:
    main()
except Exception as e:
    logging.exception(e, exc_info=True)
