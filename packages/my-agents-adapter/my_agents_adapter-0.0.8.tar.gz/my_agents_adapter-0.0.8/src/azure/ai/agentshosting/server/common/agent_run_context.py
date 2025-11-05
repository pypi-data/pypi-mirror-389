# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from ...logger import get_logger
from ...models import AgentId, AgentReference, ResponseConversation1
from ...models.openai.models import (
    CreateResponse,
    ImplicitUserMessage,
    ItemContent,
    ItemParam,
    ItemType,
)
from .id_generator.foundry_id_generator import FoundryIdGenerator
from .id_generator.id_generator import IdGenerator

logger = get_logger()


class AgentRunContext:
    def __init__(self, payload: dict):
        self._raw_payload = payload
        self._request = _deserialize_create_response(payload)
        self._id_generator = FoundryIdGenerator.from_request(payload)
        self._response_id = self._id_generator.response_id
        self._conversation_id = self._id_generator.conversation_id

    @property
    def raw_payload(self) -> dict:
        return self._raw_payload

    @property
    def request(self) -> CreateResponse:
        return self._request

    @property
    def id_generator(self) -> IdGenerator:
        return self._id_generator

    @property
    def response_id(self) -> str:
        return self._response_id

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    def get_agent_id_object(self) -> AgentId:
        if not self.request.agent:
            return None
        return AgentId(
            {
                "type": self.request.agent.type,
                "name": self.request.agent.name,
                "version": self.request.agent.version,
            }
        )

    def get_conversation_object(self) -> ResponseConversation1:
        if not self._conversation_id:
            return None
        return ResponseConversation1(id=self._conversation_id)


def _deserialize_create_response(payload: dict) -> CreateResponse:
    _deserialized = CreateResponse._deserialize(payload, [])

    raw_input = payload.get("input")
    if raw_input:
        if isinstance(raw_input, str):
            user_message = {"content": raw_input}  # force convert to ImplicitUserMessage
            _deserialized.input = [_deserialize_implicit_user_message(user_message)]
        elif isinstance(raw_input, list):
            _deserialized_input = []
            for input in raw_input:
                if isinstance(input, dict):
                    if "role" in input:
                        _deserialized_input.append(_deserialize_message_item_param(input))
                    elif "type" in input:
                        _deserialized_input.append(ItemParam._deserialize(input, []))
                    else:
                        _deserialized_input.append(_deserialize_implicit_user_message(input))
                else:
                    logger.warning(f"Unexpected input type in 'input' list: {type(input).__name__}")
            _deserialized.input = _deserialized_input

    raw_agent_reference = payload.get("agent")
    if raw_agent_reference:
        _deserialized.agent = _deserialize_agent_reference(raw_agent_reference)
    return _deserialized


def _deserialize_implicit_user_message(payload: dict) -> ImplicitUserMessage:
    _deserialized = ImplicitUserMessage._deserialize(payload, [])
    input_content = payload.get("content")
    if isinstance(input_content, list):
        _deserialized.content = _deserialize_item_content_list(input_content)
    elif not isinstance(input_content, str):  # string input, do nothing
        logger.warning(f"Unexpected content type in ImplicitUserMessage: {type(input_content)}")
    return _deserialized


def _deserialize_message_item_param(payload: dict) -> ItemParam:
    """Deserialize a input with role into an ResponsesMessageItemParam."""
    if "type" not in payload:
        payload["type"] = ItemType.MESSAGE
    _deserialized = ItemParam._deserialize(payload, [])
    input_content = payload.get("content")
    if isinstance(input_content, list):
        _deserialized.content = _deserialize_item_content_list(input_content)
    elif not isinstance(input_content, str):  # string input, do nothing
        logger.warning(f"Unexpected content type in ResponsesMessageItemParam: {type(input_content)}")
    return _deserialized


def _deserialize_item_content_list(payload: list) -> list[ItemContent]:
    _deserialized_list = []
    for item in payload:
        if isinstance(item, dict):
            _deserialized_list.append(ItemContent._deserialize(item, []))
        else:
            logger.warning(f"Unexpected item type in ItemContent list: {type(item).__name__}")
    return _deserialized_list


def _deserialize_agent_reference(payload: dict) -> AgentReference:
    if not payload:
        return None
    return AgentReference._deserialize(payload, [])
