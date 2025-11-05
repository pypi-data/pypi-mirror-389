from typing import TypedDict, Optional

from ..common.svc import Svc
from ..common.utils import StrEnum, serialize_cdm, json, check_status


class ESaasServerStatus(StrEnum):
	running = "running",
	initing = "initing",
	notAvailable = "notAvailable"


class EReloadAllClustersStatus(StrEnum):
	ok = "ok"
	errors = "errors"


class ECleanOrphanInstsStatus(StrEnum):
	ok = "ok"
	errors = "orphansFound"


class JSaasServerInfos(TypedDict):
	status: ESaasServerStatus


class JClusterInstInfo(TypedDict):
	id: str
	type: str


class JClusterInfo(TypedDict):
	version: int
	id: str
	insts: dict[str, JClusterInstInfo]
	vars: dict[str, str]


class JClusterSummary(TypedDict):
	id: str
	lastModif: int


class JReloadClustersResult(TypedDict):
	status: EReloadAllClustersStatus
	errors: Optional[list[str]]


class JCleanOrphanInstsResult(TypedDict):
	status: ECleanOrphanInstsStatus
	deletedInsts: Optional[list[str]]


class InstsClusterMgr(Svc):
	def get_infos(self) -> JSaasServerInfos:
		return json(self._s.get(self._url, params={"cdaction": "GetInfos"}))

	def list_clusters(self) -> list[JClusterSummary]:
		return json(self._s.get(self._url, params={"cdaction": "ListClusters"}))

	def get_cluster_infos(self, cluster_id: str) -> JClusterInfo:
		return json(self._s.get(self._url, params={"cdaction": "GetClusterInfos", "id": cluster_id}))

	def get_cluster_props(self, cluster_id: str) -> JClusterInfo:
		cluster_info = self.get_cluster_infos(cluster_id)
		props = cluster_info["vars"]
		for key in cluster_info["insts"]:
			props[f"instance.id@{cluster_info['insts'][key]['type']}"] = cluster_info["insts"][key]["id"]
		return props

	def create_cluster(self, cluster_id: str, inst_vars: Optional[dict[str, str]] = None) -> JClusterInfo:
		qs = {"cdaction": "CreateCluster", "id": cluster_id}
		if inst_vars is not None:
			qs["vars"] = serialize_cdm(inst_vars)
		return json(self._s.put(self._url, params=qs))

	def remove_cluster(self, cluster_id: str):
		resp = self._s.put(self._url, params={"cdaction": "RemoveCluster", "id": cluster_id})
		check_status(resp, 200)

	def reload_all_clusters(self) -> JReloadClustersResult:
		return json(self._s.put(self._url, params={"cdaction": "ReloadAllClusters"}))

	def clean_orphan_insts(self) -> JCleanOrphanInstsResult:
		return json(self._s.put(self._url, params={"cdaction": "CleanOrphanInsts"}))
