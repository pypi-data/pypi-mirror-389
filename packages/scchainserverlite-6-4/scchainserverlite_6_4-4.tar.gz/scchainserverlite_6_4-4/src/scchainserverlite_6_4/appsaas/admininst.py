from typing import Optional, TypedDict, List

from ..common.svc import Svc
from ..common.utils import StrEnum, serialize_cdm, json


class ESaasStatus(StrEnum):
	stopped = "stopped"
	started = "started"
	failed = "failed"
	stopping = "stopping"
	starting = "starting"


class EStartingMode(StrEnum):
	manual = "manuel"
	auto = "auto"


class JInstInfo(TypedDict):
	instId: str
	instPath: str
	lastDeploy: int
	startingMode: EStartingMode
	instStatus: ESaasStatus
	error: Optional[str]


class JInfosServer(TypedDict):
	serverId: str
	serverStatus: ESaasStatus
	instances: List[JInstInfo]


# Autre forme d'ecriture du TypedDict pour escaper le mot réservé from
JInstConst = TypedDict('JInstConst', {
	"from": str,
	"to": str,
	"date": str,
	"time": str,
	"countRequests": int,
	"uploadBytes": int,
	"downloadBytes": int,
	"countFiles": int,
	"filesBytes": int,
	"detailsFields": List[str],
	"details": List[List[str | int]]
})


class AdminInst(Svc):
	def get_info(self) -> JInfosServer:
		return json(self._s.get(self._url, params={"cdaction": "GetInfo"}))

	def start_server(self) -> JInfosServer:
		return json(self._s.put(self._url, params={"cdaction": "StartServer"}))

	def stop_server(self) -> JInfosServer:
		return json(self._s.put(self._url, params={"cdaction": "StopServer"}))

	def add_inst(self, path: str, auto_start: bool = False) -> JInstInfo:
		return json(self._s.put(self._url, params={"cdaction": "AddInst", "path": path, "startInst": auto_start}))

	def start_inst(self, inst_id: str) -> JInstInfo:
		return json(self._s.put(self._url, params={"cdaction": "StartInst", "instId": inst_id}))

	def stop_inst(self, inst_id: str) -> JInstInfo:
		return json(self._s.put(self._url, params={"cdaction": "StopInst", "instId": inst_id}))

	def reload_inst(self, inst_id: str) -> JInstInfo:
		return json(self._s.put(self._url, params={"cdaction": "ReloadInst", "instId": inst_id}))

	def remove_inst(self, inst_id: str) -> JInstInfo:
		return json(self._s.put(self._url, params={"cdaction": "RemoveInst", "instId": inst_id}))

	def get_inst_infos(self, inst_id: str) -> JInstInfo:
		return json(self._s.get(self._url, params={"cdaction": "GetInstInfos", "instId": inst_id}))

	def get_cons_inst(self, inst_id: str, days: int = 30) -> JInstConst:
		return json(self._s.get(self._url, params={"cdaction": "GetInstInfos", "instId": inst_id, "days": days}))

	def clone_inst(self, inst_id: str, inst_type: str, inst_vars: Optional[dict[str, str]] = None, auto_start: bool = False) -> JInstInfo:
		qs = {"cdaction": "CloneInst", "instId": inst_id, "instType": inst_type, "startInst": auto_start}
		if inst_vars is not None:
			qs["vars"] = serialize_cdm(inst_vars)
		return json(self._s.put(self._url, params=inst_vars))
