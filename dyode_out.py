import os
import time
import yaml
import dyode
import signal
import logging
import netifaces

# Configuration du logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Fonction de gestion de la temporisation
def timeout_handler(signum, frame):
    raise TimeoutError

# Fonction pour une saisie avec temporisation
def input_with_timeout(prompt, timeout=10):
    # Associer le signal d'alarme à notre gestionnaire
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)  # Déclencher l'alarme après le temps imparti
    try:
        return input(prompt)
    except TimeoutError:
        print("\nTemps écoulé, confirmation automatique.")
        return ''  # Retourne une chaîne vide pour confirmer automatiquement
    finally:
        signal.alarm(0)  # Désactiver l'alarme

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
    # Continue to prompt until a valid selection is made
    while True:
        try:
            choice = int(input("Choisissez une interface (numéro) : ").strip())
            if 1 <= choice <= len(interfaces):
                return interfaces[choice - 1]
            else:
                print("Numéro invalide. Veuillez entrer un numéro valide.")
        except ValueError:
            print("Entrée invalide. Veuillez entrer un numéro valide.")

# Charger la configuration YAML et vérifier les paramètres
def load_config():
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)

    modules = config['modules']['file_transfer']
    properties = {
        'folder': modules['out'],
        'port': modules['port'],
        'bitrate': modules['bitrate'],
        'ip': config['dyode_in']['ip']
    }

    available_interfaces = get_available_interfaces()
    if 'interface' not in config['dyode_out']:
        chosen_interface = choose_interface(available_interfaces)
        properties['interface'] = chosen_interface
        log.info(f"Interface choisie : {chosen_interface}")
    else:
        properties['interface'] = config['dyode_out']['interface']
        if properties['interface'] not in available_interfaces:
            print(f"L'interface spécifiée '{properties['interface']}' n'est pas trouvée.")
            print("Interfaces réseau disponibles :")
            for i, iface in enumerate(available_interfaces, 1):
                print(f"{i}. {iface}")
            choice = input("Voulez-vous changer l'interface ? (y/n) : ").strip().lower()
            if choice == 'y':
                properties['interface'] = choose_interface(available_interfaces)
            else:
                print("Utilisation de l'interface par défaut ou tentative de continuer sans changement.")
    
    return properties
# Fonction pour vérifier la configuration avec l'utilisateur
def confirm_or_edit_properties(properties):
    print("\nConfiguration actuelle :")
    print(f"IP du destinataire : {properties['ip']}")
    print(f"Port : {properties['port']}")
    print(f"Interface : {properties['interface']}")
    print(f"Dossier d'envoi : {properties['folder']}")
    print(f"Débit (Mbps) : {properties['bitrate']}")
    
    choice = input_with_timeout("Est-ce correct ? (y/n) : ").strip().lower()
    if choice == 'y' or choice == '':
        return properties
    elif choice == 'n':
        # Permettre à l'utilisateur de modifier chaque champ
        properties['ip'] = input(f"Entrez l'IP du destinataire [{properties['ip']}]: ").strip() or properties['ip']
        properties['port'] = int(input(f"Entrez le port [{properties['port']}]: ").strip() or properties['port'])
        properties['folder'] = input(f"Entrez le chemin du dossier [{properties['folder']}]: ").strip() or properties['folder']
        properties['bitrate'] = input(f"Entrez le débit (Mbps) [{properties['bitrate']}]: ").strip() or properties['bitrate']
        
        # Re-demander l'interface réseau
        available_interfaces = get_available_interfaces()
        properties['interface'] = choose_interface(available_interfaces)
        print("\n⚠️ Avertissement : \nSi vous avez appliquez des changements, ils ne seront valables que pour cette session.\nAssurez vous de reporter la configuration dans votre config.yaml si vous la souhaitez persistante.\n")
        return confirm_or_edit_properties(properties)
    else:
        print("Choix non valide. Veuillez réessayer.")
        return confirm_or_edit_properties(properties)

def list_all_files(directory):
    files = []
    log.debug(f"Vérification du dossier : {directory}")  # Log pour vérifier le chemin du dossier
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            log.debug(f"Fichier trouvé : {full_path}")  # Log pour chaque fichier trouvé
            files.append(full_path)
    return files

def file_copy(params):
    files = list_all_files(params['folder'])
    log.debug(f"Fichiers détectés pour l'envoi : {files}")  # Log pour afficher les fichiers détectés
    if not files:
        log.debug("Aucun fichier détecté pour l'envoi.")
        return
    
    manifest_data = {f: dyode.hash_file(f) for f in files}
    manifest_filename = 'manifest.cfg'
    dyode.write_manifest(manifest_data, manifest_filename)

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
    # Charger et confirmer les paramètres
    properties = load_config()
    properties = confirm_or_edit_properties(properties)
    
    # Démarrer la surveillance du dossier et envoi des fichiers
    watch_folder(properties)
