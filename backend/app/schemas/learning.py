"""学习模块相关 Pydantic 模型

定义学习模块的请求和响应模型，并兼容前端当前使用的字段命名。
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


# ==================== 学习进度模型 ====================

class StartLearningRequest(BaseModel):
    """开始学习请求"""

    course_id: int = Field(..., description="课程ID")


class SaveProgressRequest(BaseModel):
    """保存进度请求"""

    course_id: int | None = Field(default=None, description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int = Field(..., description="小节ID")
    resource_id: int = Field(..., description="资源ID")
    position: int | None = Field(default=None, ge=0, description="播放位置（秒）")
    progress: float | None = Field(default=None, ge=0, le=100, description="学习进度（百分比）")
    current_time: int | None = Field(default=None, ge=0, description="当前播放时间（秒）")
    total_time: int | None = Field(default=None, ge=0, description="资源总时长（秒）")
    is_completed: bool = Field(default=False, description="是否完成")

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        current_time = normalized.get("current_time")
        position = normalized.get("position")
        total_time = normalized.get("total_time")
        progress = normalized.get("progress")
        is_completed = bool(normalized.get("is_completed", False))

        if current_time is None and position is not None:
            current_time = position
            normalized["current_time"] = current_time

        if normalized.get("position") is None and current_time is not None:
            normalized["position"] = current_time

        if progress is None:
            if is_completed:
                normalized["progress"] = 100.0
            elif current_time is not None and total_time:
                normalized["progress"] = min((current_time / total_time) * 100, 100)
            else:
                normalized["progress"] = 0.0

        return normalized


class ProgressResponse(BaseModel):
    """学习进度响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    section_id: int = Field(description="小节ID")
    resource_id: int = Field(description="资源ID")
    progress: float = Field(description="学习进度（百分比）")
    position: int = Field(description="播放位置（秒）")
    current_time: int = Field(description="当前播放时间（秒）")
    total_time: int = Field(default=0, description="资源总时长（秒）")
    is_completed: bool = Field(description="是否完成")
    last_play_at: datetime | None = Field(default=None, description="最后播放时间")
    last_learn_at: datetime | None = Field(default=None, description="最后学习时间")


class ContinueLearningResponse(BaseModel):
    """继续学习响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID")
    resource_id: int | None = Field(default=None, description="资源ID")
    position: int = Field(default=0, description="播放位置（秒）")
    last_section_id: int | None = Field(default=None, description="最后学习的小节ID")
    last_section_title: str = Field(default="", description="最后学习的小节标题")
    last_resource_id: int | None = Field(default=None, description="最后学习的资源ID")
    last_resource_type: str = Field(default="", description="最后学习的资源类型")
    current_time: int = Field(default=0, description="当前播放时间（秒）")
    last_learn_at: datetime | None = Field(default=None, description="最后学习时间")


class PlayUrlResponse(BaseModel):
    """播放地址响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    play_url: str = Field(description="播放地址")
    file_url: str = Field(description="资源文件地址")
    resource_type: str = Field(description="资源类型")
    file_name: str = Field(description="文件名")
    duration: int = Field(description="时长（秒）")
    is_free: bool = Field(description="是否免费")
    resolution: str | None = Field(default=None, description="分辨率")
    thumbnail_url: str | None = Field(default=None, description="缩略图地址")


class PreviewResponse(BaseModel):
    """文档预览响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    preview_url: str = Field(description="预览地址")
    file_type: str = Field(description="文件类型")
