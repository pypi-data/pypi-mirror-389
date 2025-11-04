# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from .._models import BaseModel
from .text_content_item import TextContentItem

__all__ = [
    "MessageItem",
    "MessageContentUnionMember1",
    "MessageContentUnionMember1ImageContentItem",
    "MessageContentUnionMember1ImageContentItemImageURL",
    "MessageContentUnionMember1AudioContentItem",
    "MessageContentUnionMember1AudioContentItemInputAudio",
    "MessageContentUnionMember1FileContentItem",
    "MessageContentUnionMember1FileContentItemFile",
]


class MessageContentUnionMember1ImageContentItemImageURL(BaseModel):
    url: str
    """图片的可访问 URL。"""

    detail: Optional[Literal["low", "high", "auto"]] = None
    """清晰度等级，可选 low/high/auto。"""


class MessageContentUnionMember1ImageContentItem(BaseModel):
    image_url: MessageContentUnionMember1ImageContentItemImageURL
    """图片 URL 信息。"""

    type: Literal["image", "input_image", "output_image", "image_url"]
    """图片内容类型。"""


class MessageContentUnionMember1AudioContentItemInputAudio(BaseModel):
    data: str
    """Base64-encoded audio bytes"""

    format: Literal["wav", "mp3"]


class MessageContentUnionMember1AudioContentItem(BaseModel):
    input_audio: MessageContentUnionMember1AudioContentItemInputAudio
    """输入音频内容。"""

    type: Literal["input_audio", "output_audio", "audio"]
    """音频内容类型。"""


class MessageContentUnionMember1FileContentItemFile(BaseModel):
    file_url: str
    """远程文件的可访问 URL；与 file_data 二选一，可同时提供以便存档。"""

    filename: str
    """文件名（含扩展名），用于渲染与调试追踪。"""

    file_data: Optional[str] = None
    """Optional Base64-encoded file content"""


class MessageContentUnionMember1FileContentItem(BaseModel):
    file: MessageContentUnionMember1FileContentItemFile
    """文件详情。"""

    type: Literal["file"]
    """文件内容类型。"""


MessageContentUnionMember1: TypeAlias = Union[
    TextContentItem,
    MessageContentUnionMember1ImageContentItem,
    MessageContentUnionMember1AudioContentItem,
    MessageContentUnionMember1FileContentItem,
    str,
]


class MessageItem(BaseModel):
    role: Literal["user", "assistant", "system", "developer"]
    """消息角色。"""

    type: Literal["message"]
    """消息条目类型标识。"""

    id: Optional[str] = None
    """消息 ID。"""

    block_list: Optional[List[object]] = None
    """渲染块列表（图表/表格等富媒体）。"""

    message_content: Union[str, List[MessageContentUnionMember1], None] = None
    """消息内容，字符串或内容项数组，工具协议兼容的 message_content（保留字段）。"""

    name: Optional[str] = None
    """角色名称（可选）。"""

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
    """消息生成状态。"""
