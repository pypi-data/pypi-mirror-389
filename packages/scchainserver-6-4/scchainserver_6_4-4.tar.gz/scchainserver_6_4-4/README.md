# Application d'administration en ligne de commande et package de développement Python pour SCENARIchain-server 6.4

`scchainserver_6_4` fournit :
  * une application en ligne de commande permettant d'administrer un serveur SCENARIchain-server 6.4 ;
  * un package de développement Python permettant d'instancier un objet `portal` à utiliser avec l'API [scenaripy_api](https://pypi.org/project/scenaripy-api).

## Utilisation de la commande d'administration
```
scchainserver_6_4 [commande] [paramètres] [conf] [-v]
 - [commande] : Voir la liste des commandes disponibles avec --help.
 - [paramètres] : Certaines commandes acceptent des paramètres, voir les détails avec --help

 - [conf] : paramètres de la configuration du serveur. Valeurs possibles :
   -u [login] ou --user [login] : surcharge du nom de l'utilisateur
   -p [password] ou --password [password] : surcharge du mot de passe
   -c [./maconf.json] ou --conf [./maconf.json] : surcharge de la conf du portail
   -l ou --local : chargement de la conf système pour un usage depuis le serveur hébergeant SCENARIchain-server 6.4

 - [-v] : ajouter -v ou --verbose [level] pour rendre l'exécutable plus bavard.
   Valeurs de level possibles :
   -v debug : tous les logs de niveau debug
   -v info : tous les logs de niveau info (une ligne de log par appel réussi)
   -v warning : tous les logs de niveau warning
   -v error : tous les logs de niveau erreur (valeur par défaut). Les logs d'erreur sont également publiées sur le flux stderr.
   -v none : désactive les logs d'erreur sur la sortie standard (les erreurs restent publiées sur le flux stderr).
```

Utiliser l'aide intégrée (--help) pour consulter la liste des commandes disponibles.

```shell
# Affichage de l'aide
scchainserver_6_4 --help

# Enregistrer la configuration dans un fichier pour éditer URLs, user ou mot de passe
scchainserver_6_4 print_conf > conf.json

# Ping avec verbosité `debug` pour tester sa configuration
scchainserver_6_4 ping -c conf.json -v debug
```

## Exemples de scripts pour de gestion des backups
**Se référer à la [documentation en ligne](https://doc.scenari.software/SCENARIchain-server@6.4/linux) pour plus de détails sur les backups**

Pour créer une copie des données à backuper
```shell
scchainserver_6_4 backup_pre -c conf.json
# scripter ici la sauvegarde des données
scchainserver_6_4 backup_post -c conf.json
```

Pour un backup du répertoire de données sans créer de copie
```shell
scchainserver_6_4 backupinplace_pre -c conf.json
# scripter ici la sauvegarde des données
scchainserver_6_4 backupinplace_post -c conf.json
```

Scripter ses backups en Python
```python
import scchainserver_6_4.portal

portal = scchainserver_6_4.portal.new_portal(overridden_conf_file="conf.json")
portal.backup_pre() # ou portal.backupinplace_pre()
# Scripter ici la sauvegarde des données
portal.backup_post() # ou portal.backupinplace_pre()
```

## Utiliser ce package avec scenaripy_api

Vous devez installer `scenaripy_api` au préalable :
```shell
pip install scenaripy_api
```

Quelle que soit la version de votre serveur, il est recomandé d'utiliser **la dernière version** de `scenaripy_api`.

Exemple d'utilisation de l'API :
```python
import scenaripy_api
import scchainserver_6_4.portal

# Création de l'objet portal
portal = scchainserver_6_4.portal.new_portal(overridden_conf_file="conf.json")

# Appel d'une méthode de l'API
scenaripy_api.create_or_update_user(portal, account="mon-compte-user", first_name="Prénom", last_name="Nom", roles=["main:reader"], other_props={"password" : "Mon-Password"})
```
Pour plus d'information, se référer à la [documentation de l'API](https://doc.scenari.software/SCENARIbuilder/apipython).
