from typing import TypedDict, Optional, Any

from .engine import JProject
from ..common.svc import Svc
from ..common.utils import json, serialize_cdm


class JRawParticipant(TypedDict):
	project_id: str
	participant_id: str
	kind: str
	user: str
	start_dt: int
	end_dt: int
	state: str


class JUpdateParticipantsProps(TypedDict):
	addParticipants: list[str]  # Liste d'account
	enableParticipants: list[str]  # Liste d'id de participants
	disableParticipants: list[str]  # Liste d'id de participants
	deleteParticipants: list[str]  # Liste d'id de participants


class ProjectAdmin(Svc):
	def get_participants(self, project_id: str, kind: str) -> list[JRawParticipant]:
		return json(self._s.get(self._url, params={"cdaction": "GetParticipants", "param": project_id, "kind": kind}))

	def enable(self, project_id: str) -> JProject:
		return json(self._s.put(self._url, params={"cdaction": "Enable", "param": project_id}))

	def disable(self, project_id: str) -> JProject:
		return json(self._s.put(self._url, params={"cdaction": "Disable", "param": project_id}))

	def reset(self, project_id: str) -> bool:
		return json(self._s.put(self._url, params={"cdaction": "Reset", "param": project_id}))

	def update_participants(self, project_id: str, kind:str, update_participants_props: JUpdateParticipantsProps) -> list[JRawParticipant]:
		return json(self._s.put(self._url, params={"cdaction": "UpdateParticipants", "param": project_id, "kind": kind}, json=update_participants_props))
