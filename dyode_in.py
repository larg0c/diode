import os
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
        'folder': modules['in'],
        'port': modules['port'],
        'ip': config['dyode_out']['ip']
    }

    # Vérifier si une interface est définie dans config.yaml, sinon en demander une
    available_interfaces = get_available_interfaces()
    if 'interface' not in config['dyode_in']:
        chosen_interface = choose_interface(available_interfaces)
        properties['interface'] = chosen_interface
        log.info(f"Interface choisie : {chosen_interface}")
    else:
        properties['interface'] = config['dyode_in']['interface']
        # Valider l'interface spécifiée
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
    print(f"IP de l'émetteur : {properties['ip']}")
    print(f"Port : {properties['port']}")
    print(f"Interface : {properties['interface']}")
    print(f"Dossier de réception : {properties['folder']}")
    
    # Utilisation de input_with_timeout pour que le script continue après 10 secondes avec "y" par défaut
    choice = input_with_timeout("Est-ce correct ? (y[10s]/n) : ").strip().lower()
    if choice == 'y' or choice == '':
        return properties
    elif choice == 'n':
        # Permettre à l'utilisateur de modifier chaque champ
        properties['ip'] = input(f"Entrez l'IP de l'émetteur [{properties['ip']}]: ").strip() or properties['ip']
        properties['port'] = int(input(f"Entrez le port [{properties['port']}]: ").strip() or properties['port'])
        properties['folder'] = input(f"Entrez le chemin du dossier [{properties['folder']}]: ").strip() or properties['folder']
        
        # Re-demander l'interface réseau
        available_interfaces = get_available_interfaces()
        properties['interface'] = choose_interface(available_interfaces) or properties['interface']
        print("\n⚠️ Avertissement :\nSi vous avez appliquez des changements, ils ne seront valables que pour cette session.\nAssurez vous de reporter la configuration dans votre config.yaml si vous la souhaitez persistante.\n")
        return confirm_or_edit_properties(properties)
    else:
        print("Choix non valide. Veuillez réessayer.")
        return confirm_or_edit_properties(properties)

# Fonction principale pour recevoir les fichiers
def wait_for_file(params):
    manifest_filename = 'manifest.cfg'
    dyode.receive_file(manifest_filename, params['port'], params['ip'], params['interface'])

    if os.path.exists(manifest_filename):
        with open(manifest_filename, 'r') as manifest_file:
            log.debug(f"Contenu du fichier manifeste reçu :\n{manifest_file.read()}")

    files = dyode.parse_manifest(manifest_filename)
    if not files:
        log.error("Aucun fichier reçu.")
        return
    
    for f, expected_hash in files.items():
        temp_file = os.path.join(params['folder'], os.path.basename(f))
        dyode.receive_file(temp_file, params['port'], params['ip'], params['interface'])

        if dyode.hash_file(temp_file) != expected_hash:
            log.error(f"Checksum invalide pour le fichier {f}.")
            os.remove(temp_file)
        else:
            log.info(f"Fichier {temp_file} reçu avec succès.")

if __name__ == '__main__':
    # Charger et confirmer les paramètres
    properties = load_config()
    properties = confirm_or_edit_properties(properties)
    
    # Boucle d'attente pour les fichiers
    while True:
        wait_for_file(properties)
