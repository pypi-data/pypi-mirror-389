import copy
from typing import List

from langchain_core import messages
from langchain_core.messages import AnyMessage

from ...logger import get_logger
from ...models.openai import models as openai_models
from ..common.agent_run_context import AgentRunContext
from .utils import extract_function_call

logger = get_logger()


class LangGraphResponseConverter:
    def __init__(self, context: AgentRunContext, output):
        self.context = context
        self.output = output

    def convert(self) -> openai_models.ItemResource:
        res = []
        for step in self.output:
            for node_name, node_output in step.items():
                messages = node_output.get("messages")
                if not messages:
                    logger.warning(f"No messages found in node {node_name} output: {node_output}")
                    continue
                for message in messages:
                    try:
                        converted = self.convert_output_message(message)
                        res.append(converted)
                    except Exception as e:
                        logger.error(f"Error converting message {message}: {e}")
        return res

    def convert_output_message(self, output_message: AnyMessage) -> openai_models.ItemResource:
        # Implement the conversion logic for inner inputs
        if isinstance(output_message, messages.HumanMessage):
            return openai_models.ResponsesUserMessageItemResource(
                content=self.convert_MessageContent(
                    output_message.content, role=openai_models.ResponsesMessageRole.USER
                ),
                id=self.context.id_generator.generate_message_id(),
                status="completed",  # temporary status, can be adjusted based on actual logic
            )
        if isinstance(output_message, messages.SystemMessage):
            return openai_models.ResponsesSystemMessageItemResource(
                content=self.convert_MessageContent(
                    output_message.content, role=openai_models.ResponsesMessageRole.SYSTEM
                ),
                id=self.context.id_generator.generate_message_id(),
                status="completed",
            )
        if isinstance(output_message, messages.AIMessage):
            if output_message.tool_calls:
                # If there are tool calls, we assume there is only ONE function call
                if len(output_message.tool_calls) > 1:
                    logger.warning(
                        f"There are {len(output_message.tool_calls)} tool calls found. "
                        + "Only the first one will be processed."
                    )
                tool_call = output_message.tool_calls[0]
                name, call_id, argument = extract_function_call(tool_call)
                return openai_models.FunctionToolCallItemResource(
                    call_id=call_id,
                    name=name,
                    arguments=argument,
                    id=self.context.id_generator.generate_function_call_id(),
                    status="completed",
                )
            return openai_models.ResponsesAssistantMessageItemResource(
                content=self.convert_MessageContent(
                    output_message.content, role=openai_models.ResponsesMessageRole.ASSISTANT
                ),
                id=self.context.id_generator.generate_message_id(),
                status="completed",
            )
        if isinstance(output_message, messages.ToolMessage):
            return openai_models.FunctionToolCallOutputItemResource(
                call_id=output_message.tool_call_id,
                output=output_message.content,
                id=self.context.id_generator.generate_function_output_id(),
            )

    def convert_MessageContent(
        self, content: str | list[str | dict], role: openai_models.ResponsesMessageRole
    ) -> List[openai_models.ItemContent]:
        if isinstance(content, str):
            return [self.convert_MessageContentItem(content, role)]
        return [self.convert_MessageContentItem(item, role) for item in content]

    def convert_MessageContentItem(
        self, content: str | dict, role: openai_models.ResponsesMessageRole
    ) -> openai_models.ItemContent:
        content_dict = copy.deepcopy(content) if isinstance(content, dict) else {"text": content}

        content_type = None
        if isinstance(content, str):
            langgraph_content_type = "text"
        else:
            langgraph_content_type = content.get("type", "text")

        if langgraph_content_type == "text":
            if role == openai_models.ResponsesMessageRole.ASSISTANT:
                content_type = openai_models.ItemContentType.OUTPUT_TEXT
            else:
                content_type = openai_models.ItemContentType.INPUT_TEXT
        elif langgraph_content_type == "image":
            if role == openai_models.ResponsesMessageRole.USER:
                content_type = openai_models.ItemContentType.INPUT_IMAGE
            else:
                raise ValueError("Image content from assistant is not supported")
        elif langgraph_content_type == "audio":
            if role == openai_models.ResponsesMessageRole.USER:
                content_type = openai_models.ItemContentType.INPUT_AUDIO
            else:
                content_type = openai_models.ItemContentType.OUTPUT_AUDIO
        elif langgraph_content_type == "file":
            if role == openai_models.ResponsesMessageRole.USER:
                content_type = openai_models.ItemContentType.INPUT_FILE
            else:
                raise ValueError("File content from assistant is not supported")
        else:
            raise ValueError(f"Unsupported content: {content}")

        content_dict["type"] = content_type
        if content_type == openai_models.ItemContentType.OUTPUT_TEXT:
            content_dict["annotations"] = []  # annotation is required for output_text

        return openai_models.ItemContent(content_dict)
