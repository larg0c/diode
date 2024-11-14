# -*- coding: utf-8 -*-
import yaml
import asyncore
import pyinotify
import string
import random
import shutil
import threading
import sys
import time
import subprocess
import os
import logging
import hashlib
from math import floor
import datetime
import multiprocessing
import shlex
from configparser import ConfigParser  # Modification pour Python 3

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

######################## Reception specific functions ##########################

def parse_manifest(file):
    parser = ConfigParser()
    parser.read(file)
    if 'Files' not in parser.sections():
        log.error("La section [Files] est manquante dans le fichier manifeste.")
        return {}
    
    files = {}
    for item, value in parser.items('Files'):
        log.debug(item + ' :: ' + value)
        files[item] = value
    return files

# Boucle de réception des fichiers
def file_reception_loop(params):
    while True:
        wait_for_file(params)
        time.sleep(10)

# Lancer UDPCast pour recevoir un fichier
def receive_file(filepath, portbase, ip):
    log.debug(portbase)
    # Utilisation de l'IP depuis le paramètre `ip` au lieu d'une IP en dur
    command = f'udp-receiver --nosync --mcast-rdv-addr {ip} --interface eth1 --portbase {portbase} -f \'{filepath}\''
    log.debug(command)
    p = subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()

# Fonction d'attente de réception de fichier
def wait_for_file(params):
    log.debug('En attente de fichier ...')
    log.debug(datetime.datetime.now())
    process_name = multiprocessing.current_process().name
    manifest_filename = 'manifest_' + process_name + '.cfg'
    receive_file(manifest_filename, params['port'], params['dyode_in']['ip'])  # Ajoutez ici l'IP du YAML
    files = parse_manifest(manifest_filename)
    if len(files) == 0:
        log.error('Aucun fichier détecté')
        return 0
    log.debug('Contenu du manifeste : %s' % files)
    for f in files:
        filename = os.path.basename(f)
        temp_file = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
        receive_file(temp_file, params['port'])
        log.info('Fichier ' + f + ' reçu')
        log.debug(datetime.datetime.now())
        if hash_file(temp_file) != files[f]:
            log.error('Checksum invalide pour le fichier ' + f)
            os.remove(f)
            log.error('Calcul de l’empreinte du prochain fichier...')
            continue
        else:
            log.info('Les empreintes correspondent !')
            shutil.move(temp_file, params['out'] + '/' + filename)
            log.info('Fichier ' + filename + ' disponible dans ' + params['out'])
    os.remove(manifest_filename)

################### Fonctions pour l'envoi de fichiers #########################

def send_file(file, port_base, max_bitrate):
    command = 'udp-sender --async --fec 8x16/64 --max-bitrate ' \
              + str('{:0.0f}'.format(max_bitrate)) \
              + 'm --mcast-rdv-addr 10.0.1.2 --mcast-data-addr 10.0.1.2 ' \
              + '--portbase ' + str(port_base) + ' --autostart 1 ' \
              + '--interface eth0 -f ' + '\'' + str(file) + '\''
    log.debug(command)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, shell=False)
    output, err = p.communicate()

# Fonction pour lister tous les fichiers d'un répertoire de façon récursive
def list_all_files(dir):
    files = []
    for root, directories, filenames in os.walk(dir):
        for directory in directories:
            files.append(os.path.join(root, directory))
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def write_manifest(files, manifest_filename):
    config = ConfigParser()
    config.add_section('Files')
    log.debug('Fichiers...')
    log.debug(files)
    for f in files:
        config.set('Files', f, files[f])
        log.debug(f + ' :: ' + files[f])

    with open(manifest_filename, 'w') as configfile:
        config.write(configfile)

def file_copy(params):
    log.debug('Début de la copie locale...')

    files = list_all_files(params[1]['in'])
    log.debug('Liste des fichiers : ' + str(files))
    if len(files) == 0:
        log.debug('Aucun fichier détecté')
        return 0
    
    manifest_data = {}
    for f in files:
        manifest_data[f] = hash_file(f)
    
    # Log pour afficher le contenu de manifest_data
    log.debug("Contenu du fichier manifeste : " + str(manifest_data))

    log.debug('Écriture du fichier manifeste')
    manifest_filename = 'manifest_' + str(params[0]) + '.cfg'
    write_manifest(manifest_data, manifest_filename)
    log.info('Envoi du fichier manifeste : ' + manifest_filename)

    send_file(manifest_filename, params[1]['port'], params[1]['bitrate'])
    log.debug('Suppression du fichier manifeste')
    os.remove(manifest_filename)
    for f in files:
        log.info('Envoi de ' + f)
        send_file(f, params[1]['port'], params[1]['bitrate'])
        log.info('Suppression de ' + f)
        os.remove(f)

########################### Fonctions partagées ################################

def hash_file(file):
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()
