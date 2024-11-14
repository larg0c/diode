# Guide d'Installation

Ce guide d'installation explique comment configurer l'environnement et installer les dépendances pour exécuter le projet de transfert de fichiers via UDP en Python 3.

## Prérequis

- **Python 3.x** : Assurez-vous d'avoir Python 3 installé sur votre machine.
- **Modules Python** : Installez les modules nécessaires via `pip`.

### Installation des dépendances

1. Clonez le dépôt ou copiez les fichiers suivants dans un répertoire de travail :
   - dyode.py
   - dyode_in.py
   - dyode_out.py
   - modbus.py
   - screen.py

2. Installez les dépendances Python nécessaires :
    ```bash
    pip install pyyaml pyinotify pymodbus configparser netifaces
    ```
3. Installez les dépendances systèmes nécessaires :
   ```bash
   sudo apt update && sudo apt install net-tools && apt install ufw -y
   sudo ufw allow 9000/udp
   ```


### Configuration

1. **Fichier de Configuration** : Assurez-vous que le fichier `config.yaml` est présent dans le répertoire de travail. Ce fichier doit contenir les paramètres suivants :
   - `dyode_in` et `dyode_out` avec l'IP et l'adresse MAC pour définir les endpoints d'entrée et de sortie.
   - `modules` pour définir les modules activés et leurs paramètres.

2. **Exécution** :
   - Pour démarrer le processus d'entrée (dyode_in), exécutez :
     ```bash
     python3 dyode_in.py
     ```
   - Pour démarrer le processus de sortie (dyode_out), exécutez :
     ```bash
     python3 dyode_out.py
     ```

## Remarques

- Les scripts `dyode.py`, `modbus.py` et `screen.py` sont appelés par `dyode_in.py` et `dyode_out.py` pour gérer différents modules de transfert.
- Assurez-vous que les ports UDP nécessaires sont ouverts et accessibles entre les endpoints pour permettre le transfert de fichiers.
