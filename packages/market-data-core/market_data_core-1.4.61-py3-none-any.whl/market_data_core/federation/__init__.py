"""Federation contracts for multi-node deployments."""

from .status import ClusterTopology, NodeStatus
from .types import ClusterId, NodeId, NodeRole, Region

__all__ = [
    # Types
    "ClusterId",
    "NodeId",
    "NodeRole",
    "Region",
    # Status
    "NodeStatus",
    "ClusterTopology",
]
