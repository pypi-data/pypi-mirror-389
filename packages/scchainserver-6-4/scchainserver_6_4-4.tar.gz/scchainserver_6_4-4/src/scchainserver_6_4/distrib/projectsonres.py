from typing import TypedDict, Optional, Any

from ..common.svc import Svc
from ..common.utils import json, serialize_cdm


class JRawProjectOnRes(TypedDict):
	# Raw projects -> export direct DB. On ne passe pas par les APIs

	project_id: str  # Attention. DB ID
	iri: str
	modelversion: int
	start_dt: int
	end_dt: int
	state: str
	state: str
	configstamp: int
	res: str


class ProjectsOnResMgr(Svc):
	def list(self, path: Optional[str] = None) -> list[JRawProjectOnRes]:
		return json(self._s.get(self._url, params={"cdaction": "List", "param": path}))

	def create(self, builder_code: str, props: Optional[dict[str, Any]]) -> JRawProjectOnRes:
		return json(self._s.put(self._url, params={"cdaction": "Create", "param": builder_code, "props": serialize_cdm(props)}))

	def delete(self, project_id: str) -> bool:
		return json(self._s.put(self._url, params={"cdaction": "Create", "param": project_id}))["deleted"]
