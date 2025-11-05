import datetime
import time
from datetime import timedelta
from typing import Optional, Any, TypedDict, List

from ..common.svc import Svc
from ..common.utils import StrEnum, serialize_cdm, json, check_status


class EBackupStatus(StrEnum):
	building = "building"
	available = "available"
	deleted = "deleted"


class EBackupError(StrEnum):
	lockWrite = "lockWrite"
	cancelled = "cancelled"
	other = "other"


class EBackupStep(StrEnum):
	lockWrite = "lockWrite"
	cancelLock = "cancelLock"
	freezeDatas = "freezeDatas"
	unlockWrite = "unlockWrite"
	backupDatas = "backupDatas"
	deleteBackup = "deleteBackup"


class ERestoreStatus(StrEnum):
	pending = "pending"
	done = "done"
	failed = "failed"


class ERestoreStep(StrEnum):
	lock = "lock"
	restore = "restore"
	catchUp = "catchUp"
	unlock = "unlock"


class EDeleteBackupStatus(StrEnum):
	pending = "pending"
	done = "done"
	notFound = "notFound"
	failedRestorePending = "failedRestorePending"
	failed = "failed"


class JBackupInfoBase(TypedDict):
	started: int
	startedDt: Optional[str]
	ended: Optional[int]
	endedDt: Optional[str]
	details: Optional[str]


class JBackupInfo(JBackupInfoBase):
	id: str
	status: EBackupStatus
	step: Optional[EBackupStep]
	error: Optional[EBackupError]


class JRestoreInfo(JBackupInfoBase):
	backupId: str
	retsoreId: str
	step: Optional[ERestoreStep]
	status: ERestoreStatus


class JDeleteBackupInfo(JBackupInfoBase):
	id: str
	status: EDeleteBackupStatus


class Backup(Svc):
	def list_backups(self) -> List[JBackupInfo]:
		return json(self._s.get(self._url, params={"cdaction": "ListBackups"}))

	def get_backup_info(self, backup_id: str) -> Optional[JBackupInfo]:
		resp = self._s.get(self._url, params={"cdaction": "GetBackupInfo", "backupId": backup_id})
		check_status(resp, 200, 404)
		return None if resp.status_code == 404 else json(resp)

	def get_last_backup_info(self) -> Optional[JBackupInfo]:
		resp = self._s.get(self._url, params={"cdaction": "GetLastAddBackupInfo"})
		check_status(resp, 200, 404)
		return None if resp.status_code == 404 else json(resp)

	def add_backup(self, backup_id: Optional[str] = None, options: Optional[dict[str, Any]] = None) -> JBackupInfo:
		qs = {"cdaction": "AddBackup"}
		if backup_id is not None:
			qs["backupId"] = backup_id
		if options is not None:
			qs["options"] = serialize_cdm(options)

		resp = self._s.put(self._url, params=qs)
		check_status(resp, 200, 409)
		if resp.status_code == 200:
			return json(resp)
		else:
			raise RuntimeError("Another restore or backup session is pending.")

	def wait_for_backup_deleted(self, backup_id: str) -> JBackupInfo:
		backup_info = self.get_backup_info(backup_id=backup_id)
		while backup_info is not None:
			time.sleep(1)
			backup_info = self.get_backup_info(backup_id=backup_id)
		return backup_info

	def wait_for_last_backup_available(self) -> JBackupInfo:
		info = self.get_last_backup_info()
		while info["status"] == EBackupStatus.building.value:
			time.sleep(1)
			info = self.get_last_backup_info()
		return info

	def cleanup_old_backups(self, days_to_keep: int = 0) -> JBackupInfo:
		for backup in self.list_backups():
			backup_date: datetime.datetime = datetime.datetime.fromtimestamp(backup["ended"] / 1000)
			delete_date = datetime.datetime.now() - timedelta(days=days_to_keep)
			if backup_date < delete_date:
				self.delete_backup(backup["id"])

	def restore_backup(self, backup_id: str = "~last", with_catch_up: bool = False, options: Optional[dict[str, Any]] = None) -> JRestoreInfo:
		qs = {"cdaction": "RestoreBackup", "backupId": backup_id, "catchUp": with_catch_up}
		if options is not None:
			qs["options"] = serialize_cdm(options)

		resp = self._s.put(self._url, params=qs)
		check_status(resp, 200)
		return json(resp)

	def get_last_restore_info(self) -> Optional[JRestoreInfo]:
		resp = self._s.get(self._url, params={"cdaction": "GetLastRestoreInfo"})
		check_status(resp, 200, 404)
		return None if resp.status_code == 404 else json(resp)

	def delete_backup(self, backup_id: str, options: Optional[dict[str, Any]] = None) -> Optional[JBackupInfo]:
		qs = {"cdaction": "DeleteBackup", "backupId": backup_id}
		if options is not None:
			qs["options"] = serialize_cdm(options)

		resp = self._s.put(self._url, params=qs)
		check_status(resp, 200, 404)
		return None if resp.status_code == 404 else json(resp)

	def get_last_delete_backup_info(self) -> Optional[JBackupInfo]:
		resp = self._s.get(self._url, params={"cdaction": "GetLastDeleteBackupInfo"})
		check_status(resp, 200, 404)
		return None if resp.status_code == 404 else json(resp)
