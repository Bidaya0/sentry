import abc
from typing import cast

from sentry.services.hybrid_cloud.auth import RpcAuthIdentity, RpcAuthProvider
from sentry.services.hybrid_cloud.organization import RpcTeam
from sentry.services.hybrid_cloud.region import ByRegionName
from sentry.services.hybrid_cloud.rpc import RpcService, regional_rpc_method, rpc_method
from sentry.silo import SiloMode


class ControlReplicaService(RpcService):
    key = "control_replica"
    local_mode = SiloMode.CONTROL

    @rpc_method
    @abc.abstractmethod
    def upsert_replicated_team(self, *, team: RpcTeam) -> None:
        pass

    @classmethod
    def get_local_implementation(cls) -> RpcService:
        from .impl import DatabaseBackedControlReplicaService

        return DatabaseBackedControlReplicaService()


class RegionReplicaService(RpcService):
    key = "region_replica"
    local_mode = SiloMode.REGION

    @regional_rpc_method(resolve=ByRegionName())
    @abc.abstractmethod
    def upsert_replicated_auth_provider(
        self, *, auth_provider: RpcAuthProvider, region_name: str
    ) -> None:
        pass

    @regional_rpc_method(resolve=ByRegionName())
    @abc.abstractmethod
    def upsert_replicated_auth_identity(
        self, *, auth_identity: RpcAuthIdentity, region_name: str
    ) -> None:
        pass

    @classmethod
    def get_local_implementation(cls) -> RpcService:
        from .impl import DatabaseBackedRegionReplicaService

        return DatabaseBackedRegionReplicaService()


region_replica_service = cast(RegionReplicaService, RegionReplicaService.create_delegation())
control_replica_service = cast(ControlReplicaService, ControlReplicaService.create_delegation())
