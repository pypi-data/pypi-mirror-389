import json
from time import sleep
from typing import Optional, TypedDict, List, Any

from ..api.item import JSendProps
from ..common.svc import Svc
from ..common.utils import serialize_cdm, StrEnum, json, check_status


class EGenStatus(StrEnum):
	working = "working"
	ok = "ok"
	null = "null"
	failed = "failed"
	warning = "warning"


class JGenSkin(TypedDict):
	code: str
	title: str
	hasIllus: Optional[bool]


class JGenInfo(TypedDict):
	codeGenStack: str
	status: EGenStatus
	reason: Optional[str]
	title: Optional[str]
	skin: Optional[str]
	storedProps: dict[str, str]
	lastGen: Optional[int]
	skins: Optional[List[JGenSkin]]
	uriPub: Optional[str]
	uriTraces: Optional[str]
	mimeDownload: Optional[str]
	extrasInfos: Optional[dict[str, str]]
	"""on desktop"""
	localPathPub: Optional[str]


class WspGen(Svc):
	def generate(self, wsp_code: str, ref_uri: str, code_gen_stack: str, props: Optional[dict[str, Any]] = None):
		qs = {"cdaction": "Generate", "format": "none", "param": wsp_code, "refUri": ref_uri, "codeGenStack": code_gen_stack}
		if props is None:
			resp = self._s.put(self._url, params=qs)
		else:
			resp = self._s.post(self._url, params=qs, data={"genProps": serialize_cdm(props)})
		check_status(resp, 204)

	def get_gen_info(self, wsp_code: str, ref_uri: str, code_gen_stack: str, add_extra_infos: Optional[dict[str, str]] = None) -> JGenInfo:
		qs = {"cdaction": "GetGenInfo", "format": "json", "param": wsp_code, "refUri": ref_uri, "codeGenStack": code_gen_stack}
		if add_extra_infos is not None:
			qs["addExtraInfos"] = serialize_cdm(add_extra_infos)
		return json(self._s.get(self._url, params=qs))

	def wait_for_generation(self, wsp_code: str, ref_uri: str, code_gen_stack) -> JGenInfo:
		info: JGenInfo = self.get_gen_info(wsp_code, ref_uri, code_gen_stack)
		while info["status"] == EGenStatus.working.value:
			sleep(1)
			info = self.get_gen_info(wsp_code, ref_uri, code_gen_stack)
		return info

	def download(self, wsp_code: str, ref_uri: str, code_gen_stack: str, custom_full_uri_dest: Optional[str] = None) -> bytes:
		qs = {"cdaction": "Download", "param": wsp_code, "refUri": ref_uri, "codeGenStack": code_gen_stack}

		if custom_full_uri_dest is not None:
			qs["customFullUriDest"] = custom_full_uri_dest
		resp = self._s.get(self._url, params=qs)
		check_status(resp, 200)
		return resp.content

	def send_gen_to(self, wsp_code: str, ref_uri: str, code_gen_stack: str, param_props: JSendProps) -> int:
		return self._s.put(self._url, params={"cdaction": "SendGenTo", "param": wsp_code, "refUri": ref_uri, "codeGenStack": code_gen_stack}, json=param_props).status_code
