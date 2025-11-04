# Installation local
* Activer le venv souhaité (cf. [config] Création venv)
* Mise à jour pip [facultatif] 
```
python -m pip install --upgrade pip
```
* Installation des dépendences
```
pip install -r requirements.txt
```


# Gestion en tant que package python
## Build du package
* Depuis le venv, installation du builder
```
python -m pip install --upgrade build
```
* Lancer le build
```
python -m build
```
*Le résultat du build sera généré dans le dossier dist*

## Install du package
### Mode développement
Depuis le venv souhaité, lancer la commande depuis la racine du projet
```
pip install -e .
```
*L'avantage est qu'il est possible de modififier / mettre des points d'arrets*
### Mode dépendance classique
Depuis le venv souhaité, lancer la commande au niveau du tar.gz généré par le build
```
pip install .
```


# [config] Fichier d'environnements
Penser à déposer manuellement les fichiers .env sur le serveur car ils ne sont pas stockées dans GitHub pour des raisons de sécurites

# [config] Création venv 
Installation d'un environnement virtuel (python 3.12.5 pour être iso serveur; prérequis avoir 3.12.5 en local)
```
py -3.12 -m venv .venv
```
Sur serveur Debian 11
```
python3.12 -m venv .venv
```

# [config] Download des dépendances en local
*La commande pip install directement sur le serveur ne fonctionne pas.* 
*Le contournement est de télécharger en local les librairies, de les déposer sur le serveur puis de les installer*
* Créer un venv avec une version python similaire à celle du serveur cible (cf. [config] Création venv)
* Lancer la commande depuis le dossier .libs
```
pip download --platform manylinux_2_28_x86_64 --only-binary=:all: -r ../requirements.txt
```
* Ajouter dans le dossier .libs le build (fichier .whl) des librairies in-house (tel que negoce-ct-datamanagement)
* Ajouter le dernier pip [facultatif]
```
pip download --platform manylinux_2_28_x86_64 --only-binary=:all: pip
```

# [config] Install des dépendances sur le serveur
*prérequis: [config] Download des dépendances en local*
* Activer le venv sur le serveur cible, dans le dossier .venv/bin
```
source activate
```
* Mise à jour de pip [facultatif], depuis le dossier .libs
```
pip install --no-index --find-links . --upgrade pip
```
* Installation des dépendances, depuis le dossier .libs
```
pip install --no-index --find-links . -r ../requirements.txt
```
* Penser à installer les dépendences in-house
```
pip install --no-index --find-links . negoce_ct_datamanagement==0.0.2
```
