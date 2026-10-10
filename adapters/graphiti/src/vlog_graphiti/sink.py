from __future__ import annotations

import asyncio
from datetime import datetime
from importlib import import_module
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from vlog_memory_domain import EpisodeProjectionPayload

GRAPH_UUID_NAMESPACE = "urn:vlog:graphiti-projection:"


class GraphitiClientProtocol(Protocol):
    async def add_episode(
        self,
        *,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: datetime,
        group_id: str,
        uuid: str,
    ) -> Any: ...


class GraphitiProjectionSink:
    """Projects one canonical episode as one Graphiti temporal episode."""

    def __init__(self, client: GraphitiClientProtocol, *, group_id: str) -> None:
        self._client = client
        self._group_id = group_id

    def graph_uuid(self, payload: EpisodeProjectionPayload) -> str:
        return str(uuid5(NAMESPACE_URL, GRAPH_UUID_NAMESPACE + payload.projection_key))

    def project(self, payload: EpisodeProjectionPayload) -> str:
        graph_uuid = self.graph_uuid(payload)
        asyncio.run(
            self._client.add_episode(
                name=payload.episode_name,
                episode_body=payload.body,
                source_description=payload.source_description,
                reference_time=payload.reference_time,
                group_id=self._group_id,
                uuid=graph_uuid,
            )
        )
        return graph_uuid


def build_graphiti_client(uri: str, user: str, password: str) -> GraphitiClientProtocol:
    return import_module("graphiti_core").Graphiti(uri, user, password)
