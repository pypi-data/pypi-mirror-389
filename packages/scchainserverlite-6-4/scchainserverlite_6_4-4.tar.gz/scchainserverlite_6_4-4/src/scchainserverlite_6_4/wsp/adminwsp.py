import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Optional, Any, TypedDict, List
from xml.sax.saxutils import escape

from .wspsrc import JSrcFields
from ..common.svc import Svc
from ..common.utils import StrEnum, StrBooleanEnum, serialize_cdm, json, check_status, text


class EBackEnd(StrEnum):
    fs = "fs"
    odb = "odb"


class EWspLoadingStatus(StrEnum):
    notLoaded = "notLoaded",
    ok = "ok",
    failed = "failed",
    loading = "loading",
    failedNoData = "failedNoData",  # wsp déclaré dans la liste des wsps du repo (ie non supprimé), mais **sans** existence sur le DD
    noWsp = "noWsp"  # wsp supprimé (ie non déclaré dans la liste des wsps du repo)


class EAllItemLoaded(StrEnum):
    no = "no"
    working = "working"
    ok = "ok"


class JWspProviderProps:
    backEnd: EBackEnd
    defaultContentPath: Optional[str]
    defaultGenPath: Optional[str]


class JWspDefProps(TypedDict):
    desc: Optional[str]
    publicWsp: Optional[StrBooleanEnum]
    airIt: Optional[StrBooleanEnum]
    extIt: Optional[StrBooleanEnum]
    prxIt: Optional[StrBooleanEnum]
    mirror: Optional[StrBooleanEnum]
    drfRefWsp: Optional[str]
    draftTitle: Optional[str]
    drvAxis: Optional[str]
    drvDefaultSrcFindPath: Optional[str]
    drvMasterWsp: Optional[str]


class JWspSrcFields(TypedDict):
    srcRoles: List[str]
    srcRi: Optional[Any]


class JWspType(TypedDict):
    uri: str
    key: str
    version: str
    lang: Optional[str]
    title: Optional[str]
    desc: Optional[str]


class JWspInfoInList(TypedDict):
    wspCd: str
    status: EWspLoadingStatus
    title: str
    alias: str
    props: JWspDefProps
    srcFields: Optional[JWspSrcFields]
    srcSpecifiedRoles: Optional[Any]
    isMigrationNeeded: Optional[bool]
    wspTypeWarn: Optional[str]
    wspType: JWspType
    wspOptions: List[JWspType]


class JListWsp(TypedDict):
    wspProvider: JWspProviderProps
    wsps: List[JWspInfoInList]


class JWspTypeInst(TypedDict):
    wspType: JWspType
    wspOptions: Optional[list[JWspType]]


class JInfoWsp(TypedDict):
    wspCd: str
    status: EWspLoadingStatus
    title: str
    alias: str
    skins: Optional[list[str]]
    props: JWspDefProps
    wspProvider: JWspProviderProps
    srcFields: Optional[JSrcFields]  # fields sur le noeud racine de l'atelier (roles, rights...)
    wspMeta: Optional[JWspTypeInst]
    """Props suivant dispo uniquement si status='ok'|'failed'"""
    isMigrationNeeded: Optional[bool]
    allItemsLoaded: Optional[EAllItemLoaded]
    wspTypeWarn: Optional[str]  # ? unknown
    wspType: JWspType
    wspOptions: List[JWspType]
    """Props uniquement présent dans les WSP FS local"""
    content: Optional[str]
    """Props uniquement présent dans les WSP local"""
    gen: Optional[str]


class JWspCreateParamsFS(TypedDict):
    title: Optional[str]
    desc: Optional[str]
    code: str
    folderContent: Optional[str]
    folderGen: Optional[str]


class JWspCreateParamsDB(TypedDict):
    title: str
    alias: Optional[str]
    desc: Optional[str]
    skins: Optional[list[str]]
    publicWsp: Optional[bool]
    airIt: Optional[bool]
    extIt: Optional[bool]
    mirror: Optional[bool]


class JWspCreateParamsDB_DRF(JWspCreateParamsDB):
    wspRef: Optional[str]
    draftTitle: Optional[str]


class JWspCreateParamsDB_DRV(JWspCreateParamsDB):
    wspMaster: Optional[str]
    drvAxis: Optional[str]
    drvDefaultSrcFindPath: Optional[list[str]]


class JWspUpdateParamsFS(TypedDict):
    title: Optional[str]
    desc: Optional[str]


class JWspUpdateParamsDB(TypedDict):
    title: Optional[str]
    alias: Optional[str]
    desc: Optional[str]
    skins: Optional[list[str]]
    publicWsp: Optional[bool]
    airIt: Optional[bool]
    extIt: Optional[bool]
    mirror: Optional[bool]


class JWspUpdateParamsDB_DRF(JWspUpdateParamsDB):
    wspRef: Optional[str]
    draftTitle: Optional[str]


class JWspUpdateParamsDB_DRV(JWspUpdateParamsDB):
    wspMaster: Optional[str]
    drvAxis: Optional[str]
    drvDefaultSrcFindPath: Optional[list[str]]


class JWspDeleteParamsFS(TypedDict):
    deleteGen: bool
    deleteContent: Optional[bool]


class JWspDeleteParamsDB(TypedDict):
    deleteGen: bool


class AdminWsp(Svc):
    def list(self) -> JListWsp:
        return json(self._s.get(self._url, params={"cdaction": "List"}))

    def create_wsp(self, wsp_type: JWspTypeInst, params: JWspCreateParamsFS | JWspCreateParamsDB | JWspCreateParamsDB_DRF | JWspCreateParamsDB_DRV) -> JInfoWsp:
        return json(self._s.put(self._url, params={"cdaction": "CreateWsp", "createParams": serialize_cdm(params)}, data=self.to_wsp_type_dom(wsp_type)))

    def info_wsp(self, wsp_code: str, ws_props_opts: Optional[dict[str, bool]] = None) -> JInfoWsp:
        qs = {"cdaction": "InfoWsp", "param": wsp_code}
        if ws_props_opts is not None:
            qs["wspPropsOpts"] = serialize_cdm(ws_props_opts)
        return json(self._s.get(self._url, params=qs))

    def update_wsp_props(self, wsp_code: str, params: JWspUpdateParamsFS | JWspUpdateParamsDB | JWspUpdateParamsDB_DRF | JWspUpdateParamsDB_DRV):
        resp = self._s.post(self._url, params={"cdaction": "UpdateWspProps", "param": wsp_code, "updateParams": serialize_cdm(params)})
        check_status(resp, 200)

    def update_wsp_type(self, wsp_code: str, wsp_type: JWspTypeInst):
        resp = self._s.put(self._url, params={"cdaction": "UpdateWspType", "param": wsp_code}, data=self.to_wsp_type_dom(wsp_type))
        check_status(resp, 200)

    def create_wsp_import(self, params: JWspCreateParamsFS | JWspCreateParamsDB | JWspCreateParamsDB_DRF | JWspCreateParamsDB_DRV, data: str | bytes) -> JInfoWsp:
        """Accepte un nom de fichier ou des bytes en data"""
        encoded = data if type(data) is bytes else Path(data).read_bytes()
        return json(self._s.put(self._url, params={"cdaction": "CreateWspImport", "createParams": serialize_cdm(params)}, data=encoded))

    def is_migration_needed(self, wsp_code: str, wsp_type: JWspTypeInst, normalize_wsp_type:bool = True):
        resp = self._s.put(self._url, params={"cdaction": "IsMigrationNeeded", "param": wsp_code, "normaliseWspType":normalize_wsp_type}, data=self.to_wsp_type_dom(wsp_type))
        check_status(resp, 200)

        response_text = text(resp)
        root = ElementTree.fromstring(response_text)
        if root.tag == "noMigrationNeeded":
            return False
        elif root.tag == "migrationNeeded":
            return True
        raise RuntimeError(f"Unknown IsMigrationNeeded response.\n{response_text}")

    def migrate_update_wsp_type(self, wsp_code, wsp_type: JWspTypeInst, normalize_wsp_type:bool = True) -> JInfoWsp:
        resp = self._s.put(self._url, params={"cdaction": "MigrateUpdateWspType", "param": wsp_code, "normaliseWspType":normalize_wsp_type}, data=self.to_wsp_type_dom(wsp_type))
        return json(resp)

    def migrate_update_wsp_type_and_wait(self, wsp_code, wsp_type: JWspTypeInst, normalize_wsp_type:bool = True) -> JInfoWsp:
        wsp = self.migrate_update_wsp_type(wsp_code, wsp_type, normalize_wsp_type)
        while wsp["status"] == "loading":
            time.sleep(1)
            wsp = self.info_wsp(wsp_code)

    def delete_wsp(self, wsp_code: str, params: JWspDeleteParamsFS|JWspDeleteParamsDB):
        resp = self._s.post(self._url, params={"cdaction": "DeleteWsp", "param": wsp_code, "deleteParams": serialize_cdm(params)})
        check_status(resp, 200)

    @staticmethod
    def to_wsp_type_dom(wsp_type_inst: JWspTypeInst):
        xml = f'<wspType key="{escape(wsp_type_inst["wspType"]["key"])}"'
        if "uri" in wsp_type_inst["wspType"]:
            xml += f' uri="{escape(wsp_type_inst["wspType"]["uri"])}"'
        if "version" in wsp_type_inst["wspType"]:
            xml += f' version="{escape(wsp_type_inst["wspType"]["version"])}"'
        if "lang" in wsp_type_inst["wspType"]:
            xml += f' lang="{escape(wsp_type_inst["wspType"]["lang"])}"'
        if "title" in wsp_type_inst["wspType"]:
            xml += f' title="{escape(wsp_type_inst["wspType"]["title"])}"'
        xml += ">"
        if "wspOptions" in wsp_type_inst:
            for wsp_option in wsp_type_inst["wspOptions"]:
                xml += f'<wspOption key="{wsp_option["key"]}"'
                if "uri" in wsp_option:
                    xml += f' uri="{escape(wsp_option["uri"])}"'
                if "version" in wsp_option:
                    xml += f' version="{escape(wsp_option["version"])}"'
                if "lang" in wsp_option:
                    xml += f' lang="{escape(wsp_option["lang"])}"'
                if "title" in wsp_option:
                    xml += f' title="{escape(wsp_option["title"])}"'
                xml += "/>"
        xml += "</wspType>"
        return xml

    def export_config(self) -> ElementTree.Element:
        return ElementTree.fromstring(text(self._s.put(self._url, params={"cdaction": "ExportConfig"})))
