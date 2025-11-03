# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import builtins
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = [
    "TaskCancelResponse",
    "Error",
    "Result",
    "ResultOutput",
    "ResultOutputReasoningItem",
    "ResultOutputReasoningItemSummary",
    "ResultOutputReasoningItemSummaryAnnotation",
    "ResultOutputReasoningItemSummaryAnnotationFileCitation",
    "ResultOutputReasoningItemSummaryAnnotationURLCitation",
    "ResultOutputReasoningItemSummaryAnnotationContainerFileCitation",
    "ResultOutputReasoningItemSummaryAnnotationFilePath",
    "ResultOutputReasoningItemSummaryLogprob",
    "ResultOutputReasoningItemSummaryLogprobTopLogprob",
    "ResultOutputReasoningItemContent",
    "ResultOutputReasoningItemContentAnnotation",
    "ResultOutputReasoningItemContentAnnotationFileCitation",
    "ResultOutputReasoningItemContentAnnotationURLCitation",
    "ResultOutputReasoningItemContentAnnotationContainerFileCitation",
    "ResultOutputReasoningItemContentAnnotationFilePath",
    "ResultOutputReasoningItemContentLogprob",
    "ResultOutputReasoningItemContentLogprobTopLogprob",
    "ResultOutputMessageItem",
    "ResultOutputMessageItemContentUnionMember1",
    "ResultOutputMessageItemContentUnionMember1TextContentItem",
    "ResultOutputMessageItemContentUnionMember1TextContentItemAnnotation",
    "ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFileCitation",
    "ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationURLCitation",
    "ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationContainerFileCitation",
    "ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFilePath",
    "ResultOutputMessageItemContentUnionMember1TextContentItemLogprob",
    "ResultOutputMessageItemContentUnionMember1TextContentItemLogprobTopLogprob",
    "ResultOutputMessageItemContentUnionMember1ImageContentItem",
    "ResultOutputMessageItemContentUnionMember1ImageContentItemImageURL",
    "ResultOutputMessageItemContentUnionMember1AudioContentItem",
    "ResultOutputMessageItemContentUnionMember1AudioContentItemInputAudio",
    "ResultOutputMessageItemContentUnionMember1FileContentItem",
    "ResultOutputMessageItemContentUnionMember1FileContentItemFile",
    "ResultOutputToolCallItem",
    "ResultOutputToolResultItem",
    "ResultOutputToolResultItemOutputUnionMember1",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItem",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotation",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFileCitation",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationURLCitation",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationContainerFileCitation",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFilePath",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprob",
    "ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprobTopLogprob",
    "ResultOutputToolResultItemOutputUnionMember1ImageContentItem",
    "ResultOutputToolResultItemOutputUnionMember1ImageContentItemImageURL",
    "ResultOutputToolResultItemOutputUnionMember1AudioContentItem",
    "ResultOutputToolResultItemOutputUnionMember1AudioContentItemInputAudio",
    "ResultOutputToolResultItemOutputUnionMember1FileContentItem",
    "ResultOutputToolResultItemOutputUnionMember1FileContentItemFile",
    "ResultError",
    "ResultInputRequired",
]


class Error(BaseModel):
    code: int
    """错误码（遵循 JSON-RPC 约定或服务端自定义）。"""

    message: str
    """错误信息。"""

    data: Union[List[object], str, float, bool, object, None] = None
    """自定义错误数据，任意 JSON 值或 null。"""


class ResultOutputReasoningItemSummaryAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class ResultOutputReasoningItemSummaryAnnotationURLCitation(BaseModel):
    end_index: int
    """The index of the last character of the URL citation in the message."""

    start_index: int
    """The index of the first character of the URL citation in the message."""

    title: str
    """The title of the web resource."""

    type: Literal["url_citation"]
    """The type of the URL citation. Always `url_citation`."""

    url: str
    """The URL of the web resource."""


class ResultOutputReasoningItemSummaryAnnotationContainerFileCitation(BaseModel):
    container_id: str
    """The ID of the container file."""

    end_index: int
    """The index of the last character of the container file citation in the message."""

    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the container file cited."""

    start_index: int
    """The index of the first character of the container file citation in the message."""

    type: Literal["container_file_citation"]
    """The type of the container file citation. Always `container_file_citation`."""


class ResultOutputReasoningItemSummaryAnnotationFilePath(BaseModel):
    file_url: str
    """The URL of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file citation. Always `file_path`."""


ResultOutputReasoningItemSummaryAnnotation: TypeAlias = Annotated[
    Union[
        ResultOutputReasoningItemSummaryAnnotationFileCitation,
        ResultOutputReasoningItemSummaryAnnotationURLCitation,
        ResultOutputReasoningItemSummaryAnnotationContainerFileCitation,
        ResultOutputReasoningItemSummaryAnnotationFilePath,
    ],
    PropertyInfo(discriminator="type"),
]


class ResultOutputReasoningItemSummaryLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class ResultOutputReasoningItemSummaryLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[ResultOutputReasoningItemSummaryLogprobTopLogprob]


class ResultOutputReasoningItemSummary(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]
    """文本内容类型。"""

    id: Optional[int] = None
    """可选的内容引用 ID。"""

    annotations: Optional[List[ResultOutputReasoningItemSummaryAnnotation]] = None
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Optional[List[ResultOutputReasoningItemSummaryLogprob]] = None
    """每个 token 的对数概率信息（可选）。"""

    tags: Optional[List[str]] = None
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""


class ResultOutputReasoningItemContentAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class ResultOutputReasoningItemContentAnnotationURLCitation(BaseModel):
    end_index: int
    """The index of the last character of the URL citation in the message."""

    start_index: int
    """The index of the first character of the URL citation in the message."""

    title: str
    """The title of the web resource."""

    type: Literal["url_citation"]
    """The type of the URL citation. Always `url_citation`."""

    url: str
    """The URL of the web resource."""


class ResultOutputReasoningItemContentAnnotationContainerFileCitation(BaseModel):
    container_id: str
    """The ID of the container file."""

    end_index: int
    """The index of the last character of the container file citation in the message."""

    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the container file cited."""

    start_index: int
    """The index of the first character of the container file citation in the message."""

    type: Literal["container_file_citation"]
    """The type of the container file citation. Always `container_file_citation`."""


class ResultOutputReasoningItemContentAnnotationFilePath(BaseModel):
    file_url: str
    """The URL of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file citation. Always `file_path`."""


ResultOutputReasoningItemContentAnnotation: TypeAlias = Annotated[
    Union[
        ResultOutputReasoningItemContentAnnotationFileCitation,
        ResultOutputReasoningItemContentAnnotationURLCitation,
        ResultOutputReasoningItemContentAnnotationContainerFileCitation,
        ResultOutputReasoningItemContentAnnotationFilePath,
    ],
    PropertyInfo(discriminator="type"),
]


class ResultOutputReasoningItemContentLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class ResultOutputReasoningItemContentLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[ResultOutputReasoningItemContentLogprobTopLogprob]


class ResultOutputReasoningItemContent(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]
    """文本内容类型。"""

    id: Optional[int] = None
    """可选的内容引用 ID。"""

    annotations: Optional[List[ResultOutputReasoningItemContentAnnotation]] = None
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Optional[List[ResultOutputReasoningItemContentLogprob]] = None
    """每个 token 的对数概率信息（可选）。"""

    tags: Optional[List[str]] = None
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""


class ResultOutputReasoningItem(BaseModel):
    id: str
    """推理项 ID。"""

    summary: List[ResultOutputReasoningItemSummary]
    """推理摘要内容（结构化）。"""

    type: Literal["reasoning"]
    """推理项类型标识。"""

    content: Optional[List[ResultOutputReasoningItemContent]] = None
    """推理详细内容（可选）。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """状态。"""


class ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationURLCitation(BaseModel):
    end_index: int
    """The index of the last character of the URL citation in the message."""

    start_index: int
    """The index of the first character of the URL citation in the message."""

    title: str
    """The title of the web resource."""

    type: Literal["url_citation"]
    """The type of the URL citation. Always `url_citation`."""

    url: str
    """The URL of the web resource."""


class ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationContainerFileCitation(BaseModel):
    container_id: str
    """The ID of the container file."""

    end_index: int
    """The index of the last character of the container file citation in the message."""

    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the container file cited."""

    start_index: int
    """The index of the first character of the container file citation in the message."""

    type: Literal["container_file_citation"]
    """The type of the container file citation. Always `container_file_citation`."""


class ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFilePath(BaseModel):
    file_url: str
    """The URL of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file citation. Always `file_path`."""


ResultOutputMessageItemContentUnionMember1TextContentItemAnnotation: TypeAlias = Annotated[
    Union[
        ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFileCitation,
        ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationURLCitation,
        ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationContainerFileCitation,
        ResultOutputMessageItemContentUnionMember1TextContentItemAnnotationFilePath,
    ],
    PropertyInfo(discriminator="type"),
]


class ResultOutputMessageItemContentUnionMember1TextContentItemLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class ResultOutputMessageItemContentUnionMember1TextContentItemLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[ResultOutputMessageItemContentUnionMember1TextContentItemLogprobTopLogprob]


class ResultOutputMessageItemContentUnionMember1TextContentItem(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]
    """文本内容类型。"""

    id: Optional[int] = None
    """可选的内容引用 ID。"""

    annotations: Optional[List[ResultOutputMessageItemContentUnionMember1TextContentItemAnnotation]] = None
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Optional[List[ResultOutputMessageItemContentUnionMember1TextContentItemLogprob]] = None
    """每个 token 的对数概率信息（可选）。"""

    tags: Optional[List[str]] = None
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""


class ResultOutputMessageItemContentUnionMember1ImageContentItemImageURL(BaseModel):
    url: str
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]] = None
    """清晰度等级，可选 low/high/auto。"""


class ResultOutputMessageItemContentUnionMember1ImageContentItem(BaseModel):
    image_url: ResultOutputMessageItemContentUnionMember1ImageContentItemImageURL
    """图片 URL 信息。"""

    type: Literal["image", "input_image", "output_image", "image_url"]
    """图片内容类型。"""


class ResultOutputMessageItemContentUnionMember1AudioContentItemInputAudio(BaseModel):
    data: str
    """Base64-encoded audio bytes"""

    format: Literal["wav", "mp3"]


class ResultOutputMessageItemContentUnionMember1AudioContentItem(BaseModel):
    input_audio: ResultOutputMessageItemContentUnionMember1AudioContentItemInputAudio
    """输入音频内容。"""

    type: Literal["input_audio", "output_audio", "audio"]
    """音频内容类型。"""


class ResultOutputMessageItemContentUnionMember1FileContentItemFile(BaseModel):
    file_url: str
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: str
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: Optional[str] = None
    """Optional Base64-encoded file content"""


class ResultOutputMessageItemContentUnionMember1FileContentItem(BaseModel):
    file: ResultOutputMessageItemContentUnionMember1FileContentItemFile
    """文件详情。"""

    type: Literal["file"]
    """文件内容类型。"""


ResultOutputMessageItemContentUnionMember1: TypeAlias = Union[
    ResultOutputMessageItemContentUnionMember1TextContentItem,
    ResultOutputMessageItemContentUnionMember1ImageContentItem,
    ResultOutputMessageItemContentUnionMember1AudioContentItem,
    ResultOutputMessageItemContentUnionMember1FileContentItem,
    str,
]


class ResultOutputMessageItem(BaseModel):
    content: Union[str, List[ResultOutputMessageItemContentUnionMember1]]
    """消息内容，字符串或内容项数组。"""

    role: Literal["user", "assistant", "system", "developer"]
    """消息角色。"""

    type: Literal["message"]
    """消息条目类型标识。"""

    id: Optional[str] = None
    """消息 ID。"""

    block_list: Optional[List[object]] = None
    """渲染块列表（图表/表格等富媒体）。"""

    message_content: Optional[List[object]] = None
    """工具协议兼容的 message_content（保留字段）。"""

    name: Optional[str] = None
    """角色名称（可选）。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """消息生成状态。"""


class ResultOutputToolCallItem(BaseModel):
    arguments: str
    """工具调用参数（JSON 字符串）。"""

    call_id: str
    """工具调用唯一 ID（跨事件关联）。"""

    name: str
    """工具名称。"""

    type: Literal["tool_call"]
    """工具调用条目类型标识。"""

    id: Optional[str] = None
    """工具调用条目 ID。"""

    language: Optional[Literal["json", "yaml", "python", "javascript"]] = None
    """参数语言标注（可选）。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """调用状态。"""


class ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationURLCitation(BaseModel):
    end_index: int
    """The index of the last character of the URL citation in the message."""

    start_index: int
    """The index of the first character of the URL citation in the message."""

    title: str
    """The title of the web resource."""

    type: Literal["url_citation"]
    """The type of the URL citation. Always `url_citation`."""

    url: str
    """The URL of the web resource."""


class ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationContainerFileCitation(BaseModel):
    container_id: str
    """The ID of the container file."""

    end_index: int
    """The index of the last character of the container file citation in the message."""

    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the container file cited."""

    start_index: int
    """The index of the first character of the container file citation in the message."""

    type: Literal["container_file_citation"]
    """The type of the container file citation. Always `container_file_citation`."""


class ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFilePath(BaseModel):
    file_url: str
    """The URL of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file citation. Always `file_path`."""


ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotation: TypeAlias = Annotated[
    Union[
        ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFileCitation,
        ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationURLCitation,
        ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationContainerFileCitation,
        ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotationFilePath,
    ],
    PropertyInfo(discriminator="type"),
]


class ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprobTopLogprob]


class ResultOutputToolResultItemOutputUnionMember1TextContentItem(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]
    """文本内容类型。"""

    id: Optional[int] = None
    """可选的内容引用 ID。"""

    annotations: Optional[List[ResultOutputToolResultItemOutputUnionMember1TextContentItemAnnotation]] = None
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Optional[List[ResultOutputToolResultItemOutputUnionMember1TextContentItemLogprob]] = None
    """每个 token 的对数概率信息（可选）。"""

    tags: Optional[List[str]] = None
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""


class ResultOutputToolResultItemOutputUnionMember1ImageContentItemImageURL(BaseModel):
    url: str
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]] = None
    """清晰度等级，可选 low/high/auto。"""


class ResultOutputToolResultItemOutputUnionMember1ImageContentItem(BaseModel):
    image_url: ResultOutputToolResultItemOutputUnionMember1ImageContentItemImageURL
    """图片 URL 信息。"""

    type: Literal["image", "input_image", "output_image", "image_url"]
    """图片内容类型。"""


class ResultOutputToolResultItemOutputUnionMember1AudioContentItemInputAudio(BaseModel):
    data: str
    """Base64-encoded audio bytes"""

    format: Literal["wav", "mp3"]


class ResultOutputToolResultItemOutputUnionMember1AudioContentItem(BaseModel):
    input_audio: ResultOutputToolResultItemOutputUnionMember1AudioContentItemInputAudio
    """输入音频内容。"""

    type: Literal["input_audio", "output_audio", "audio"]
    """音频内容类型。"""


class ResultOutputToolResultItemOutputUnionMember1FileContentItemFile(BaseModel):
    file_url: str
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: str
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: Optional[str] = None
    """Optional Base64-encoded file content"""


class ResultOutputToolResultItemOutputUnionMember1FileContentItem(BaseModel):
    file: ResultOutputToolResultItemOutputUnionMember1FileContentItemFile
    """文件详情。"""

    type: Literal["file"]
    """文件内容类型。"""


ResultOutputToolResultItemOutputUnionMember1: TypeAlias = Union[
    ResultOutputToolResultItemOutputUnionMember1TextContentItem,
    ResultOutputToolResultItemOutputUnionMember1ImageContentItem,
    ResultOutputToolResultItemOutputUnionMember1AudioContentItem,
    ResultOutputToolResultItemOutputUnionMember1FileContentItem,
    str,
]


class ResultOutputToolResultItem(BaseModel):
    block_list: List[object]
    """工具结果的渲染块列表。"""

    call_id: str
    """对应的工具调用 ID。"""

    message_content: List[object]
    """工具结果的 message_content（用于富文本/富媒体渲染）。"""

    type: Literal["tool_result"]
    """工具结果条目类型标识。"""

    id: Optional[str] = None
    """工具结果条目 ID。"""

    output: Union[str, List[ResultOutputToolResultItemOutputUnionMember1], None] = None
    """以字符串或内容数组形式返回的工具输出。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """结果状态。"""


ResultOutput: TypeAlias = Union[
    ResultOutputReasoningItem, ResultOutputMessageItem, ResultOutputToolCallItem, ResultOutputToolResultItem
]


class ResultError(BaseModel):
    code: int
    """错误码（遵循 JSON-RPC 约定或服务端自定义）。"""

    message: str
    """错误信息。"""

    data: Union[List[object], str, float, bool, object, None] = None
    """自定义错误数据，任意 JSON 值或 null。"""


class ResultInputRequired(BaseModel):
    arguments: str
    """工具调用参数（JSON 字符串）。"""

    call_id: str
    """工具调用唯一 ID（跨事件关联）。"""

    name: str
    """工具名称。"""

    type: Literal["tool_call"]
    """工具调用条目类型标识。"""

    id: Optional[str] = None
    """工具调用条目 ID。"""

    language: Optional[Literal["json", "yaml", "python", "javascript"]] = None
    """参数语言标注（可选）。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """调用状态。"""


class Result(BaseModel):
    id: str
    """任务 ID。"""

    created_at: int
    """任务创建时间（Unix 秒）。"""

    object: Literal["task"]
    """固定为 task。"""

    output: List[ResultOutput]
    """模型/代理生成的输出条目集合（多类型）。"""

    session_id: str
    """会话 ID。"""

    status: Literal[
        "created", "queued", "working", "input-required", "paused", "completed", "canceled", "expired", "failed"
    ]
    """任务状态。"""

    user_id: str
    """用户 ID。"""

    error: Optional[ResultError] = None
    """错误信息（失败时）。"""

    input_required: Optional[ResultInputRequired] = None
    """若任务等待外部输入，则给出需要执行的工具调用（如等待用户参数）。"""

    metadata: Optional[Dict[str, builtins.object]] = None
    """扩展元数据。"""

    previous_task_id: Optional[str] = None
    """前置任务 ID（用于续写/衔接）。"""

    rollouts: Optional[List[Dict[str, builtins.object]]] = None
    """任务推演/回溯事件集合（可选）。"""

    usage: Optional[Dict[str, builtins.object]] = None
    """token 用量统计信息。"""


class TaskCancelResponse(BaseModel):
    jsonrpc: Literal["2.0"]
    """JSON-RPC protocol version, always '2.0'."""

    id: Union[str, int, None] = None
    """请求/响应 ID，由客户端生成或服务器透传；可为字符串、整数或 null。"""

    error: Optional[Error] = None
    """JSON-RPC 错误对象（如失败时）。"""

    result: Optional[Result] = None
    """JSON-RPC result：任务对象。"""
