from ..common.svc import Svc
from ..common.utils import check_status, text


class AdminOdb(Svc):
    def info(self) -> str:
        qs = {"cdaction": "Info"}
        return text(self._s.get(self._url, params=qs))

    def check_storage(self):
        resp = self._s.get(self._url, params={"cdaction": "CheckStorage"})
        check_status(resp, 200)

    def check_auto(self):
        resp = self._s.get(self._url, params={"cdaction": "CheckAuto"})
        check_status(resp, 200)

    def backup_db(self):
        resp = self._s.put(self._url, params={"cdaction": "BackupDb"})
        check_status(resp, 200)

    def end_backup(self):
        resp = self._s.put(self._url, params={"cdaction": "EndBackup"})
        check_status(resp, 200)

    def rebuild(self):
        resp = self._s.put(self._url, params={"cdaction": "Rebuild"})
        check_status(resp, 200)

    def compress_db(self):
        resp = self._s.put(self._url, params={"cdaction": "CompressDb"})
        check_status(resp, 200)
