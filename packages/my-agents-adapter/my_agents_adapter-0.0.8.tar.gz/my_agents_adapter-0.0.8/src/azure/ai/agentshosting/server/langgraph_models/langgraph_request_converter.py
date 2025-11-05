import json
from typing import Dict, List

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall

from ...logger import get_logger
from ...models.openai import models as openai_models

logger = get_logger()

role_mapping = {
    openai_models.ResponsesMessageRole.USER: HumanMessage,
    openai_models.ResponsesMessageRole.SYSTEM: SystemMessage,
    openai_models.ResponsesMessageRole.ASSISTANT: AIMessage,
    # openai_models.ResponsesMessageRole.DEVELOPER: ToolMessage,
}

item_content_type_mapping = {
    openai_models.ItemContentType.INPUT_TEXT: "text",
    openai_models.ItemContentType.INPUT_AUDIO: "audio",
    openai_models.ItemContentType.INPUT_IMAGE: "image",
    openai_models.ItemContentType.INPUT_FILE: "file",
    openai_models.ItemContentType.OUTPUT_TEXT: "text",
    openai_models.ItemContentType.OUTPUT_AUDIO: "audio",
    # openai_models.ItemContentType.REFUSAL: "refusal",
}


class LangGraphRequestConverter:
    def __init__(self, data: openai_models.CreateResponse):
        self.data: openai_models.CreateResponse = data

    def convert(self) -> dict:
        # Convert the CreateRunRequest input to a format suitable for LangGraph
        langgraph_input = {"messages": []}

        if self.data.instructions:
            langgraph_input["messages"].append(SystemMessage(content=self.data.instructions))

        input = self.data.input
        if isinstance(input, str):
            langgraph_input["messages"].append(HumanMessage(content=input))
        elif isinstance(input, List):
            for inner in input:
                if isinstance(inner, openai_models.ImplicitUserMessage):
                    langgraph_input["messages"].append(self.convert_OpenAIImplicitUserMessage(inner))
                elif isinstance(inner, openai_models.ItemParam):
                    langgraph_input["messages"].append(self.convert_OpenAIItemParam(inner))
                else:
                    raise ValueError(f"Unsupported input type: {type(inner)}")
        return langgraph_input

    def convert_OpenAIImplicitUserMessage(self, input_message: openai_models.ImplicitUserMessage) -> AnyMessage:
        """
        Convert OpenAIImplicitUserMessageContent to a list of message
        """
        if isinstance(input_message.content, str):
            return HumanMessage(content=input_message.content)
        if isinstance(input_message.content, list):
            return HumanMessage(content=self.convert_OpenAIItemContentList(input_message.content))
        raise ValueError(
            f"Unsupported ImplicitUserMessage content type: {type(input_message.content)}, {input_message.content}"
        )

    def convert_OpenAIItemContentList(self, content: List[openai_models.ItemContent]) -> List:
        """
        Convert ItemContent to a list format
        """
        result = []
        for item in content:
            if isinstance(item, openai_models.ItemContent):
                result.append(self.convert_OpenAIItemContent(item))
            else:
                raise ValueError(f"Unsupported ItemContent type: {type(item)}, {item}")
        return result

    def convert_OpenAIItemContent(self, content: openai_models.ItemContent) -> Dict:
        """
        Convert ItemContent to a dict format
        """
        if isinstance(content, openai_models.ItemContent):
            res = content.as_dict()
            res["type"] = item_content_type_mapping.get(content.type, content.type)
            return res
        else:
            raise ValueError(f"Unsupported ItemContent type: {type(content)}, {content}")

    def convert_OpenAIItemParam(self, item: openai_models.ItemParam) -> AnyMessage:
        """
        Convert OpenAIItemParam to a dict format
        """
        if item.type == openai_models.ItemType.MESSAGE:
            if isinstance(item.content, str):
                return role_mapping[item.role](content=item.content)
            elif isinstance(item.content, list):
                return role_mapping[item.role](content=self.convert_OpenAIItemContentList(item.content))
            raise ValueError(
                f"Unsupported ResponseMessagesItemParam content type: {type(item.content)}, {item.content}"
            )
        elif item.type == openai_models.ItemType.FUNCTION_CALL:
            try:
                args = json.loads(item.arguments) if item.arguments else {}
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in function call arguments: {item.arguments}") from e
            return AIMessage(tool_calls=[ToolCall(id=item.call_id, name=item.name, args=args)], content="")
        elif item.type == openai_models.ItemType.FUNCTION_CALL_OUTPUT:
            return ToolMessage(content=item.output, tool_call_id=item.call_id)
        else:
            raise ValueError(f"Unsupported OpenAIItemParam type: {item.type}, {item}")
