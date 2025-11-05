from time import sleep
from typing import TypedDict, Optional, Any

from ..common.svc import Svc
from ..common.utils import StrEnum, json, check_status


class EDptResInstMgrStatus(StrEnum):
	initing = "initing"
	running = "running"
	notAvailable = "notAvailable"


class EEditSessionStatus(StrEnum):
	inSync = "inSync"
	failed = "failed"
	passed = "passed"
	contentNotSync = "contentNotSync"
	syncFailed = "syncFailed"
	resNotFound = "resNotFound"
	notexist = "notexist"
	unknown = "unknown"


class EOpenSessionMode(StrEnum):
	previous = "previous"  # reprise du contenu de la dernière session
	resetContent = "previous"  # reprise de la session, mais suppression du contenu


class JDptResInstMgrInfo(TypedDict):
	chainInstMgr: EDptResInstMgrStatus
	dptMaster: bool


class JEditSessionInfo(TypedDict):
	status: EEditSessionStatus
	error: Optional[dict[str, Any]]
	sessionId: str
	path: str


class DptResInstMgr(Svc):
	def get_infos(self) -> JDptResInstMgrInfo:
		return json(self._s.get(self._url, params={"cdaction": "GetInfos"}))

	def list_open_edit_sessions(self) -> list[JEditSessionInfo]:
		return json(self._s.get(self._url, params={"cdaction": "ListOpenEditSessions"}))

	def open_edit_session(self, path: str, mode: EOpenSessionMode = EOpenSessionMode.previous, start: bool = True) -> JEditSessionInfo:
		return json(self._s.put(self._url, params={"cdaction": "OpenEditSession", "path": path, "favoriteMode": mode.value, "forceStart": "true" if start else "false"}))

	def get_edit_session_infos(self, path: str) -> Optional[JEditSessionInfo]:
		resp = self._s.get(self._url, params={"cdaction": "GetEditSessionInfos", "path": path})
		return json(resp) if resp.status_code == 200 else None

	def remove_edit_session(self, path: str):
		resp = self._s.put(self._url, params={"cdaction": "RemoveEditSession", "path": path})
		check_status(resp, 200)

	def refresh_edit_session(self, path: str) -> Optional[JEditSessionInfo]:
		resp = self._s.put(self._url, params={"cdaction": "RefreshEditSession", "path": path})
		check_status(resp, 200, 404)
		return json(resp) if resp.status_code == 200 else None

	def reset_status_and_refresh_edit_session(self, path: str) -> Optional[JEditSessionInfo]:
		resp = self._s.put(self._url, params={"cdaction": "ResetStatusAndRefreshEditSession", "path": path})
		check_status(resp, 200, 404)
		return json(resp) if resp.status_code == 200 else None

	def enable_maintenance_mode(self):
		resp = self._s.put(self._url, params={"cdaction": "EnableMaintenanceMode"})
		check_status(resp, 204)

	def disable_maintenance_mode(self):
		resp = self._s.put(self._url, params={"cdaction": "DisableMaintenanceMode"})
		check_status(resp, 204)

	def open_and_wait_edit_session(self, path: str, mode: EOpenSessionMode = EOpenSessionMode.previous, start: bool = True) -> JEditSessionInfo:
		info: JEditSessionInfo = self.open_edit_session(path, mode, start)
		while info["status"] == EEditSessionStatus.inSync:
			sleep(1)
			info = self.get_edit_session_infos(path)
		return info
