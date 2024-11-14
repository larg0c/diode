import os
import dyode
import logging
from configparser import ConfigParser

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def wait_for_file(params):
    manifest_filename = 'manifest.cfg'
    dyode.receive_file(manifest_filename, params['port'], params['ip'])

    files = dyode.parse_manifest(manifest_filename)
    if not files:
        log.error("Aucun fichier reçu.")
        return
    
    for f, expected_hash in files.items():
        temp_file = os.path.join(params['out'], os.path.basename(f))
        dyode.receive_file(temp_file, params['port'], params['ip'])

        if dyode.hash_file(temp_file) != expected_hash:
            log.error(f"Checksum invalide pour le fichier {f}.")
            os.remove(temp_file)
        else:
            log.info(f"Fichier {temp_file} reçu avec succès.")

if __name__ == '__main__':
    with open('config.yaml', 'r') as config_file:
        config = ConfigParser()
        config.read_file(config_file)

    modules = config['modules']['file_transfer']
    properties = {
        'out': modules['out'],
        'port': modules['port'],
        'ip': config['dyode_out']['ip']
    }

    while True:
        wait_for_file(properties)
