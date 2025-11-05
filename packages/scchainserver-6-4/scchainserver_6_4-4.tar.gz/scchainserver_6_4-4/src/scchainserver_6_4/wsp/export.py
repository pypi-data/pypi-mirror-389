from time import sleep
from typing import Optional, List

from ..api.item import JSendProps
from ..common.svc import Svc
from ..common.utils import StrEnum, check_status


class EScope(StrEnum):
	node = "node"
	net = "net"


class EFormat(StrEnum):
	jar = "jar"
	zip = "zip"
	stream = "stream"


class EMode(StrEnum):
	wspTree = "wspTree"
	flat = "flat"
	rootAndRes = "rootAndRes"


class ELink(StrEnum):
	absolute = "absolute",
	relative = "relative"


class Export(Svc):
	def send_to(self, wsp_code: str, ref_uris: List[str], send_props: JSendProps, scope: EScope = EScope.net, link_filter: Optional[str] = None, mode: EMode = EMode.wspTree,
	            content_format: EFormat = EFormat.jar, link: ELink = ELink.absolute, include_wsp_metas: bool = True, include_wsp_origin: bool = True,
	            forced_ref_uri_origin: Optional[str] = None) -> int:
		"""
		Envoie d'un scar sur une destination.
		Voir la fonction du send_to_depot pour un export direct
		"""
		qs = {
			"cdaction": "SendTo",
			"param": wsp_code,
			"refUris": "\t".join(ref_uris),
			"scope": scope,
			"mode": mode,
			"format": content_format,
			"link": link,
			"includeWspMeta": include_wsp_metas,
			"includeWspOrigin": include_wsp_origin
		}
		if link_filter is not None:
			qs["linkFilter"] = link_filter
		if forced_ref_uri_origin is not None:
			qs["forcedRefUriOrigin"] = forced_ref_uri_origin
		resp = self._s.put(self._url, params=qs, json=send_props)
		check_status(resp, 200, 204)
		return resp.status_code

	def send_to_depot(self, wsp_code: str, ref_uri: str, depot, metas: dict[str, str]):
		"""
		Paramètre depot non typé en raison des contraintes d'init cycliques de pythons. Il s'agit bien d'un objet Depot attendu
		:param wsp_code:
		:param ref_uri:
		:param depot:
		:param metas:
		:return:
		"""
		session_id = depot.cid.create_session_only(props={"processing": metas["processing"]})
		send_props = {
			"url": f"{depot._url}/public/u/cid?cdaction=RequestSession&createMetas=true&scCidSessId={session_id}",
			"addQSParams": metas
		}
		self.send_to(wsp_code=wsp_code, ref_uris=[ref_uri], send_props=send_props)
		status = depot.cid.request_session(session_id, return_props=["scCidSessStatus", "scCidSessId", "scCidSessDetails"]).json()
		while status["scCidSessStatus"] not in ["failed", "rollbacked", "commited"]:
			sleep(1)
			status = depot.cid.request_session(session_id, return_props=["scCidSessStatus", "scCidSessId", "scCidSessDetails"]).json()
		if status["scCidSessStatus"] != "commited":
			raise RuntimeError(f"Error while sending scar from item {ref_uri}\nstatus: {status['scCidSessStatus']}\n{status['scCidSessDetails']}")

	def export(self, wsp_code: str, ref_uris: List[str], scope: EScope = EScope.node, link_filter: Optional[str] = None, mode: EMode = EMode.wspTree, format: EFormat = EFormat.jar,
	           link: ELink = ELink.absolute, include_wsp_metas: bool = True, include_wsp_origin: bool = True, forced_ref_uri_origin: Optional[str] = None) -> bytes:
		qs = {
			"cdaction": "Export",
			"param": wsp_code,
			"refUris": "\t".join(ref_uris),
			"scope": scope,
			"mode": mode,
			"format": format,
			"link": link,
			"includeWspMeta": include_wsp_metas,
			"includeWspOrigin": include_wsp_origin
		}
		if link_filter is not None:
			qs["linkFilter"] = link_filter
		if forced_ref_uri_origin is not None:
			qs["forcedRefUriOrigin"] = forced_ref_uri_origin

		resp = self._s.put(self._url, params=qs)
		check_status(resp, 200)
		return resp.content
