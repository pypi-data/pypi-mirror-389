from typing import Optional, Any, TypedDict

from ..common.svc import Svc
from ..common.utils import json, check_status


class JBackupState(TypedDict):
	started: int
	finished: Optional[int]
	error: Optional[Any]


class JBackupStates(TypedDict):
	previous: Optional[JBackupState]
	last: Optional[JBackupState]  # Possiblement encore en cours


class BackupInPlace(Svc):
	def get_backup_states(self) -> JBackupStates:
		return json(self._s.get(self._url, params={"cdaction": "GetBackupStates"}))

	def start_backup(self):
		resp = self._s.put(self._url, params={"cdaction": "StartBackup"})
		check_status(resp, 200)

	def end_backup(self):
		resp = self._s.put(self._url, params={"cdaction": "EndBackup"})
		check_status(resp, 200)
