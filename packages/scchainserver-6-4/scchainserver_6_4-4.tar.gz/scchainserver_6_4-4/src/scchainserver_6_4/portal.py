# -*- coding: UTF-8 -*-
import json
import logging
import os
import sys
import textwrap
from io import StringIO
from pathlib import Path
from typing import Optional, TypedDict, Any

from .appsaas.admininst import JInstInfo, ESaasStatus
from .appsaas.dptresinstmgr import JEditSessionInfo, EEditSessionStatus
from .appsaas.instsclustermgr import JReloadClustersResult, JClusterInfo, JClusterSummary
from .portlets import Chain, Depot, Saas, Distrib, JSaasOpt, JDistribOpt, JDepotOpt, JChainOpt, JPortletConf, EPortletName

import requests


def _has_arg(arg: str, argv: list[Any]) -> bool:
    if arg not in argv:
        return False
    return True


def _has_args(*args: str, argv: list[Any]) -> bool:
    for arg in args:
        if _has_arg(arg, argv):
            return True
    return False


def _read_arg(arg: str, argv: list[Any]) -> Optional[str]:
    if arg not in argv:
        return None
    pos = argv.index(arg)
    if pos == len(argv) - 1:
        return None
    else:
        return argv[pos+1]


def _read_args(*args: str, argv: list[Any]) -> Optional[str]:
    for arg in args:
        val = _read_arg(arg, argv)
        if val is not None:
            return val
    return None


class JPortalConf(TypedDict):
    user: Optional[str]
    password: Optional[str]
    portlets: dict[str, JPortletConf]


class ScPortal:
    """ Classe représentant un serveur Scenari. Les objets ScPortal sont instanciés par la méthode scenaripy_lib.portal.new_portal.
    C'est cet objet une fois correctement instancié qui est à passer en premier argument de chaque fonction de scenaripy_api.

    Les objets ScPortal supportent également toutes les commandes de l'application d'administration pour développer des scripts d'administration en Python.
    Pour un usage en ligne de commande, préfixer le nom des paramètres par `--` (`days_to_keep=30` dans un appel de fonction python devient `--days_to_keep 30` dans un appel en ligne de commande). En ligne de commande, les paramètres booléens ne prennent pas de valeur (`strict=True` en python devient `--strict` en ligne de commande et `strict=False` est toujours la valeur par défaut et ne nécessite donc pas d'être précisé en python ou ligne de commande).
    """
    def __init__(self, user: str, pw: str, save_conf: any = None):
        self._s: requests.Session = requests.Session()  # Session interaction avec le portal
        self._s.auth = (user, pw)
        self._portlets: dict[str, Portlet] = {}
        self._saved_conf = save_conf

    def help(self, stream: StringIO = sys.stdout):
        """Imprime la page d'aide dans le flux stream.
        :param stream: Flux sur lequel écrire la doc. sys.stdout par défaut."""
        doc = f"""Cet exécutable permet d'interagir avec un serveur SCENARI. Il vise à aider les administrateurs système dans la gestion de leurs serveurs.

Usage : {sys.argv[0]} [commande] [paramètres] [conf] [-v]
 - [commande] : Voir la liste des commandes disponibles ci-après.
 - [paramètres] : Certaines commandes acceptent des paramètres. Consulter leur documentation ci-après

 - [conf] : paramètres de la configuration du serveur.
   Valeurs possibles :
   -u [login] ou --user [login] : surcharge du nom de l'utilisateur
   -p [password] ou --password [password] : surcharge du mot de passe 
   -c [./maconf.json] ou --conf [./maconf.json] : surcharge de la conf du serveur
   -l ou --local : chargement de la conf système pour un usage depuis la machine hébergeant le serveur SCENARI

 - [-v] : ajouter -v ou --verbose [level] pour rendre l'exécutable plus bavard.
   Valeurs de level possibles :
   -v debug : tous les logs de niveau debug
   -v info : tous les logs de niveau info (une ligne de log par appel réussi)
   -v warning : tous les logs de niveau warning
   -v error : tous les logs de niveau erreur (valeur par défaut). Les logs d'erreur sont également publiées sur le flux stderr.
   -v none : désactive les logs d'erreur sur la sortie standard (les erreurs restent publiées sur le flux stderr).

Liste des commandes disponibles :
"""
        for line in doc.split("\n"):
            if line == "":
                print(file=stream)
            for sub_line in textwrap.wrap(line.strip(), 100, replace_whitespace=False):
                print(sub_line, file=stream)

        for method in dir(self):
            if not self._allow(method):
                continue

            print(method, file=stream)
            if getattr(self, method).__doc__:
                has_param = False
                for line in getattr(self, method).__doc__.split("\n"):
                    if ":param" in line and "[exclude]" not in line:
                        has_param = True
                    else:
                        for sub_line in textwrap.wrap(line.strip(), 100, replace_whitespace=False):
                            print(sub_line, file=stream)

                if has_param:
                    print(file=stream)
                    print("Paramètre(s) :", file=stream)
                    for line in getattr(self, method).__doc__.split("\n"):
                        if ":param" in line and "[exclude]" not in line:
                            line = f" --{line.strip().split(":param ")[1]}"
                            for sub_line in textwrap.wrap(line, 100, replace_whitespace=False):
                                print(sub_line, file=stream)
            else:
                print("Cette fonction n'est pas documentée.\n", file=stream)
            print(file=stream)
            print(file=stream)

    @staticmethod
    def _allow_print_conf() -> bool:
        return True

    def print_conf(self, full: bool = False, stream: StringIO = sys.stdout):
        """ Cette commande permet d'afficher la configuration publique du serveur (simplifiée avec les URLs uniquement ou complète avec la configuration de chaque portlet). La commande peut être utilisée pour extraire un fichier d'URLs afin de modifier les URLs du serveur visé.

    :param full: Permet d'afficher la configuration complète (Par défaut, la configuration contient uniquement les URLs d'accès aux portlets).
    :param stream: Flux vers lequel écrire la conf [exclude]
"""
        self._allow("print_conf", raise_on_not_allowed=True)
        if full:
            print(json.dumps(self._saved_conf, ensure_ascii=False), file=stream)
        else:
            conf = {"portlets": {}}
            for code in self._saved_conf["portlets"]:
                conf["portlets"][code] = {"url": self._saved_conf["portlets"][code]["url"]}
            print(json.dumps(conf, ensure_ascii=False), file=stream)

    def _allow_backupinplace_pre(self) -> bool:
        for portlet in self._portlets:
            if "backupInPlace" in self[portlet]:
                return True
        return False

    def backupinplace_pre(self, portlet: Optional[str] = None):
        """ Cette commande prépare chaque portlet à un backup rapide de type "snapshot". Les données en RAM sont sérialisées sur disque pour permettre un backup cohérent.
 Après appel de cette commande, le répertoire data du serveur peut être sauvegardé. Attention, le serveur est accessible en lecture seule entre les appels de backupinplace_pre et backupinplace_post.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets du serveur.
"""
        self._allow("backupinplace_pre", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].backupInPlace.start_backup()
            logging.info(f"portlet {portlet} backup in place mode: ready to copy")
        else:
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is not None:
                    # Step 1. Porlet without auth
                    if "backupInPlace" in self[prtlt_cd]:
                        self[prtlt_cd].backupInPlace.start_backup()
                        logging.info(f"portlet {prtlt_cd} backup in place mode: ready to copy")

            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is None:
                    # Step 2. Porlet with auth
                    if "backupInPlace" in self[prtlt_cd]:
                        self[prtlt_cd].backupInPlace.start_backup()
                        logging.info(f"portlet {prtlt_cd} backup in place mode: ready to copy")

    def _allow_backupinplace_post(self) -> bool:
        return self._allow_backupinplace_pre()

    def backupinplace_post(self, strict: bool = False, portlet: Optional[str] = None):
        """ Cette commande est à appeler après un backup du répertoire data de type "snapshot". Elle indique aux différents portlets qu'ils peuvent rouvrir les accès en écriture. La commande se termine par des appels de purge de données obsolètes et de contrôle de cohérence (ces appels peuvent être désactivés en utilisant le paramètre `strict`).

    :param strict: Ajouter ce paramètre pour désactiver les purges de données et contrôles de cohérence en fin d'exécution.
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets du serveur.
"""
        self._allow("backupinplace_post", raise_on_not_allowed=True)
        error = False
        if portlet is not None:
            self[portlet].backupInPlace.end_backup()
            logging.info(f"portlet {portlet} backup in place mode: ended")
            if not strict:
                if "assetsCtrl" in self[portlet]:
                    self.assets_gc(portlet=portlet)
                if "store" in self[portlet]:
                    self.store_gc(portlet=portlet)
                if "adminOdb" in self[portlet]:
                    self.odb_checkauto(portlet=portlet)
        else:
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is None:
                    # Step 1.Porlet with auth
                    try:
                        if "backupInPlace" in self[prtlt_cd]:
                            self[prtlt_cd].backupInPlace.end_backup()
                            logging.info(f"portlet {prtlt_cd} backup in place mode: ended")
                    except Exception as e:
                        logging.error(e)
                        error = True

            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is not None:
                    # Step 2.Porlet without auth
                    try:
                        if "backupInPlace" in self[prtlt_cd]:
                            self[prtlt_cd].backupInPlace.end_backup()
                            logging.info(f"portlet {prtlt_cd} backup in place mode: ended")
                    except Exception as e:
                        logging.error(e)
                        error = True

                if not strict:
                    if "assetsCtrl" in self[prtlt_cd]:
                        self.assets_gc()
                    if "store" in self[prtlt_cd]:
                        self.store_gc()
                    if "adminOdb" in self[prtlt_cd]:
                        self.odb_checkauto()

        if error:
            raise RuntimeError("Error occur during backupinplace_post. Check the logs and check your backup")

    def _allow_backup_pre(self) -> bool:
        for portlet in self._portlets:
            if isinstance(self[portlet], Chain) and "adminOdb" not in self[portlet]:
                return False
            if isinstance(self[portlet], Depot) and "backup" not in self[portlet]:
                return False
        return True

    def backup_pre(self, backupid: str = None, portlet: Optional[str] = None):
        """ Cette commande prépare les données pour réaliser un backup.
        Les fichiers de la db interne sont copiés et les blobs sont verrouillés pour ne plus être supprimés des portlets chain.
        Un ensemble de données cohérent et copié dans un répertoire de backup pour les portlets depot.

    :param backupid: Identifiant à utiliser pour le backup du depot (si le serveur contient un depot uniquement). Si précisé, un précédent backup ayant le même identifiant sera supprimé.
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type chain et depot du serveur.
"""
        self._allow("backup_pre", raise_on_not_allowed=True)
        if portlet is not None:
            if isinstance(self[portlet], Chain) and "adminOdb" in self[portlet]:
                self[portlet].adminOdb.backup_db()
                logging.info(f"portlet {portlet} backup: ready to copy")
            elif isinstance(self[portlet], Depot) and "backup" in self[portlet]:
                if backupid is not None:
                    if self[portlet].backup.get_backup_info(backup_id=backupid) is not None:
                        self[portlet].backup.delete_backup(backup_id=backupid)
                        self[portlet].backup.wait_for_backup_deleted(backup_id=backupid)
                self[portlet].backup.add_backup(backup_id=backupid)
                self[portlet].backup.wait_for_last_backup_available()
                logging.info(f"portlet {portlet} backup: ready to copy")

        else:
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is not None:
                    # Step 1. portlet without auth
                    if isinstance(self[prtlt_cd], Chain) and "adminOdb" in self[prtlt_cd]:
                        self[prtlt_cd].adminOdb.backup_db()
                        logging.info(f"portlet {prtlt_cd} backup: ready to copy")
                    elif isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                        if backupid is not None:
                            if self[prtlt_cd].backup.get_backup_info(backup_id=backupid) is not None:
                                self[prtlt_cd].backup.delete_backup(backup_id=backupid)
                                self[prtlt_cd].backup.wait_for_backup_deleted(backup_id=backupid)
                        self[prtlt_cd].backup.add_backup(backup_id=backupid)
                        self[prtlt_cd].backup.wait_for_last_backup_available()
                        logging.info(f"portlet {prtlt_cd} backup: ready to copy")
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is None:
                    # Step 2. portlet with auth
                    if isinstance(self[prtlt_cd], Chain) and "adminOdb" in self[prtlt_cd]:
                        self[prtlt_cd].adminOdb.backup_db()
                        logging.info(f"portlet {prtlt_cd} backup: ready to copy")
                    elif isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                        if backupid is not None:
                            if self[prtlt_cd].backup.get_backup_info(backup_id=backupid) is not None:
                                self[prtlt_cd].backup.delete_backup(backup_id=backupid)
                                self[prtlt_cd].backup.wait_for_backup_deleted(backup_id=backupid)
                        self[prtlt_cd].backup.add_backup(backup_id=backupid)
                        self[prtlt_cd].backup.wait_for_last_backup_available()
                        logging.info(f"portlet {prtlt_cd} backup: ready to copy")

    def _allow_backup_post(self) -> bool:
        return self._allow_backup_pre()

    def backup_post(self, backupid: str = None, portlet: Optional[str] = None, strict: bool = None):
        """ Cette commande informe les portlets chain qu'il est à nouveau possible de supprimer des blobs du disque. La commande se termine par des appels de purge de données obsolètes et de contrôle de cohérence (ces appels peuvent être désactivés en utilisant le paramètre `strict`).

    :param backupid: Identifiant à utiliser pour le backup du depot (si le serveur contient un depot uniquement). Si précisé, les fichiers temporaires à sauvegarder seront supprimés
    :param strict: Ajouter ce paramètre pour désactiver les purges de données et contrôles de cohérence en fin d'exécution.
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type chain et depot du serveur.
"""
        self._allow("backup_post", raise_on_not_allowed=True)
        error = False
        if portlet is not None:
            if isinstance(self[portlet], Chain) and "adminOdb" in self[portlet]:
                self[portlet].adminOdb.end_backup()
                logging.info(f"portlet {portlet} backup mode: ended")
            elif isinstance(self[portlet], Depot) and "backup" in self[portlet]:
                if backupid is not None:
                    self[portlet].backup.delete_backup(backup_id=backupid)
                logging.info(f"portlet {portlet} backup mode: ended")

            if not strict:
                if "assetsCtrl" in self[portlet]:
                    self.assets_gc(portlet=portlet)
                if "store" in self[portlet]:
                    self.store_gc(portlet=portlet)
                if "adminOdb" in self[portlet]:
                    self.odb_checkauto(portlet=portlet)
        else:
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is None:
                    # Step 1. Portlet with auth
                    try:
                        if isinstance(self[prtlt_cd], Chain) and "adminOdb" in self[prtlt_cd]:
                            self[prtlt_cd].adminOdb.end_backup()
                            logging.info(f"portlet {prtlt_cd} backup mode: ended")
                        elif isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                            if backupid is not None:
                                self[prtlt_cd].backup.delete_backup(backup_id=backupid)
                            logging.info(f"portlet {prtlt_cd} backup mode: ended")
                    except Exception as e:
                        logging.error(e)
                        error = True
            for prtlt_cd in self._portlets:
                if self[prtlt_cd].get_remote_auth_portlet() is not None:
                    # Step 2. Portlet without auth
                    try:
                        if isinstance(self[prtlt_cd], Chain) and "adminOdb" in self[prtlt_cd]:
                            self[prtlt_cd].adminOdb.end_backup()
                            logging.info(f"portlet {prtlt_cd} backup mode: ended")
                        elif isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                            if backupid is not None:
                                self[prtlt_cd].backup.delete_backup(backup_id=backupid)
                            logging.info(f"portlet {prtlt_cd} backup mode: ended")
                    except Exception as e:
                        logging.error(e)
                        error = True

                if not strict:
                    if "assetsCtrl" in self[prtlt_cd]:
                        self.assets_gc()
                    if "store" in self[prtlt_cd]:
                        self.store_gc()
                    if "adminOdb" in self[prtlt_cd]:
                        self.odb_checkauto()

        if error:
            raise RuntimeError("Error occur during backupinplace_post. Check the logs and check your backup")

    def _allow_depot_backup_list(self) -> bool:
        has_depot = False
        for portlet in self._portlets:
            if isinstance(self[portlet], Depot):
                has_depot = True
        return has_depot and self._allow_backup_pre()

    def depot_backup_list(self, portlet: Optional[str] = None):
        """ Liste tous les backups disponibles sur les portlets depot.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
"""
        self._allow("depot_backup_list", raise_on_not_allowed=True)
        if portlet is not None:
            print(json.dumps(self[portlet].backup.list_backups()))
        else:
            for prtlt_cd in self._portlets:
                if isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                    print(f"Backups du portlet {prtlt_cd}: ")
                    print(json.dumps(self[prtlt_cd].backup.list_backups()))

    def _allow_depot_backup_restore(self) -> bool:
        return self._allow_depot_backup_list()

    def depot_backup_restore(self, portlet: Optional[str] = None, backupid: str = "~last"):
        """ Restore le backup d'un depot.

    :param backupid : Identifiant du backup du depot à restorer. Par défaut, le dernier backup disponible est restauré.
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
"""
        self._allow("depot_backup_restore", raise_on_not_allowed=True)
        if backupid is None:
            backupid = "~last"
        if portlet is not None:
            self[portlet].backup.restore_backup(backup_id=backupid)
            logging.info(f"Backup {backupid} restored on portlet {portlet}")
        else:
            for prtlt_cd in self._portlets:
                if isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                    self[prtlt_cd].backup.restore_backup(backup_id=backupid)
                    logging.info(f"Backup {backupid} restored on portlet {prtlt_cd}")
        print("depot restore backup done. Please RESTART THE SERVER NOW")

    def _allow_depot_backup_cleanup(self) -> bool:
        return self._allow_depot_backup_list()

    def depot_backup_cleanup(self, portlet: Optional[str] = None, days_to_keep: Optional[int] = 1):
        """ Supprime les anciens backups du depot (le dernier backup est systématiquement conservé)

    :param days_to_keep: Nombre de jours de conservation du backup (facultatif). Tous les backups plus anciens sont supprimés.
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
    """
        self._allow("depot_backup_cleanup", raise_on_not_allowed=True)
        if days_to_keep is None:
            days = 1
        elif str == type(days_to_keep):
            days = int(days_to_keep)
        else:
            days = days_to_keep
        if portlet is not None:
            self[portlet].backup.cleanup_old_backups(days_to_keep=days)
            logging.info(f"Old backups deleted on portlet {portlet}")
        else:
            for prtlt_cd in self._portlets:
                if isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                    self[prtlt_cd].backup.cleanup_old_backups(days_to_keep=days)
                    logging.info(f"Old backups deleted on portlet {prtlt_cd}")

    def _allow_depot_backup_delete(self) -> bool:
        return self._allow_depot_backup_list()

    def depot_backup_delete(self, portlet: Optional[str] = None, backupid: str = None):
        """ Supprime le backup d'un depot. Le paramètre backupid est obligatoire pour savoir quel backup supprimer.

    :param backupid : L'identifiant du backup du depot à supprimer
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
"""
        self._allow("depot_backup_delete", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].backup.delete_backup(backup_id=backupid)
            logging.info(f"Backup {backupid} deleted on portlet {portlet}")
        else:
            for prtlt_cd in self._portlets:
                if isinstance(self[prtlt_cd], Depot) and "backup" in self[prtlt_cd]:
                    self[prtlt_cd].backup.delete_backup(backup_id=backupid)
                    logging.info(f"Backup {backupid} deleted on portlet {prtlt_cd}")

    @staticmethod
    def _allow_ping() -> bool:
        return True

    def ping(self, portlet: Optional[str] = None):
        """ Effectue une requête de ping vers les portlets du serveur. Cette commande permet de tester l'URL, les logins et mots de passe.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot, distrib) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets du serveur.
"""
        self._allow("ping", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].ping.ping()
            logging.info(f"portlet {portlet} ping: OK")
        else:
            for prtlt_cd in self._portlets:
                self[prtlt_cd].ping.ping()
                logging.info(f"portlet {prtlt_cd} ping: OK")

    def _allow_odb_checkauto(self) -> bool:
        for portlet in self._portlets:
            if "adminOdb" in self[portlet]:
                return True
        return False

    def odb_checkauto(self, portlet: Optional[str] = None):
        """ Lance un test de cohérence de la base de données interne. Cette commande est appelée par les commandes backup_post et backupinplace_post lorsque le paramètre strict n'est pas précisé.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type chain du serveur.
"""
        self._allow("odb_checkauto", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].adminOdb.check_auto()
            logging.info(f"portlet {portlet} db check auto: OK")
        else:
            for prtlt_cd in self._portlets:
                if "adminOdb" in self[prtlt_cd]:
                    self[prtlt_cd].adminOdb.check_auto()
                    logging.info(f"portlet {prtlt_cd} db check auto: OK")

    def _allow_odb_rebuild(self) -> bool:
        return self._allow_odb_checkauto()

    def odb_rebuild(self, portlet: Optional[str] = None):
        """ Lance une reconstruction de la base de données interne.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type chain du serveur.
"""
        self._allow("odb_rebuild", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].adminOdb.rebuild()
            logging.info(f"portlet {portlet} db rebuild: OK")
        else:
            for prtlt_cd in self._portlets:
                if "adminOdb" in self[prtlt_cd]:
                    self[prtlt_cd].adminOdb.rebuild()
                    logging.info(f"portlet {prtlt_cd} db rebuild: OK")

    def _allow_store_gc(self) -> bool:
        for portlet in self._portlets:
            if "store" in self[portlet]:
                return True
        return False

    def store_gc(self, portlet: Optional[str] = None):
        """ Lance le garbage collector d'un store (système de stockage des ressources d'un depot). Cette commande est appelée par les commandes backup_post et backupinplace_post lorsque le paramètre strict n'est pas précisé. Attention, si cette méthode n'est pas appelée, les ressources supprimées d'un depot NE SONT JAMAIS SUPPRIMÉS DU RÉPERTOIRE DATA DU SERVEUR.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
"""
        self._allow("store_gc", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].store.gc()
            logging.info(f"portlet {portlet} store GC: OK")
        else:
            for prtlt_cd in self._portlets:
                if "store" in self[prtlt_cd]:
                    self[prtlt_cd].store.gc()
                    logging.info(f"portlet {prtlt_cd} store GC: OK")

    def _allow_assets_gc(self) -> bool:
        for portlet in self._portlets:
            if "assetsCtrl" in self[portlet]:
                return True
        return False

    def assets_gc(self, portlet: Optional[str] = None):
        """ Lance le garbage collector des assets (stockage des skins et libs js mutualisées). Cette commande est appelée par les commandes backup_post et backupinplace_post lorsque le paramètre strict n'est pas précisé. Attention, si cette méthode n'est pas appelée, les skins ou libs mutualisées obsolètes d'un depot NE SONT JAMAIS SUPPRIMÉS DU RÉPERTOIRE DATA DU SERVEUR.

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depot) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type depot du serveur.
"""
        self._allow("assets_gc", raise_on_not_allowed=True)
        if portlet is not None:
            self[portlet].assetsCtrl.gc()
            logging.info(f"portlet {portlet} assetsCtrl GC: OK")
        else:
            for prtlt_cd in self._portlets:
                if "assetsCtrl" in self[prtlt_cd]:
                    self[prtlt_cd].assetsCtrl.gc()
                    logging.info(f"portlet {prtlt_cd} assetsCtrl GC: OK")

    @staticmethod
    def _allow_actlogs_purge() -> bool:
        return True

    def actlogs_purge(self, days_to_keep: Optional[int] = 365, portlet: Optional[str] = None):
        """ Commande de suppression des actlogs (logs applicatifs, peut contenir des logs d'accès ou des logs d'utilisation de certaines fonctions comme l'écriture dans un depot). Attention, si cette commande n'est jamais appelée, les logs applicatifs NE SONT JAMAIS SUPPRIMÉS DU RÉPERTOIRE DE LOG DU SERVEUR.

    :param days_to_keep: Nombre de jours d'actlogs à conserver (365 par défaut).
    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : chain, depot, distrib) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets du serveur.
"""
        self._allow("actlogs_purge", raise_on_not_allowed=True)
        if days_to_keep is None:
            days = 365
        elif str == type(days_to_keep):
            days = int(days_to_keep)
        else:
            days = days_to_keep
        if portlet is not None:
            self[portlet].universeActLog.purge_old_logs(days)
            logging.info(f"portlet {portlet} PurgeOldLogs: OK")
        else:
            for prtlt_cd in self._portlets:
                self[prtlt_cd].universeActLog.purge_old_logs(days)
                logging.info(f"portlet {prtlt_cd} PurgeOldLogs GC: OK")

    def _allow_strongbox_reset_scaccountpw(self) -> bool:
        usr_mgr_prt: Optional[Portlet] = None
        strongbox_prt: [Portlet] = None
        for prtlt_cd in self._portlets:
            if self._portlets[prtlt_cd].get_remote_auth_portlet() is not None:
                usr_mgr_prt = self._portlets[prtlt_cd]
            if "strongbox" in self._portlets[prtlt_cd]:
                strongbox_prt = self._portlets[prtlt_cd]
        return usr_mgr_prt is not None and strongbox_prt is not None

    def strongbox_reset_scaccountpw(self, account: str, new_password: str, usermgr_portlet: Optional[str] = None, strongbox_portlet: Optional[str] = None,
                                    account_portlet_owner: Optional[str] = None):
        """ Modifie un mot de passe interne au service de gestion des utilisateurs et à la strongbox. Cette méthode n'est utile que si le serveur a été spécifiquement configuré avec des comptes de service dans la strongbox.
    Exemple : `strongbox_reset_scaccountpw --account svc-internal-dpt --new-password [nouveau mot de passe] --account_portlet_owner depot -c conf.json`

    :param account: Nom du compte de service (exemple : svc-internal-dpt)
    :param new_password: nouveau mot de passe
    :param usermgr_portlet: Code du portlet portant le userMgr. Si non spécifié, utilise le premier portlet trouvé ayant un userMgr interne.
    :param strongbox_portlet: Code du portlet portant la strongbox. Si non spécifié, utilise le premier portlet trouvé ayant une stronbox.
    :param account_portlet_owner: Nom du portlet utilisant le compte interne. Si non spécifié, le compte sera associé à la box du portlet portant la strongbox
"""
        self._allow("strongbox_reset_scaccountpw", raise_on_not_allowed=True)
        usr_mgr_prt: Optional[Portlet] = None
        strongbox_prt: [Portlet] = None
        strongbox_prt_code = strongbox_portlet

        if usermgr_portlet is not None:
            usr_mgr_prt = self._portlets[usermgr_portlet]
        if strongbox_portlet is not None:
            strongbox_prt = self._portlets[strongbox_portlet]

        if usermgr_portlet is None or strongbox_portlet is None:
            for prtlt_cd in self._portlets:
                if usermgr_portlet is None and self._portlets[prtlt_cd].get_remote_auth_portlet() is None:
                    usr_mgr_prt = self._portlets[prtlt_cd]
                if strongbox_portlet is None and "strongbox" in self._portlets[prtlt_cd]:
                    strongbox_prt = self._portlets[prtlt_cd]
                    strongbox_prt_code = prtlt_cd

        box: str = "app" if account_portlet_owner is None or account_portlet_owner == strongbox_prt_code else f"{account_portlet_owner}~app"

        if "password" not in strongbox_prt.strongbox.get_data(box, f"account.{account}.password"):
            logging.error("Strongbox entry do not contains password data. Check 'account' and 'account_portlet_owner' param.")
            return
        else:
            usr_mgr_prt.adminUsers.update_user(account, {"password": new_password})
            strongbox_prt.strongbox.set_data(box, f"account.{account}.password", {"account": account, "password": new_password})
            logging.info(f"password of account {account} resetted: OK")

    def _allow_list_clusters(self) -> bool:
        for portlet in self._portlets:
            if "instsClusterMgr" in self._portlets[portlet]:
                return True
        return False

    def list_clusters(self, portlet: Optional[str] = None):
        """ Liste les clusters d'un portlet saas

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : saas) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type saas de clusters du serveur.
        """
        self._allow("list_clusters", raise_on_not_allowed=True)
        if portlet is not None:
            clusters: list[JClusterSummary] = self.saas(portlet).instsClusterMgr.list_clusters()
            out = ""
            for cluster in clusters:
                out += f"{cluster['id']} "
            print(out)

        else:
            for prtlt_cd in self._portlets:
                if "instsClusterMgr" in self._portlets[prtlt_cd]:
                    print(f"portlet {prtlt_cd}")
                    clusters: list[JClusterSummary] = self.saas(portlet).instsClusterMgr.list_clusters()
                    out = ""
                    for cluster in clusters:
                        out += f"{cluster['id']} "
                    print(out)

    def _allow_list_edit_sessions(self) -> bool:
        for prtl_cd in self._portlets:
            if "dptResInstMgr" in self._portlets[prtl_cd]:
                return True
        return False

    def list_edit_sessions(self, portlet: Optional[str] = None):
        """ Liste les EditSession d'un serveur saas

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depotw) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type saas de EditSession du serveur.
        """
        self._allow("list_edit_sessions", raise_on_not_allowed=True)
        if portlet is not None:
            sessions: list[JEditSessionInfo] = self.saas(portlet).dptResInstMgr.list_open_edit_sessions()
            out = ""
            for session in sessions:
                out += f"{session['path']}[{session['sessionId']}] "
            print(out)

        else:
            for prtlt_cd in self._portlets:
                if "dptResInstMgr" in self._portlets[prtlt_cd]:
                    sessions: list[JEditSessionInfo] = self.saas(portlet).dptResInstMgr.list_open_edit_sessions()
                    out = ""
                    for session in sessions:
                        out += f"{session['path']}[{session['sessionId']}] "
                    print(out)

    def _allow_reload_clusters_conf(self) -> bool:
        for portlet in self._portlets:
            if "instsClusterMgr" in self._portlets[portlet]:
                return True
        return False

    def reload_clusters_conf(self, portlet: Optional[str] = None):
        """ Reconstruit l'ensemble des configurations des clusters d'un portlet saas

    :param portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : saas) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type saas de clusters du serveur.
        """
        self._allow("reload_clusters_conf", raise_on_not_allowed=True)
        if portlet is not None:
            info: JReloadClustersResult = self.saas(portlet).instsClusterMgr.reload_all_clusters()
            if info["status"] == "ok":
                logging.info(f"All clusters of portlet {portlet} has been reloaded")
            else:
                logging.error(f"Error on clusters reloading on portlet {portlet}:\n{info['errors']}")

        else:
            for prtlt_cd in self._portlets:
                if "instsClusterMgr" in self._portlets[prtlt_cd]:
                    info: JReloadClustersResult = self.saas(prtlt_cd).instsClusterMgr.reload_all_clusters()
                    if info["status"] == "ok":
                        logging.info(f"All clusters of portlet {prtlt_cd} has been reloaded")
                    else:
                        logging.error(f"Error on clusters reloading on portlet {prtlt_cd}:\n{info['errors']}")

    def _allow_cmd_subportal(self) -> bool:
        for portlet in self._portlets:
            if "instsClusterMgr" in self._portlets[portlet]:
                return True
            if "dptResInstMgr" in self._portlets[portlet]:
                return True
        return False

    def cmd_subportal(self, portal_id: Optional[str] = None, saas_portlet: Optional[str] = None, sub_cmd: Optional[list[Any]] = None):
        """ Appel d'une commande sur une ou sur toutes les instances du saas.

    :param portal_id: Id d'un cluster ou path d'une session d'édition pour appeler la commande sur une unique instance. Si non spécifié, la commande est appelée sur tous les clusters ou EditSessions.
    :param saas_portlet: Utiliser ce paramètre (optionnel) avec le nom d'un portlet (ex : depotw, saas) pour limiter l'appel à un unique portlet du serveur. Par défaut, la commande est lancée sur tous les portlets de type saas du serveur.
    :param sub_cmd: La commande et ses paramètres à exécuter sur les instances du saas. Ce paramètre est à préciser en dernier.

    Exemple : `cmd_subportal --portal_id [clust.id] ping -u system -p system`
        """
        self._allow("cmd_subportal", raise_on_not_allowed=True)
        if sub_cmd is None:
            sub_cmd = []
            skip = False
            for arg in sys.argv[2:]:

                if arg in ["--portal_id", "--saas_portlet", "-u", "--user", "-p", "--password", "-c", "--conf", "l", "--local", "-v", "--verbose", "-h", "--help"]:
                    skip = True
                    continue
                if skip:
                    skip = False
                    continue
                sub_cmd.append(arg)

        if len(sub_cmd) < 1:
            logging.error("No subcommands to apply to subportal found")

        if saas_portlet is not None:
            self._cmd_subportal_on_portlet(portlet=saas_portlet, portal_id=portal_id, sub_cmd=sub_cmd)

        else:
            for prtlt_cd in self._portlets:
                if "instsClusterMgr" in self._portlets[prtlt_cd] or "dptResInstMgr" in self._portlets[prtlt_cd]:
                    self._cmd_subportal_on_portlet(portlet=prtlt_cd, portal_id=portal_id, sub_cmd=sub_cmd)

    def _cmd_subportal_on_portlet(self, portlet: str, portal_id: Optional[str] = None, sub_cmd: Optional[list[Any]] = None):
        saas: Saas = self.saas(portlet)
        if saas is None:
            logging.error(f"Unable to find a saas portlet with code '{portlet}'")
            return

        if saas.dptResInstMgr is not None:
            if portal_id is not None:
                self._call_sub_cmd_on_session(portlet=portlet, path=portal_id, sub_cmd=sub_cmd)
            else:
                for session in saas.dptResInstMgr.list_open_edit_sessions():
                    self._call_sub_cmd_on_session(portlet=portlet, path=session["path"], sub_cmd=sub_cmd)

        elif saas.instsClusterMgr is not None:
            if portal_id is not None:
                self._call_sub_cmd_on_cluster(portlet=portlet, cluster_id=portal_id, sub_cmd=sub_cmd)
            else:
                for cluster in saas.instsClusterMgr.list_clusters():
                    self._call_sub_cmd_on_cluster(portlet=portlet, cluster_id=cluster["id"], sub_cmd=sub_cmd)

        else:
            logging.error(f"Saas portlet with code '{portlet}' has no 'dptResInstMgr' or 'instsClusterMgr' services. Unable to call sub command on sub portal")
            return

    def _call_sub_cmd_on_session(self, portlet: str, path: str, sub_cmd: list[Any]):
        saas: Saas = self.saas(portlet)
        inst_id = saas.dptResInstMgr.get_edit_session_infos(path=path)["sessionId"]
        inst_info: JInstInfo = saas.adminInst.get_inst_infos(inst_id=inst_id)
        session_info: JEditSessionInfo = saas.dptResInstMgr.open_and_wait_edit_session(path)

        if session_info["status"] != EEditSessionStatus.passed:
            logging.error(f"Unable to open session '{path}.' Session status: {session_info['status']}")
            return

        if inst_info["instStatus"] == ESaasStatus.failed:
            logging.error(f"Unable to call inst '{inst_id}.' Saas inst is in status 'failed'")
            return

        sub_portal: ScPortal = saas.get_portal(user=self._s.auth[0], pw=self._s.auth[1], portal_vars={"session.id": inst_id})
        sub_portal.call(argv=sub_cmd)
        logging.info(f"sub cmd {sub_cmd[0]} called on session '{path}' (corresponding to session.id '{inst_id}')")

        if inst_info["instStatus"] == ESaasStatus.stopped or inst_info["instStatus"] == ESaasStatus.stopping:
            saas.adminInst.stop_inst(inst_id=inst_id)

    def _call_sub_cmd_on_cluster(self, portlet: str, cluster_id: str, sub_cmd: list[Any]):
        saas: Saas = self.saas(portlet)

        cluster_info: JClusterInfo = saas.instsClusterMgr.get_cluster_infos(cluster_id=cluster_id)
        insts_info: dict[str, JInstInfo] = {}
        for inst in cluster_info["insts"]:
            insts_info[inst] = saas.adminInst.get_inst_infos(inst)
            if insts_info[inst]["instStatus"] == ESaasStatus.failed:
                logging.error(f"Unable to call inst '{inst} in cluster {cluster_id}'. Saas inst is in status 'failed'")
                return

        sub_portal: ScPortal = saas.get_portal(user=self._s.auth[0], pw=self._s.auth[1], portal_vars=saas.instsClusterMgr.get_cluster_props(cluster_id=cluster_id))
        sub_portal.call(argv=sub_cmd)
        logging.info(f"sub cmd {sub_cmd[0]} called on cluster '{cluster_id}'")

        for inst in insts_info:
            if insts_info[inst]["instStatus"] == ESaasStatus.stopped or insts_info[inst]["instStatus"] == ESaasStatus.stopping:
                saas.adminInst.stop_inst(inst_id=inst)

    def call(self, argv: Optional[list[str]] = None):
        if argv is None:
            argv = sys.argv[1:]
        if len(argv) > 0:
            cmd = argv[0]
            if self._allow(cmd):
                try:
                    method = getattr(self, cmd)
                    args = {}
                    for arg in method.__annotations__:
                        if method.__annotations__[arg] == bool:
                            args[arg] = _has_arg(f"--{arg}", argv)
                        else:
                            args[arg] = _read_arg(f"--{arg}", argv)
                    method(**args)
                    return
                except Exception as ex:
                    if hasattr(ex, 'message'):
                        logging.error(ex.message)
                    else:
                        logging.error(ex)
                    raise RuntimeError(f"Unable to execute command {cmd}. Try --help to get help.")
        raise RuntimeError("Unknown command. Try --help to get help.")

    def _allow(self, method_name: str, raise_on_not_allowed: bool = False):
        allowed = f"_allow_{method_name}" in dir(self) and getattr(self, f"_allow_{method_name}")()
        if allowed is False and raise_on_not_allowed is True:
            raise RuntimeError(f"The method {method_name} is not available on the server. Try method help() to get help.")
        return allowed

    def add_chain_portlet(self, url: str, code: str = "chain", opt: Optional[JChainOpt] = None, exec_frame: str = "script"):
        if exec_frame is None:
            exec_frame = "script"
        if opt is None:
            opt = {}
        self._portlets[code] = Chain(url, self._s, opt, exec_frame)

    def add_depot_portlet(self, url: str, code: str = "depot", opt: Optional[JDepotOpt] = None, exec_frame: str = "script"):
        if exec_frame is None:
            exec_frame = "script"
        if opt is None:
            opt = {}
        self._portlets[code] = Depot(url, self._s, opt, exec_frame)

    def add_saas_portlet(self, url: str, code: str = "depotw", opt: Optional[JSaasOpt] = None, exec_frame: str = "script"):
        if exec_frame is None:
            exec_frame = "script"
        if opt is None:
            opt = {}
        self._portlets[code] = Saas(url, self._s, opt, exec_frame)

    def add_distrib_portlet(self, url: str, code: str = "distrib", opt: Optional[JDistribOpt] = None, exec_frame: str = "script"):
        if exec_frame is None:
            exec_frame = "script"
        if opt is None:
            opt = {}
        self._portlets[code] = Distrib(url, self._s, opt, exec_frame)

    def __getitem__(self, item):
        return self._portlets[item]

    def __contains__(self, item):
        return item in self._portlets

    def chain(self, code: Optional[str] = None) -> Optional[Chain]:
        if code is not None and type(self._portlets[code]) is Chain:
            return self._portlets[code]
        else:
            for prtlt_cd in self._portlets:
                if type(self._portlets[prtlt_cd]) is Chain:
                    return self._portlets[prtlt_cd]
        return None

    def depot(self, code: Optional[str] = None) -> Optional[Depot]:
        if code is not None and type(self._portlets[code]) is Depot:
            return self._portlets[code]
        else:
            for prtlt_cd in self._portlets:
                if type(self._portlets[prtlt_cd]) is Depot:
                    return self._portlets[prtlt_cd]
        return None

    def saas(self, code: Optional[str] = None) -> Optional[Saas]:
        if code is not None and type(self._portlets[code]) is Saas:
            return self._portlets[code]
        else:
            for prtlt_cd in self._portlets:
                if type(self._portlets[prtlt_cd]) is Saas:
                    return self._portlets[prtlt_cd]
        return None

    def distrib(self, code: Optional[str] = None) -> Optional[Distrib]:
        if code is not None and type(self._portlets[code]) is Distrib:
            return self._portlets[code]
        else:
            for prtlt_cd in self._portlets:
                if type(self._portlets[prtlt_cd]) is Distrib:
                    return self._portlets[prtlt_cd]
        return None


def new_portal(system_conf: bool = False, overridden_conf_file: Optional[str] = None, override_props: Optional[Any] = None):
    """
    Méthode d'instanciation d'un objet ScPortal. Cette méthode s'appuie sur la conf par défaut du package scenaripy_lib.
    ```python
    # Avec user et mot de passe dans le code Python
    portal = scenaripy_lib.portal.new_portal(override_props={"user": "mon-user", "password": "mon-password"})

    # Avec user, mot de passe et possibilité de surcharger des URLs dans un fichier json
    portal = scenaripy_lib.portal.new_portal(overridden_conf_file="conf.json")

    # En mobilisant les URLs system (http://172.0.0.1:8080...) pour exécution depuis le serveur
    portal = scenaripy_lib.portal.new_portal(system_conf=True, override_props={"user": "mon-user", "password": "mon-password"})

    # En surchargeant d'abord la conf par le fichier overridden_conf_file puis le login et password via override_props
    portal = scenaripy_lib.portal.new_portal(overridden_conf_file="conf.json", override_props={"user": "mon-user", "password": "mon-password"})
    ```

    :param system_conf: Ajouter ce paramètre pour charger la configuration système par défaut (URL locales de type http://127.0.0.1:8080/xxx pour une utilisation sur la même machine que celle où le serveur est installée).
    :param overridden_conf_file: Chemin vers un fichier de surcharges des propriétés par défaut. Ce fichier de conf peut par exemple contenir les champs login, password ou portlets (pour redéfinir uniquement les URLs ou la configuration complète des portlets)
    :param override_props: Propriétés de surcharge de la conf par défaut (et du fichier overridden_conf_file). Permet de surcharger les champs login, password ou portlets (pour redéfinir uniquement les URLs ou la configuration complète des portlets)
    :return: Un objet ScPortal à utiliser avec les méthodes de scenaripy_api ou via ses propres méthodes pour appeler les commandes d'administration.
    """
    conf_file: str = os.path.join(os.path.dirname(__file__), "system_default_conf.json" if system_conf else "public_default_conf.json")
    with open(conf_file, "r") as file:
        conf: JPortalConf = json.load(file)

    login_conf_str: str = os.path.join(os.path.dirname(__file__), "login.json")
    login_conf: Path = Path(login_conf_str)
    if login_conf.is_file():
        with open(login_conf, "r") as file:
            overridden_conf: JPortalConf = json.load(file)
        conf = __override_prop(conf, overridden_conf)

    if overridden_conf_file is not None:
        with open(overridden_conf_file, "r") as file:
            overridden_conf: JPortalConf = json.load(file)
        conf = __override_prop(conf, overridden_conf)

    if override_props is not None:
        conf = __override_prop(conf, override_props)

    user = conf["user"] if "user" in conf else None
    pw = conf["password"] if "password" in conf else None
    portal = ScPortal(user=user, pw=pw, save_conf=conf)

    if "portlets" not in conf:
        logging.error("Error : no portlets found in portal conf.")
        sys.exit(1)

    for code in conf["portlets"]:
        portlet: JPortletConf = conf["portlets"][code]
        execframe = "script" if "execframe" not in portlet else portlet["execframe"]
        if portlet["portlet"] == EPortletName.chain.value:
            portal.add_chain_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
        elif portlet["portlet"] == EPortletName.depot.value:
            portal.add_depot_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
        elif portlet["portlet"] == EPortletName.distrib.value:
            portal.add_distrib_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
        elif portlet["portlet"] == EPortletName.saas.value:
            portal.add_saas_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
        else:
            logging.error(f"unknown portlet {portlet}")
            sys.exit(1)

    return portal


def __override_prop(prop, override):
    if prop is None or type(prop) is not dict:
        prop = {}

    for code in override:
        if type(override[code]) is dict:
            prop[code] = __override_prop({} if code not in prop else prop[code], override[code])
        else:
            prop[code] = override[code]
    return prop


def __main():
    try:
        user = _read_args("-u", "--user", argv=sys.argv)
        pw = _read_args("-p", "--password", argv=sys.argv)
        conf = _read_args("-c", "--conf", argv=sys.argv)
        local = _has_args("-l", "--local", argv=sys.argv)
        verbose = _read_args("-v", "--verbose", argv=sys.argv)
        doc = _has_args("-h", "--help", argv=sys.argv)

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        error_handler = logging.StreamHandler(stream=sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logging.getLogger().setLevel(logging.DEBUG)

        if verbose == "debug":
            error_handler.setLevel(logging.DEBUG)
        elif verbose == "info":
            error_handler.setLevel(logging.INFO)
        elif verbose == "warning":
            error_handler.setLevel(logging.WARNING)
        elif verbose == "error":
            error_handler.setLevel(logging.ERROR)
        elif _has_args("-v", "--verbose", argv=sys.argv):
            error_handler.setLevel(logging.INFO)
        else:
            error_handler.setLevel(logging.ERROR)

        if verbose != "none":
            logging.getLogger().addHandler(error_handler)

        override_conf = {}
        if user is not None:
            override_conf["user"] = user
        if pw is not None:
            override_conf["password"] = pw

        portal = new_portal(system_conf=local, overridden_conf_file=conf, override_props=override_conf)
        if doc:
            portal.help()
        else:
            portal.call()
    except Exception as ex:
        if hasattr(ex, 'message'):
            logging.error(ex.message)
        else:
            logging.error(ex)
        sys.exit(1)


if __name__ == '__main__':
    __main()
