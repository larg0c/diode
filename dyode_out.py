import os
import time
import dyode
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
    with open('config.yaml', 'r') as config_file:
        config = ConfigParser()
        config.read_file(config_file)
    
    modules = config['modules']['file_transfer']
    properties = {
        'in': modules['in'],
        'port': modules['port'],
        'bitrate': modules['bitrate'],
        'ip': config['dyode_in']['ip']
    }
    watch_folder(properties)
