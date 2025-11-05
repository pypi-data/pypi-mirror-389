from typing import Optional, List

from ..api.item import ESrcField
from ..common.svc import Svc
from ..common.utils import check_status
from ..common.utils import json as parse_json


class History(Svc):
	def list_trashed_nodes(self, wsp_code: str, ref_uri_live: str, fields: List[ESrcField]):
		qs = {"cdaction": "ListTrashedNodes", "param": wsp_code, "refUriLive": ref_uri_live}
		if fields is not None:
			qs["fields"] = "*".join(fields)
		return parse_json(self._s.get(self._url, params=qs))

	def list_history_nodes(self, wsp_code: str, ref_uri_live: str, fields: List[ESrcField]):
		qs = {"cdaction": "ListHistoryNodes", "param": wsp_code, "refUriLive": ref_uri_live}
		if fields is not None:
			qs["fields"] = "*".join(fields)
		return parse_json(self._s.get(self._url, params=qs))

	def restore_trashed(self, wsp_code: str, src_uris: List[str]):
		qs = {"cdaction": "RestoreTrashed", "param": wsp_code, "srcUris": "\t".join(src_uris)}
		return check_status(self._s.post(self._url, params=qs), 200)

	def restore_from_history(self, wsp_code: str, ref_uri_live: str, ref_uri_hist: str):
		qs = {"cdaction": "RestoreFromHistory", "param": wsp_code, "refUriLive": ref_uri_live, "refUriHist": ref_uri_hist}
		return check_status(self._s.post(self._url, params=qs), 200)

	def delete_permanently(self, wsp_code: str, src_uris: List[str]):
		qs = {"cdaction": "DeletePermanently", "param": wsp_code, "srcUris": "\t".join(src_uris)}
		return check_status(self._s.post(self._url, params=qs), 200)

	def delete_permanently_all(self, wsp_code: str, src_uris: Optional[List[str]] = None):
		qs = {"cdaction": "DeletePermanentlyAll", "param": wsp_code}
		if src_uris is not None:
			qs["srcUris"] = "\t".join(src_uris)
		return check_status(self._s.post(self._url, params=qs), 200)
