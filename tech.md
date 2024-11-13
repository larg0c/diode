# Documentation Technique

Ce document décrit en détail la configuration technique mise en place pour le transfert de fichiers via UDP entre deux machines, séparées par une diode réseau unidirectionnelle.

## Objectif du Projet

L'objectif est de permettre un transfert de fichiers unidirectionnel entre deux machines sans connexion TCP, en utilisant le protocole UDP. Le transfert doit être fiable malgré l'absence de connexion bidirectionnelle.

## Architecture et Modules

1. **dyode.py** : Ce fichier définit les fonctions principales pour envoyer et recevoir des fichiers via UDP.
   - Fonction `send_file` : Segmente les fichiers en paquets UDP pour l'envoi.
   - Fonction `file_reception_loop` : Attend les fichiers en UDP et les assemble.

2. **dyode_in.py** : Script pour surveiller un dossier d'entrée et envoyer les fichiers détectés via UDP.
   - Utilisation de `pyinotify` pour détecter les nouveaux fichiers dans le dossier.
   - Appelle `dyode.send_file` pour chaque fichier détecté.

3. **dyode_out.py** : Gère la réception des fichiers envoyés depuis l'entrée.
   - Utilise `asyncore` pour gérer les événements réseau et recevoir les paquets.
   - Assemble les paquets UDP pour recréer les fichiers d'origine.

4. **modbus.py et screen.py** : Modules auxiliaires pour étendre les capacités de transfert (éventuellement pour d'autres types de données).

## Détails Techniques

### Protocole de Transfert (UDP)

Le choix de l'UDP permet de réaliser un transfert unidirectionnel compatible avec la diode réseau. Chaque fichier est segmenté et envoyé en paquets de taille fixe, avec un identifiant de séquence pour chaque segment.

### Intégrité des Données

1. **Segmentation des Paquets** : Chaque segment inclut une taille fixe et un numéro de séquence pour garantir la bonne reconstitution des fichiers.
2. **Hachage SHA-256** : Un hachage est calculé pour chaque fichier envoyé, permettant à la machine de réception de vérifier l'intégrité une fois la réception terminée.

### Gestion des Paquets

Pour chaque fichier :
- Le fichier est divisé en segments de 2048 octets pour garantir qu'ils passent en une seule trame UDP.
- Chaque segment est envoyé via `socket.sendto()` à une adresse et un port définis.

Le récepteur collecte les paquets en vérifiant les numéros de séquence, puis les assemble pour recréer le fichier.

## Sécurité et Performance

- **Performance** : Une pause de 0,2 ms est introduite entre les envois de paquets pour éviter la surcharge réseau.
- **Sécurité** : Seuls les fichiers provenant d'adresses IP autorisées sont traités, minimisant les risques d'injection de données incorrectes.

---

Ce système offre une méthode fiable et simple de transfert de fichiers, adaptée aux environnements unidirectionnels avec des diodes réseau.
"""

# Enregistrement des fichiers
with open(os.path.join(output_directory, 'INSTALL.md'), 'w') as f:
    f.write(install_md_content)

with open(os.path.join(output_directory, 'TECH.md'), 'w') as f:
    f.write(tech_md_content)

# Affichage des chemins des fichiers créés pour téléchargement
output_files = {
    'INSTALL.md': os.path.join(output_directory, 'INSTALL.md'),
    'TECH.md': os.path.join(output_directory, 'TECH.md')
}
output_files