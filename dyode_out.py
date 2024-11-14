import os
import time
import dyode
import yaml
import logging
from configparser import ConfigParser

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def list_all_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def file_copy(params):
    files = list_all_files(params['in'])
    if not files:
        log.debug("Aucun fichier détecté pour l'envoi.")
        return
    
    manifest_data = {f: dyode.hash_file(f) for f in files}
    manifest_filename = 'manifest.cfg'
    dyode.write_manifest(manifest_data, manifest_filename)

    dyode.send_file(manifest_filename, params['port'], params['bitrate'], params['ip'])
    os.remove(manifest_filename)

    for f in files:
        dyode.send_file(f, params['port'], params['bitrate'], params['ip'])
        os.remove(f)

def watch_folder(params):
    while True:
        file_copy(params)
        time.sleep(10)

if __name__ == '__main__':
    # Charger la configuration depuis le fichier YAML
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    # Extraire les informations nécessaires pour dyode_out
    modules = config['modules']['file_transfer']
    properties = {
        'in': modules['in'],                  # Dossier de surveillance
        'port': modules['port'],              # Port de transfert
        'bitrate': modules['bitrate'],        # Débit
        'ip': config['dyode_in']['ip']        # IP de dyode_in pour l'envoi
    }
    watch_folder(properties)
