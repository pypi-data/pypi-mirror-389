from typing import Any
from ..common.svc import Svc
from ..common.utils import json


class AdminServer(Svc):
    def list_traces(self) -> Any:
        return json(self._s.get(self._url, params={"cdaction": "ListTraces"}))
