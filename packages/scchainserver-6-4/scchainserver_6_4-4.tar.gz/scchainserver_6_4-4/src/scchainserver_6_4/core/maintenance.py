from typing import Optional, TypedDict

from ..common.svc import Svc
from ..common.utils import json, check_status


class JMaintenanceMsg(TypedDict):
	msg: str


class Maintenance(Svc):
	def get_maintenance_mode(self) -> Optional[JMaintenanceMsg]:
		resp = self._s.get(self._url, params={"cdaction": "GetMaintenanceMode"})
		check_status(resp, 200, 204)
		return None if resp.status_code == 204 else json(resp)

	def set_maintenance_mode(self, message:Optional[str] = None) -> Optional[JMaintenanceMsg]:
		resp = self._s.put(self._url, params={"cdaction": "SetMaintenanceMode", "param": message})
		check_status(resp, 200, 204)
		return None if resp.status_code == 204 else json(resp)
