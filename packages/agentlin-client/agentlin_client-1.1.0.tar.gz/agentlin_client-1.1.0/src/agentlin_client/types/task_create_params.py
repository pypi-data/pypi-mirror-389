# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "TaskCreateParams",
    "UserMessageContent",
    "UserMessageContentTextContent",
    "UserMessageContentImageURLContent",
    "UserMessageContentImageURLContentImageURL",
    "UserMessageContentInputAudioContent",
    "UserMessageContentInputAudioContentInputAudio",
    "UserMessageContentFileContent",
    "UserMessageContentFileContentFile",
    "AgentConfig",
    "AgentConfigBuiltinTool",
    "AgentConfigBuiltinToolFunction",
    "ClientTool",
    "ClientToolFunction",
    "HistoryMessage",
    "HistoryMessageContentUnionMember1",
    "HistoryMessageContentUnionMember1TextContent",
    "HistoryMessageContentUnionMember1ImageURLContent",
    "HistoryMessageContentUnionMember1ImageURLContentImageURL",
    "HistoryMessageContentUnionMember1InputAudioContent",
    "HistoryMessageContentUnionMember1InputAudioContentInputAudio",
    "HistoryMessageContentUnionMember1FileContent",
    "HistoryMessageContentUnionMember1FileContentFile",
    "ThoughtMessage",
    "ThoughtMessageContentUnionMember1",
    "ThoughtMessageContentUnionMember1TextContent",
    "ThoughtMessageContentUnionMember1ImageURLContent",
    "ThoughtMessageContentUnionMember1ImageURLContentImageURL",
    "ThoughtMessageContentUnionMember1InputAudioContent",
    "ThoughtMessageContentUnionMember1InputAudioContentInputAudio",
    "ThoughtMessageContentUnionMember1FileContent",
    "ThoughtMessageContentUnionMember1FileContentFile",
]


class TaskCreateParams(TypedDict, total=False):
    stream: Required[bool]
    """是否启用流式（SSE）返回；true 则以 text/event-stream 推送 Task 事件。"""

    user_message_content: Required[Iterable[UserMessageContent]]
    """当前用户输入内容（多模态），按顺序提供给主 Agent。"""

    agent_config: AgentConfig
    """指定主 Agent 的配置；为空则按 client_id 推断默认 Agent。"""

    allowed_subagents: SequenceNotStr[str]
    """允许使用的子代理白名单；为 null 允许全部，空数组禁止所有。"""

    allowed_tools: SequenceNotStr[str]
    """允许使用的工具白名单；为 null 允许全部，空数组表示禁止所有。"""

    client_id: str
    """调用方客户端标识（如 AIME）。"""

    client_tools: Iterable[ClientTool]
    """客户端自带工具定义；命中后会停止由服务端执行，等待客户端完成。"""

    disallowed_tools: SequenceNotStr[str]
    """禁用的工具黑名单；为 null 或空数组不生效。"""

    env: Dict[str, str]
    """Agent 的运行时环境变量键值对。"""

    history_messages: Iterable[HistoryMessage]
    """历史对话消息，用于提供上下文。"""

    include_compress_model_rollout: bool
    """是否包含上下文压缩模型的 rollout 结果。"""

    include_subagent_rollout: bool
    """是否包含子 Agent 的 rollout 结果。"""

    inference_args: Dict[str, object]
    """推理参数覆盖项（如温度、最大 tokens 等），具体字段由后端实现决定。"""

    log_dir: str
    """日志输出目录。"""

    request_id: str
    """请求链路唯一 ID；便于将复杂调用串联在一起。"""

    return_rollout: bool
    """是否在最终结果中返回 rollout 事件集合。"""

    rollout_save_dir: str
    """回溯（rollout）结果保存目录。"""

    session_id: str
    """会话 ID；用于跨多轮交互复用上下文。"""

    stop_tools: SequenceNotStr[str]
    """命中则停止代理循环的工具名列表；为 null 或空数组不生效。"""

    structured_output: Dict[str, object]
    """期望的结构化输出 JSON Schema；仅非流式模式有效，流式模式下将被忽略。"""

    task_id: str
    """任务 ID；用于区分主任务与子任务。"""

    thought_messages: Iterable[ThoughtMessage]
    """隐藏的助手思考内容（不可见思考轨迹），如有将并入上下文。"""

    user_id: str
    """终端用户 ID。"""

    workspace_dir: str
    """文件系统工作目录；供文件工具与代码解释器使用。"""


class UserMessageContentTextContent(TypedDict, total=False):
    text: Required[str]
    """文本内容。"""

    type: Required[Literal["text", "input_text"]]
    """文本内容类型标识。"""


class UserMessageContentImageURLContentImageURL(TypedDict, total=False):
    url: Required[str]
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]]
    """清晰度等级，可选 low/high/auto。"""


class UserMessageContentImageURLContent(TypedDict, total=False):
    image_url: Required[UserMessageContentImageURLContentImageURL]
    """图片 URL 及清晰度参数。"""

    type: Required[Literal["image_url", "image"]]
    """图片内容类型标识。"""


class UserMessageContentInputAudioContentInputAudio(TypedDict, total=False):
    data: Required[str]
    """Base64-encoded audio bytes"""

    format: Required[Literal["wav", "mp3"]]


class UserMessageContentInputAudioContent(TypedDict, total=False):
    input_audio: Required[UserMessageContentInputAudioContentInputAudio]
    """输入音频内容（Base64 编码）。"""

    type: Required[Literal["input_audio"]]
    """音频内容类型标识。"""


class UserMessageContentFileContentFile(TypedDict, total=False):
    file_url: Required[str]
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: Required[str]
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: str
    """Optional Base64-encoded file content"""


class UserMessageContentFileContent(TypedDict, total=False):
    file: Required[UserMessageContentFileContentFile]
    """文件详情（URL/文件名/可选 Base64 内容）。"""

    type: Required[Literal["file"]]
    """文件内容类型标识。"""


UserMessageContent: TypeAlias = Union[
    UserMessageContentTextContent,
    UserMessageContentImageURLContent,
    UserMessageContentInputAudioContent,
    UserMessageContentFileContent,
]


class AgentConfigBuiltinToolFunction(TypedDict, total=False):
    name: Required[str]
    """工具/函数名称（唯一标识）。"""

    parameters: Required[Dict[str, object]]
    """JSON Schema for the function parameters."""

    description: str
    """函数的用途说明。"""

    strict: bool
    """是否启用严格参数校验。"""


class AgentConfigBuiltinTool(TypedDict, total=False):
    function: Required[AgentConfigBuiltinToolFunction]
    """函数工具定义（名称/参数/描述）。"""

    type: Required[Literal["function"]]
    """工具类型，此处固定为 function。"""


class AgentConfig(TypedDict, total=False):
    agent_id: Required[str]
    """Agent 唯一标识（目录名）。"""

    code_for_agent: Required[str]
    """注入到 Agent 侧的代码片段。"""

    code_for_interpreter: Required[str]
    """注入到代码解释器侧的代码片段。"""

    description: Required[str]
    """Agent 描述。"""

    developer_prompt: Required[str]
    """主系统提示词（开发者指令）。"""

    max_model_length: Required[int]
    """模型上下文最大 tokens。"""

    max_response_length: Required[int]
    """模型生成的最大 tokens。"""

    model: Required[str]
    """主模型名称。"""

    name: Required[str]
    """Agent 名称。"""

    allowed_tools: SequenceNotStr[str]
    """默认允许使用的工具。"""

    builtin_subagents: Iterable[object]
    """内置子代理列表（名称/工具/提示词等）。"""

    builtin_tools: Iterable[AgentConfigBuiltinTool]
    """内置工具集合（含 CodeInterpreter/Task 等）。"""

    code_interpreter_config: Dict[str, object]
    """代码解释器连接配置（Jupyter）。"""

    compress_model: str
    """用于压缩上下文的模型名称。"""

    compress_prompt: str
    """上下文压缩时使用的系统提示词。"""

    compress_threshold_token_ratio: float
    """触发上下文压缩的 token 比例阈值。"""

    inference_args: Dict[str, object]
    """默认推理参数覆盖项。"""

    tool_mcp_config: Dict[str, object]
    """MCP 服务器配置（工具来源）。"""


class ClientToolFunction(TypedDict, total=False):
    name: Required[str]
    """工具/函数名称（唯一标识）。"""

    parameters: Required[Dict[str, object]]
    """JSON Schema for the function parameters."""

    description: str
    """函数的用途说明。"""

    strict: bool
    """是否启用严格参数校验。"""


class ClientTool(TypedDict, total=False):
    function: Required[ClientToolFunction]
    """函数工具定义（名称/参数/描述）。"""

    type: Required[Literal["function"]]
    """工具类型，此处固定为 function。"""


class HistoryMessageContentUnionMember1TextContent(TypedDict, total=False):
    text: Required[str]
    """文本内容。"""

    type: Required[Literal["text", "input_text"]]
    """文本内容类型标识。"""


class HistoryMessageContentUnionMember1ImageURLContentImageURL(TypedDict, total=False):
    url: Required[str]
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]]
    """清晰度等级，可选 low/high/auto。"""


class HistoryMessageContentUnionMember1ImageURLContent(TypedDict, total=False):
    image_url: Required[HistoryMessageContentUnionMember1ImageURLContentImageURL]
    """图片 URL 及清晰度参数。"""

    type: Required[Literal["image_url", "image"]]
    """图片内容类型标识。"""


class HistoryMessageContentUnionMember1InputAudioContentInputAudio(TypedDict, total=False):
    data: Required[str]
    """Base64-encoded audio bytes"""

    format: Required[Literal["wav", "mp3"]]


class HistoryMessageContentUnionMember1InputAudioContent(TypedDict, total=False):
    input_audio: Required[HistoryMessageContentUnionMember1InputAudioContentInputAudio]
    """输入音频内容（Base64 编码）。"""

    type: Required[Literal["input_audio"]]
    """音频内容类型标识。"""


class HistoryMessageContentUnionMember1FileContentFile(TypedDict, total=False):
    file_url: Required[str]
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: Required[str]
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: str
    """Optional Base64-encoded file content"""


class HistoryMessageContentUnionMember1FileContent(TypedDict, total=False):
    file: Required[HistoryMessageContentUnionMember1FileContentFile]
    """文件详情（URL/文件名/可选 Base64 内容）。"""

    type: Required[Literal["file"]]
    """文件内容类型标识。"""


HistoryMessageContentUnionMember1: TypeAlias = Union[
    HistoryMessageContentUnionMember1TextContent,
    HistoryMessageContentUnionMember1ImageURLContent,
    HistoryMessageContentUnionMember1InputAudioContent,
    HistoryMessageContentUnionMember1FileContent,
]


class HistoryMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[HistoryMessageContentUnionMember1]]]
    """消息内容，字符串或多模态内容数组。"""

    role: Required[Literal["user", "assistant", "system", "developer"]]
    """角色。"""

    name: str
    """可选的角色名称。"""


class ThoughtMessageContentUnionMember1TextContent(TypedDict, total=False):
    text: Required[str]
    """文本内容。"""

    type: Required[Literal["text", "input_text"]]
    """文本内容类型标识。"""


class ThoughtMessageContentUnionMember1ImageURLContentImageURL(TypedDict, total=False):
    url: Required[str]
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]]
    """清晰度等级，可选 low/high/auto。"""


class ThoughtMessageContentUnionMember1ImageURLContent(TypedDict, total=False):
    image_url: Required[ThoughtMessageContentUnionMember1ImageURLContentImageURL]
    """图片 URL 及清晰度参数。"""

    type: Required[Literal["image_url", "image"]]
    """图片内容类型标识。"""


class ThoughtMessageContentUnionMember1InputAudioContentInputAudio(TypedDict, total=False):
    data: Required[str]
    """Base64-encoded audio bytes"""

    format: Required[Literal["wav", "mp3"]]


class ThoughtMessageContentUnionMember1InputAudioContent(TypedDict, total=False):
    input_audio: Required[ThoughtMessageContentUnionMember1InputAudioContentInputAudio]
    """输入音频内容（Base64 编码）。"""

    type: Required[Literal["input_audio"]]
    """音频内容类型标识。"""


class ThoughtMessageContentUnionMember1FileContentFile(TypedDict, total=False):
    file_url: Required[str]
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: Required[str]
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: str
    """Optional Base64-encoded file content"""


class ThoughtMessageContentUnionMember1FileContent(TypedDict, total=False):
    file: Required[ThoughtMessageContentUnionMember1FileContentFile]
    """文件详情（URL/文件名/可选 Base64 内容）。"""

    type: Required[Literal["file"]]
    """文件内容类型标识。"""


ThoughtMessageContentUnionMember1: TypeAlias = Union[
    ThoughtMessageContentUnionMember1TextContent,
    ThoughtMessageContentUnionMember1ImageURLContent,
    ThoughtMessageContentUnionMember1InputAudioContent,
    ThoughtMessageContentUnionMember1FileContent,
]


class ThoughtMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[ThoughtMessageContentUnionMember1]]]
    """消息内容，字符串或多模态内容数组。"""

    role: Required[Literal["user", "assistant", "system", "developer"]]
    """角色。"""

    name: str
    """可选的角色名称。"""
