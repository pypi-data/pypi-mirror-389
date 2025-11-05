"""Helper utilities for constructing AgentId model instances.

Centralizes logic for safely building a `models.AgentId` from a request agent
object. We intentionally do not allow overriding the generated model's fixed
`type` literal ("agent_id"). If the provided object lacks a name, `None` is
returned so callers can decide how to handle absence.
"""

from __future__ import annotations

from typing import Optional

from ...models.agents import models
from ..common.agent_run_context import AgentRunContext


class AgentIdGenerator:
    @staticmethod
    def generate(context: AgentRunContext) -> Optional[models.AgentId]:
        """Builds an AgentId model from the request agent object in the provided context."""
        if not context.request.agent:
            return None

        agent_id = models.AgentId(
            {
                "type": context.request.agent.type,
                "name": context.request.agent.name,
                "version": context.request.agent.version,
            }
        )

        return agent_id
