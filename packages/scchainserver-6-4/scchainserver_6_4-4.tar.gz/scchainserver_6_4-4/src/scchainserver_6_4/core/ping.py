from ..common.svc import Svc
from ..common.utils import check_status


class Ping(Svc):
    def ping(self):
        resp = self._s.get(self._url, params={"cdaction": "Ping"})
        check_status(resp, 200)
