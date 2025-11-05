from time import sleep
from typing import Optional, List, Any

import requests

from ..common.svc import Svc
from ..common.utils import StrEnum, json


class ECidStatus(StrEnum):
	working = "working"  # Statut initial, traitement en cours
	waitingUserInput = "waitingUserInput"  # La tâche est en attente d'un retour utilisateur
	waitingForCommit = "waitingForCommit"  # La tâche est en attente du commit final
	commiting = "commiting"  # Commit de la tâche en cours
	rollbacking = "rollbacking"  # Rollback de la tâche en cours
	commited = "commited"  # La tâche est achevée, commitée
	rollbacked = "rollbacked"  # rollback La tâche n'a pu être démarrée ou a échouée et a été correctement rollbackée. Les données sont dans un état consistant
	failed = "failed"  # La tâche est en échec (après rollback ou revert). Pourrait donc laisser les données dans un état inconsistant


class CidServer(Svc):
	def _request(self, params: dict[str, str], props: Optional[dict[str, str]] = None, sync: Optional[bool] = True, content: Optional[bytes | str] = None,
	             return_props: Optional[List[str]] = None, resp: Optional[str] = "200-403") -> requests.Response:
		qs = {}
		if props is not None:
			for prop in props:
				qs[prop] = props[prop]
		if return_props is not None:
			qs["returnProps"] = "*".join(return_props)
		if resp is not None:
			qs["scResp"] = resp
		qs["synch"] = "true" if sync else "false"
		for param in params:
			qs[param] = params[param]

		if content is None:
			return self._s.post(self._url, params=qs)
		else:
			if type(content) is str:
				with open(content, "rb") as file:
					data = file.read()
			else:
				data = content
			return self._s.put(self._url, params=qs, data=data)

	def start_session(self, props: dict[str, str], sync: bool = True, content: Optional[bytes | str] = None, return_props: Optional[List[str]] = None,
	                  resp: Optional[str] = "200-403") -> requests.Response:
		return self._request(params={"cdaction": "StartSession"}, props=props, sync=sync, content=content, return_props=return_props, resp=resp)

	def create_session_only(self, props: dict[str, str]) -> str:
		return json(self._s.post(f"{self._url}?createSessionOnly&returnProps=scCidSessId", params=props))["scCidSessId"]

	def request_session(self, cid_session_id: str, props: dict[str, str] = None, sync: bool = True, content: Optional[bytes | str] = None, return_props: Optional[List[str]] = None,
	                    resp: Optional[str] = "200-403") -> requests.Response:
		return self._request(params={"cdaction": "RequestSession", "scCidSessId": cid_session_id}, props=props, sync=sync, content=content, return_props=return_props, resp=resp)

	def get_session_state(self, cid_session_id: str, return_props: Optional[List[str]] = None, resp: Optional[str] = "200-403") -> requests.Response:
		return self._request(params={"cdaction": "GetSessionState", "scCidSessId": cid_session_id}, return_props=return_props, resp=resp, sync=False)

	"""
	Wrap des cdactions du service pour appels sync et async.
	"""

	def sync_cid_request(self, metas: dict[str, str], content: Optional[bytes | str] = None, return_props: Optional[List[str]] = None, resp: Optional[str] = "200-403") -> dict[
		str, Any]:
		metas["createMetas"] = "true"
		if content is None:
			metas["scContent"] = "none"
		return json(self.start_session(props=metas, sync=True, content=content, return_props=return_props, resp=resp))

	def async_cid_request(self, metas: dict[str, str], content: Optional[bytes | str] = None, return_props: Optional[List[str]] = None) -> dict[str, Any]:
		metas["createMetas"] = "true"

		if content is None:
			metas["scContent"] = "none"

		if return_props is None:
			return_props = []
		if "scCidSessId" not in return_props:
			return_props.append("scCidSessId")
		if "scCidSessStatus" not in return_props:
			return_props.append("scCidSessStatus")

		resp = json(self.start_session(props=metas, sync=True, content=content, return_props=return_props))
		while resp["scCidSessStatus"] not in [ECidStatus.failed.value, ECidStatus.rollbacked.value, ECidStatus.commited.value]:
			sleep(1)
			resp = json(self.get_session_state(resp["scCidSessId"], return_props=return_props))
		return resp
