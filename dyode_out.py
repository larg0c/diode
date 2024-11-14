import os
import time
import yaml
import dyode
import logging
import netifaces
from configparser import ConfigParser

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Fonction pour détecter les interfaces réseau disponibles
def get_available_interfaces():
    interfaces = netifaces.interfaces()
    available_interfaces = [iface for iface in interfaces if iface != 'lo']
    return available_interfaces

# Fonction pour demander à l'utilisateur de choisir une interface
def choose_interface(interfaces):
    print("Interfaces réseau disponibles :")
    for i, iface in enumerate(interfaces, 1):
        print(f"{i}. {iface}")
    choice = int(input("Choisissez une interface (numéro) : ")) - 1
    return interfaces[choice]

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
}

# Vérifier si une interface est définie dans config.yaml, sinon en demander une
if 'interface' not in config['dyode_out']:
    available_interfaces = get_available_interfaces()
    if not available_interfaces:
        log.error("Aucune interface réseau disponible.")
        exit(1)
    chosen_interface = choose_interface(available_interfaces)
    properties['interface'] = chosen_interface
    log.info(f"Interface choisie : {chosen_interface}")
else:
    properties['interface'] = config['dyode_out']['interface']

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
