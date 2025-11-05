from typing import Optional, TypedDict, List, Any
import json as json_ser

from ..api.item import EDrvState, EDrfState, ESrcField
from ..common.svc import Svc
from ..common.utils import StrEnum, IntEnum, serialize_cdm, json, check_status, text


class ESrcRights(IntEnum):
    none = 0
    read = 1
    listChildren = 2
    write = 4
    remove = 8
    removeChildren = 16
    createFile = 32
    createFolder = 64
    createChildren = 128
    move = 256


class ESrcSt(IntEnum):
    none = -1
    conflict = -2
    file = 1
    folder = 2


class JSubItem(TypedDict):
    id: str
    ti: Optional[str]
    mo: Optional[str]
    subItems: Optional[List[dict[str, Any]]]  # Self - on évite la dépendance à typing-extension


class JSrcIdent(TypedDict):
    srcUri: Optional[str]
    srcId: Optional[str]
    itSubItem: Optional[JSubItem]


class EItStatus(IntEnum):
    null = -1
    conflict = -2
    unknown = -99
    ok = 1
    warnings = 2
    errors = 3


class EItResp(IntEnum):
    undefined = -1
    ok = 1
    errors = 3


class JInvolvedUser(TypedDict):
    usr: str
    resp: List[str]


class EActStage(StrEnum):
    pending = "pending"
    forthcoming = "forthcoming"
    completed = "completed"


class JActTouchedContent(TypedDict):
    srcId: str


class JSrcFields(JSrcIdent):
    # com.scenari.src.feature.fields.SrcFeatureFields
    srcNm: Optional[str]
    srcSt: Optional[ESrcSt]
    srcDt: Optional[int]
    srcStamp: Optional[str]
    srcTreeDt: Optional[int]
    srcSi: Optional[int]
    srcTy: Optional[str]  # ContentType
    srcRi: Optional[ESrcRights]
    srcRoles: Optional[List[str]]
    srcUser: Optional[str]
    srcLiveUri: Optional[str]
    srcTrashed: Optional[bool]
    metaComment: Optional[str]
    metaFlag: Optional[int]
    # com.scenari.src.feature.drv.SrcFeatureDrv
    drvState: Optional[EDrvState]
    drvAxisDefCo: Optional[str]
    # com.scenari.src.feature.drf.SrcFeatureDrf
    drfState: Optional[EDrfState]
    # eu.scenari.wsp.item.IItemDataKeys
    itTi: Optional[str]
    itSt: Optional[EItStatus]  # @see eu.scenari.wsp.item.IItemDef
    itSgn: Optional[str]
    itModel: Optional[str]
    itFullUriInOwnerWsp: Optional[str]
    itSubItems: Optional[List[JSubItem]]
    """propriétés DES subItems ancêtres DU subItem pointé"""
    itSubItemAnc: List[JSubItem]
    # com.scenari.src.feature.responsibility.SrcFeatureResponsibility
    rspUsrs: Optional[List[JInvolvedUser]]
    rspSt: Optional[EItResp]
    # com.scenari.src.feature.tasks.SrcFeatureTasks
    tkPending: Optional[bool]
    tkPendingCount: Optional[int]
    tkForthcoming: Optional[bool]
    tkForthcomingCount: Optional[int]
    # com.scenari.src.act.IAct
    actStage: Optional[EActStage]
    actTi: Optional[str]
    actCts: Optional[List[JActTouchedContent]]
    # com.scenari.src.feature.lifecycle.SrcFeatureLifeCycle
    lcSt: Optional[str]
    lcDt: Optional[int]
    lcBy: Optional[str]
    """true si une transition est en cours"""
    lcTrP: Optional[bool]
    # com.scenari.src.feature.tasks.ISrcTask
    tkDeadline: Optional[int]
    tkCompletedDt: Optional[int]
    tkCompletedBy: Optional[str]
    # eu.scenari.wsp.provider.IReposSrcNode
    wspOwner: Optional[str]


class JRolesMap(TypedDict):
    allowedRoles: Optional[list[str]]
    deniedRoles: Optional[list[str]]


class WspSrc(Svc):
    def get_src(self, wsp_code: str, ref_uri: str) -> str:
        resp = self._s.get(self._url, params={"cdaction": "GetSrc", "format": "stream", "param": wsp_code, "refUri": ref_uri, "srcTrashed": "false"})
        check_status(resp, 200)
        return text(resp)

    def get_src_bytes(self, wsp_code: str, ref_uri: str) -> bytes:
        resp = self._s.get(self._url, params={"cdaction": "GetSrc", "format": "stream", "param": wsp_code, "refUri": ref_uri, "srcTrashed": "false"})
        check_status(resp, 200)
        return resp.content

    def get_src_fields(self, wsp_code: str, ref_uri: str, fields:list[ESrcField], depth:int =1) -> dict[str, any]:
        return json(self._s.get(self._url, params={"cdaction": "GetSrc", "format": "JSON", "param": wsp_code, "refUri": ref_uri, "fields": "*".join(fields), "depth": depth}))

    def put_src(self, wsp_code: str, ref_uri: str, data: str | bytes):
        encoded = data if type(data) is bytes else data.encode(encoding='utf-8')
        resp = self._s.put(self._url, params={"cdaction": "PutSrc", "param": wsp_code, "refUri": ref_uri}, data=encoded)
        check_status(resp, 200)

    def set_specified_roles(self, wsp_code: str, users_role_map: dict[str, JRolesMap], ref_uri: str = "") -> dict[str, JRolesMap]:
        return json(self._s.post(self._url, params={"cdaction": "SetSpecifiedRoles", "param": wsp_code, "refUri": ref_uri, "options": serialize_cdm(users_role_map)}))

    def update_cid_end_points(self, wsp_code: str, cid_end_points: Any, ref_uri: str):
        data = {"options": json_ser.dumps(cid_end_points)}
        return check_status(self._s.post(self._url, params={"cdaction": "UpdateCidEndPoints", "param": wsp_code, "refUri": ref_uri, "fields": "cidEndPoints"}, data=data), 200)

    def delete(self, wsp_code: str, ref_uri: str | list[str]):
        data = {}
        if type(ref_uri) is str:
            data["refUri"] = ref_uri
        else:
            data["refUris"] = "/t".join(ref_uri)
        return check_status(self._s.post(self._url, params={"cdaction": "Delete", "param": wsp_code}, data=data), 200)

    def delete(self, wsp_code: str, ref_uri: str | list[str]):
        data = {}
        if type(ref_uri) is str:
            data["refUri"] = ref_uri
        else:
            data["refUris"] = "/t".join(ref_uri)
        return check_status(self._s.post(self._url, params={"cdaction": "Delete", "param": wsp_code}, data=data), 200)