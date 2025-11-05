from typing import Optional, TypedDict, Any

from ..common.svc import Svc
from ..common.utils import json, check_status, serialize_cdm


class JStrongboxState(TypedDict):
	strongboxOpened: bool
	masterPassModality: str
	dataVisibility: str


class Strongbox(Svc):
	def get_state(self) -> JStrongboxState:
		return json(self._s.get(self._url, params={"cdaction": "GetState"}))

	def open(self, password: str) -> JStrongboxState:
		return json(self._s.post(self._url, params={"cdaction": "Open"}, data={"pass": password}))

	def close(self) -> JStrongboxState:
		return json(self._s.get(self._url, params={"cdaction": "Close"}))

	def change_master_pass(self, password: str, new_password: str) -> None:
		return json(self._s.post(self._url, params={"cdaction": "ChangeMasterPass"}, data={"pass": password, "newPass": new_password}))

	def reset_strongbox(self, new_password: str) -> None:
		return check_status(self._s.post(self._url, params={"cdaction": "ResetStrongbox"}, data={"newPass": new_password}), 200)

	def set_data(self, box: str, entry: str, data: Optional[dict[str, any]]) -> None:
		if data is None:
			check_status(self._s.post(self._url, params={"cdaction": "SetData", "box": box, "entry": entry}), 200)
		else:
			check_status(self._s.post(self._url, params={"cdaction": "SetData", "box": box, "entry": entry}, data={"data": serialize_cdm(data)}), 200)

	def set_box_data(self, box: str, data: Optional[dict[str, dict[str, any]]] = None) -> None:
		if data is None:
			check_status(self._s.post(self._url, params={"cdaction": "SetBoxData", "box": box}), 200)
		else:
			check_status(self._s.post(self._url, params={"cdaction": "SetBoxData", "box": box}, data={"data": serialize_cdm(data)}), 200)

	def get_data(self, box: Optional[str] = None, entry: Optional[str] = None) -> dict[str, Any]:
		qs = {"cdaction": "GetData"}
		if box is not None:
			qs["box"] = box
		if entry is not None:
			qs["entry"] = entry
		return json(self._s.get(self._url, params=qs))
