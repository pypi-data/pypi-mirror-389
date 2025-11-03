# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from .._models import BaseModel
from .text_content_item import TextContentItem

__all__ = [
    "ToolResultItem",
    "MessageContentUnionMember1",
    "MessageContentUnionMember1TextContent",
    "MessageContentUnionMember1ImageURLContent",
    "MessageContentUnionMember1ImageURLContentImageURL",
    "MessageContentUnionMember1InputAudioContent",
    "MessageContentUnionMember1InputAudioContentInputAudio",
    "MessageContentUnionMember1FileContent",
    "MessageContentUnionMember1FileContentFile",
    "OutputUnionMember1",
    "OutputUnionMember1ImageContentItem",
    "OutputUnionMember1ImageContentItemImageURL",
    "OutputUnionMember1AudioContentItem",
    "OutputUnionMember1AudioContentItemInputAudio",
    "OutputUnionMember1FileContentItem",
    "OutputUnionMember1FileContentItemFile",
]


class MessageContentUnionMember1TextContent(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text"]
    """文本内容类型标识。"""


class MessageContentUnionMember1ImageURLContentImageURL(BaseModel):
    url: str
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]] = None
    """清晰度等级，可选 low/high/auto。"""


class MessageContentUnionMember1ImageURLContent(BaseModel):
    image_url: MessageContentUnionMember1ImageURLContentImageURL
    """图片 URL 及清晰度参数。"""

    type: Literal["image_url", "image"]
    """图片内容类型标识。"""


class MessageContentUnionMember1InputAudioContentInputAudio(BaseModel):
    data: str
    """Base64-encoded audio bytes"""

    format: Literal["wav", "mp3"]


class MessageContentUnionMember1InputAudioContent(BaseModel):
    input_audio: MessageContentUnionMember1InputAudioContentInputAudio
    """输入音频内容（Base64 编码）。"""

    type: Literal["input_audio"]
    """音频内容类型标识。"""


class MessageContentUnionMember1FileContentFile(BaseModel):
    file_url: str
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: str
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: Optional[str] = None
    """Optional Base64-encoded file content"""


class MessageContentUnionMember1FileContent(BaseModel):
    file: MessageContentUnionMember1FileContentFile
    """文件详情（URL/文件名/可选 Base64 内容）。"""

    type: Literal["file"]
    """文件内容类型标识。"""


MessageContentUnionMember1: TypeAlias = Union[
    MessageContentUnionMember1TextContent,
    MessageContentUnionMember1ImageURLContent,
    MessageContentUnionMember1InputAudioContent,
    MessageContentUnionMember1FileContent,
]


class OutputUnionMember1ImageContentItemImageURL(BaseModel):
    url: str
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]] = None
    """清晰度等级，可选 low/high/auto。"""


class OutputUnionMember1ImageContentItem(BaseModel):
    image_url: OutputUnionMember1ImageContentItemImageURL
    """图片 URL 信息。"""

    type: Literal["image", "input_image", "output_image", "image_url"]
    """图片内容类型。"""


class OutputUnionMember1AudioContentItemInputAudio(BaseModel):
    data: str
    """Base64-encoded audio bytes"""

    format: Literal["wav", "mp3"]


class OutputUnionMember1AudioContentItem(BaseModel):
    input_audio: OutputUnionMember1AudioContentItemInputAudio
    """输入音频内容。"""

    type: Literal["input_audio", "output_audio", "audio"]
    """音频内容类型。"""


class OutputUnionMember1FileContentItemFile(BaseModel):
    file_url: str
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: str
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: Optional[str] = None
    """Optional Base64-encoded file content"""


class OutputUnionMember1FileContentItem(BaseModel):
    file: OutputUnionMember1FileContentItemFile
    """文件详情。"""

    type: Literal["file"]
    """文件内容类型。"""


OutputUnionMember1: TypeAlias = Union[
    TextContentItem,
    OutputUnionMember1ImageContentItem,
    OutputUnionMember1AudioContentItem,
    OutputUnionMember1FileContentItem,
    str,
]


class ToolResultItem(BaseModel):
    block_list: List[object]
    """工具结果的渲染块列表。"""

    call_id: str
    """对应的工具调用 ID。"""

    message_content: Union[str, List[MessageContentUnionMember1]]
    """工具结果的 message_content（用于富文本/富媒体渲染）。"""

    type: Literal["tool_result"]
    """工具结果条目类型标识。"""

    id: Optional[str] = None
    """工具结果条目 ID。"""

    output: Union[str, List[OutputUnionMember1], None] = None
    """以字符串或内容数组形式返回的工具输出。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """结果状态。"""
