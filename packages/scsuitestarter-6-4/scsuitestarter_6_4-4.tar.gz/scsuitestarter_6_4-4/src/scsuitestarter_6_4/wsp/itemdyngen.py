import json
from typing import Optional, TypedDict, Any

from ..common.svc import Svc
from ..common.utils import serialize_cdm, json, check_status, encode_url2


class JSkinInfo(TypedDict):
	code: str
	title: str
	owner: str


class ItemDynGen(Svc):
	def get(self, wsp_code: str, ref_uri: str, code_gen: str, props: dict[str, Any] = {}, path_in_gen: str = ""):
		props["refUri"] = ref_uri
		resp = self._s.get(f"{self._url}/{wsp_code}/{code_gen}/{encode_url2(serialize_cdm(props))}/{path_in_gen}")
		check_status(resp, 200)
		return resp.content

	def get_skins(self, wsp_code: str, ref_uri: str, code_gen: str) -> list[JSkinInfo]:
		qs = {"cdaction": "GetSkins", "wspCd": wsp_code, "refUri": ref_uri, "cdGen": code_gen}
		return json(self._s.get(self._url, params=qs))
