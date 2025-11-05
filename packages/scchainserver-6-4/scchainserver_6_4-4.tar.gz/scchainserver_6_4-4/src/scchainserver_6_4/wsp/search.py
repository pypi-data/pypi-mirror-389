from typing import Any, TypedDict, List

from ..api.search import Request, EResultType
from ..common.svc import Svc
from ..api.item import ESrcField
from ..common.utils import json


class JResuls(TypedDict):
    columns: List[ESrcField]
    results: List[List[Any]]


class Search(Svc):
    def raw_search(self, wsp_code: str, request: str) -> JResuls | int:
        return json(self._s.get(self._url, params={"param": wsp_code, "request": request}))

    def search(self, wsp_code: str, request: Request) -> JResuls:
        return self.raw_search(wsp_code, request.serialize(EResultType.entries))

    def count(self, wsp_code: str, request: Request) -> int:
        return self.raw_search(wsp_code, request.serialize(EResultType.count))
