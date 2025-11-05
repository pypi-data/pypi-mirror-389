from __future__ import annotations

from typing import List

from agent_framework import ChatMessage, Role as ChatRole
from agent_framework._types import TextContent

from ...logger import get_logger
from ...models.openai.models import (
    ImplicitUserMessage,
    ItemContentInputText,
    ItemParam,
    ResponsesAssistantMessageItemParam,
    ResponsesMessageItemParam,
    ResponsesSystemMessageItemParam,
    ResponsesUserMessageItemParam,
)

logger = get_logger()


class AgentFrameworkInputConverter:
    """Normalize inputs for agent.run.

    Accepts: str | List[ImplicitUserMessage | ItemParam] | None
    Returns: None | str | ChatMessage | list[str] | list[ChatMessage]
    """

    def transform_input(
        self,
        input: str | List[ImplicitUserMessage | ItemParam] | None,
    ) -> str | ChatMessage | list[str] | list[ChatMessage] | None:
        logger.debug("Transforming input of type: %s", type(input))

        if input is None:
            return None

        if isinstance(input, str):
            return input

        try:
            if isinstance(input, list):
                messages: list[str | ChatMessage] = []

                for item in input:
                    # Case 1: ImplicitUserMessage with content as str or list of ItemContentInputText
                    if isinstance(item, ImplicitUserMessage):
                        content = getattr(item, "content", None)
                        if isinstance(content, str):
                            messages.append(content)
                        elif isinstance(content, list):
                            text_parts: list[str] = []
                            for content_item in content:
                                if (
                                    hasattr(content_item, "type")
                                    and content_item.type == "input_text"
                                    and isinstance(content_item, ItemContentInputText)
                                ):
                                    text_parts.append(content_item.text)
                            if text_parts:
                                messages.append(" ".join(text_parts))

                    # Case 2: Explicit message params (user/assistant/system)
                    elif (
                        hasattr(item, "type")
                        and item.type == "message"
                        and isinstance(item, ResponsesMessageItemParam)
                        and isinstance(
                            item,
                            (
                                ResponsesUserMessageItemParam,
                                ResponsesAssistantMessageItemParam,
                                ResponsesSystemMessageItemParam,
                            ),
                        )
                    ):
                        role_map = {
                            "user": ChatRole.USER,
                            "assistant": ChatRole.ASSISTANT,
                            "system": ChatRole.SYSTEM,
                        }
                        role = role_map.get(getattr(item, "role", "user"), ChatRole.USER)

                        content_text = ""
                        if hasattr(item, "content") and isinstance(item.content, list):
                            text_parts: list[str] = []
                            for content_item in item.content:
                                if (
                                    hasattr(content_item, "type")
                                    and content_item.type == "input_text"
                                    and isinstance(content_item, ItemContentInputText)
                                ):
                                    text_parts.append(content_item.text)
                            content_text = " ".join(text_parts) if text_parts else ""
                        else:
                            content_text = str(getattr(item, "content", ""))

                        if content_text:
                            messages.append(ChatMessage(role=role, text=content_text))

                # Determine the most natural return type
                if not messages:
                    return None
                if len(messages) == 1:
                    return messages[0]
                if all(isinstance(m, str) for m in messages):
                    return [m for m in messages if isinstance(m, str)]
                if all(isinstance(m, ChatMessage) for m in messages):
                    return [m for m in messages if isinstance(m, ChatMessage)]

                # Mixed content: coerce ChatMessage to str by extracting TextContent parts
                result: list[str] = []
                for msg in messages:
                    if isinstance(msg, ChatMessage):
                        text_parts: list[str] = []
                        for c in getattr(msg, "contents", []) or []:
                            if isinstance(c, TextContent):
                                text_parts.append(c.text)
                        result.append(" ".join(text_parts) if text_parts else str(msg))
                    else:
                        result.append(str(msg))
                return result

            raise TypeError(f"Unsupported input type: {type(input)}")
        except Exception as e:
            logger.error("Error processing messages: %s", e, exc_info=True)
            raise Exception(f"Error processing messages: {e}") from e
