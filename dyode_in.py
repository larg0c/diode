import os
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

# Extraire les informations de configuration pour dyode_in
modules = config['modules']['file_transfer']
properties = {
    'in': modules['in'],                   # Dossier pour enregistrer les fichiers reçus
    'port': modules['port'],                  # Port de transfert
    'ip': config['dyode_out']['ip'],          # IP de dyode_out pour réception
}

# Vérifier si une interface est définie dans config.yaml, sinon en demander une
if 'interface' not in config['dyode_in']:
    available_interfaces = get_available_interfaces()
    if not available_interfaces:
        log.error("Aucune interface réseau disponible.")
        exit(1)
    chosen_interface = choose_interface(available_interfaces)
    properties['interface'] = chosen_interface
    log.info(f"Interface choisie : {chosen_interface}")
else:
    properties['interface'] = config['dyode_in']['interface']


def wait_for_file(params):
    manifest_filename = 'manifest.cfg'
    dyode.receive_file(manifest_filename, params['port'], params['ip'], params['interface'])

    # Vérifier le contenu du fichier manifeste après réception
    if os.path.exists(manifest_filename):
        with open(manifest_filename, 'r') as manifest_file:
            log.debug(f"Contenu du fichier manifeste reçu :\n{manifest_file.read()}")

    files = dyode.parse_manifest(manifest_filename)
    if not files:
        log.error("Aucun fichier reçu.")
        return
    
    for f, expected_hash in files.items():
        temp_file = os.path.join(params['in'], os.path.basename(f))
        dyode.receive_file(temp_file, params['port'], params['ip'], params['interface'])

        if dyode.hash_file(temp_file) != expected_hash:
            log.error(f"Checksum invalide pour le fichier {f}.")
            os.remove(temp_file)
        else:
            log.info(f"Fichier {temp_file} reçu avec succès.")

if __name__ == '__main__':
    # Boucle d'attente pour les fichiers
    while True:
        wait_for_file(properties)