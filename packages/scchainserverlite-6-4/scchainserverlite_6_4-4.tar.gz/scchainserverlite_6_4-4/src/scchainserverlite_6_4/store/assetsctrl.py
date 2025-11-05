from ..common.svc import Svc
from ..common.utils import check_status, text


class AssetsCtrl(Svc):

	def gc(self) -> None:
		check_status(self._s.put(self._url, params={"cdaction": "Gc"}), 204, 200)

	def check_missing_assets(self) -> None | list[str]:
		resp = self._s.put(self._url, params={"cdaction": "CheckMissingAssets"})
		if resp.status_code == 200:
			return text(resp).split("\n")
		else:
			check_status(resp, 204)
