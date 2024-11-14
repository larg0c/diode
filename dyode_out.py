import os
import time
import yaml
import dyode
import logging
from configparser import ConfigParser

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Charger la configuration YAML
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Extraire les informations de configuration pour dyode_out
modules = config['modules']['file_transfer']
properties = {
    'out': modules['out'],                      # Dossier surveillé pour envoi
    'port': modules['port'],                  # Port de transfert
    'bitrate': modules['bitrate'],            # Débit en Mbps
    'ip': config['dyode_in']['ip'],           # IP de dyode_in pour l'envoi
    'interface': config['dyode_out']['interface']  # Interface réseau pour l'envoi
}

def list_all_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def file_copy(params):
    files = list_all_files(params['out'])
    if not files:
        log.debug("Aucun fichier détecté pour l'envoi.")
        return
    
    manifest_data = {f: dyode.hash_file(f) for f in files}
    manifest_filename = 'manifest.cfg'
    dyode.write_manifest(manifest_data, manifest_filename)
    
    # Ajouter un log pour vérifier le contenu du fichier manifeste
    with open(manifest_filename, 'r') as manifest_file:
        log.debug(f"Contenu du fichier manifeste généré :\n{manifest_file.read()}")

    dyode.send_file(manifest_filename, params['port'], params['bitrate'], params['ip'], params['interface'])
    os.remove(manifest_filename)

    for f in files:
        dyode.send_file(f, params['port'], params['bitrate'], params['ip'], params['interface'])
        os.remove(f)


def watch_folder(params):
    while True:
        file_copy(params)
        time.sleep(10)

if __name__ == '__main__':
    # Lancement de la surveillance du dossier et envoi des fichiers
    watch_folder(properties)
