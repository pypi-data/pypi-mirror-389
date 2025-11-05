from typing import Optional

from ..common.svc import Svc
from ..common.utils import serialize_cdm, check_status, text


class StoreSquare(Svc):
	def enable_batch(self):
		resp = self._s.put(self._url, params={"cdaction": "EnableBatch"})
		check_status(resp, 204)

	def disable_batch(self):
		resp = self._s.put(self._url, params={"cdaction": "DisableBatch"})
		check_status(resp, 204)

	def export_st_log(self) -> str:
		resp = self._s.put(self._url, params={"cdaction": "ExportStLog"})
		check_status(resp, 200)
		return text(resp)

	def gc(self):
		resp = self._s.put(self._url, params={"cdaction": "Gc"})
		check_status(resp, 204, 200)

	def catch_up(self, data: str | bytes, options: Optional[dict[str, str]] = None) -> str:
		encoded = data if type(data) is bytes else data.encode(encoding='utf-8')
		qs = {"cdaction": "PutSrc"}
		if options is not None:
			qs["options"] = serialize_cdm(options)
		resp = self._s.put(self._url, params=qs, data=encoded)
		check_status(resp, 200)
		return text(resp)
