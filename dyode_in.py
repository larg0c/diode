import os
import hashlib
import logging
import subprocess
import shlex
from configparser import ConfigParser

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def hash_file(file):
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def write_manifest(files, manifest_filename):
    config = ConfigParser()
    config.add_section('Files')
    for f in files:
        config.set('Files', f, files[f])

    with open(manifest_filename, 'w') as configfile:
        config.write(configfile)

def parse_manifest(file):
    parser = ConfigParser()
    parser.read(file)
    if 'Files' not in parser.sections():
        log.error("La section [Files] est manquante dans le fichier manifeste.")
        return {}
    
    return {item: value for item, value in parser.items('Files')}

def send_file(file, port_base, max_bitrate, ip):
    command = f'udp-sender --async --fec 8x16/64 --max-bitrate {max_bitrate}m --mcast-rdv-addr {ip} --portbase {port_base} --autostart 1 --interface eth0 -f \'{file}\''
    log.debug(command)
    subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, shell=False).communicate()

def receive_file(filepath, portbase, ip):
    command = f'udp-receiver --nosync --mcast-rdv-addr {ip} --interface eth1 --portbase {portbase} -f \'{filepath}\''
    log.debug(command)
    subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
