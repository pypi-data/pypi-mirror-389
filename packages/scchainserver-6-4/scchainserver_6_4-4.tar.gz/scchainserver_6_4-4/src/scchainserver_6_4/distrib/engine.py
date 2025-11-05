from typing import Any, TypedDict
from ..common.svc import Svc
from ..common.utils import json, check_status
from ..core.adminuser import JUser


class JParticipant(TypedDict):
    kind: str
    label: str
    projectId: str
    comps: list[Any]


class JActor(TypedDict):
    kind: str
    label: str
    projectId: str
    roomId: str
    comps: list[Any]


class JProject(TypedDict):
    iri: str
    configParams: dict[str, str]
    comps: list[Any]


class JDistribSessionInfo(TypedDict):
    user: JUser
    participants: dict[str, JParticipant]
    actors: dict[str, JActor]
    projects: dict[str, JProject]


class DistribEngine(Svc):
    def get_session_info(self) -> JDistribSessionInfo:
        return json(self._s.get(self._url, params={"cdaction": "GetSessionInfo"}))

    def logout(self):
        return check_status(self._s.put(self._url, params={"cdaction": "Logout"}), 200)
