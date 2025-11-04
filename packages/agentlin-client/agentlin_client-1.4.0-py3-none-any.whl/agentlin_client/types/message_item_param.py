# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .text_content_item_param import TextContentItemParam

__all__ = [
    "MessageItemParam",
    "MessageContentUnionMember1",
    "MessageContentUnionMember1ImageContentItem",
    "MessageContentUnionMember1ImageContentItemImageURL",
    "MessageContentUnionMember1AudioContentItem",
    "MessageContentUnionMember1AudioContentItemInputAudio",
    "MessageContentUnionMember1FileContentItem",
    "MessageContentUnionMember1FileContentItemFile",
]


class MessageContentUnionMember1ImageContentItemImageURL(TypedDict, total=False):
    url: Required[str]
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]]
    """清晰度等级，可选 low/high/auto。"""


class MessageContentUnionMember1ImageContentItem(TypedDict, total=False):
    image_url: Required[MessageContentUnionMember1ImageContentItemImageURL]
    """图片 URL 信息。"""

    type: Required[Literal["image", "input_image", "output_image", "image_url"]]
    """图片内容类型。"""


class MessageContentUnionMember1AudioContentItemInputAudio(TypedDict, total=False):
    data: Required[str]
    """Base64-encoded audio bytes"""

    format: Required[Literal["wav", "mp3"]]


class MessageContentUnionMember1AudioContentItem(TypedDict, total=False):
    input_audio: Required[MessageContentUnionMember1AudioContentItemInputAudio]
    """输入音频内容。"""

    type: Required[Literal["input_audio", "output_audio", "audio"]]
    """音频内容类型。"""


class MessageContentUnionMember1FileContentItemFile(TypedDict, total=False):
    file_url: Required[str]
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: Required[str]
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: str
    """Optional Base64-encoded file content"""


class MessageContentUnionMember1FileContentItem(TypedDict, total=False):
    file: Required[MessageContentUnionMember1FileContentItemFile]
    """文件详情。"""

    type: Required[Literal["file"]]
    """文件内容类型。"""


MessageContentUnionMember1: TypeAlias = Union[
    TextContentItemParam,
    MessageContentUnionMember1ImageContentItem,
    MessageContentUnionMember1AudioContentItem,
    MessageContentUnionMember1FileContentItem,
    str,
]


class MessageItemParam(TypedDict, total=False):
    role: Required[Literal["user", "assistant", "system", "developer"]]
    """消息角色。"""

    type: Required[Literal["message"]]
    """消息条目类型标识。"""

    id: str
    """消息 ID。"""

    block_list: Iterable[object]
    """渲染块列表（图表/表格等富媒体）。"""

    message_content: Union[str, SequenceNotStr[MessageContentUnionMember1]]
    """消息内容，字符串或内容项数组，工具协议兼容的 message_content（保留字段）。"""

    name: str
    """角色名称（可选）。"""

    status: Literal["in_progress", "completed", "incomplete"]
    """消息生成状态。"""
