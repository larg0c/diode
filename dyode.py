import yaml
import shlex
import hashlib
import logging
import subprocess
from configparser import ConfigParser

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Charger la configuration YAML (exemple d'utilisation de yaml pour config.yaml)
def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Fonction de hachage des fichiers
def hash_file(file):
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

# Écriture du fichier manifeste au format .cfg (en utilisant ConfigParser pour un fichier INI)
def write_manifest(files, manifest_filename):
    config = ConfigParser()
    config.add_section('Files')
    for f in files:
        config.set('Files', f, files[f])

    with open(manifest_filename, 'w') as configfile:
        config.write(configfile)

# Lecture du fichier manifeste (format .cfg)
def parse_manifest(file):
    parser = ConfigParser()
    parser.read(file)
    if 'Files' not in parser.sections():
        log.error("La section [Files] est manquante dans le fichier manifeste.")
        return {}
    
    return {item: value for item, value in parser.items('Files')}

# Envoi de fichier via UDP
def send_file(file, port_base, max_bitrate, ip, interface):
    command = f'udp-sender --async --fec 8x16/64 --max-bitrate {max_bitrate}m --mcast-rdv-addr {ip} --portbase {port_base} --autostart 1 --interface {interface} -f \'{file}\''
    log.debug(command)
    subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, shell=False).communicate()

# Réception de fichier via UDP
def receive_file(filepath, portbase, ip, interface):
    command = f'udp-receiver --nosync --mcast-rdv-addr {ip} --interface {interface} --portbase {portbase} -f \'{filepath}\''
    log.debug(command)
    subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()