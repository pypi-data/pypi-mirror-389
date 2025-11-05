from typing import TypedDict, cast

from ..common.utils import StrEnum
from ..core.backupinplace import BackupInPlace


class EInstsBackupStatus(StrEnum):
	startBkpPending = "startBkpPending"
	endBkpPending = "endBkpPending"
	locked = "locked"
	notLocked = "notLocked"
	error = "error"


class JInstsBackupStates(TypedDict):
	status: EInstsBackupStatus
	change: int


class InstsBackupInPlace(BackupInPlace):
	def get_backup_states(self) -> JInstsBackupStates:
		return cast(JInstsBackupStates, super().get_backup_states())
