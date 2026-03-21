"""学习模块相关 Pydantic 模型

定义学习模块的请求和响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ==================== 学习进度模型 ====================

class StartLearningRequest(BaseModel):
    """开始学习请求"""

    course_id: int = Field(..., description="课程ID")


class SaveProgressRequest(BaseModel):
    """保存进度请求"""

    course_id: int = Field(..., description="课程ID")
    chapter_id: int = Field(..., description="章节ID")
    section_id: int = Field(..., description="小节ID")
    resource_id: int = Field(..., description="资源ID")
    position: int = Field(..., ge=0, description="播放位置（秒）")
    progress: float = Field(..., ge=0, le=100, description="学习进度（百分比）")


class ProgressResponse(BaseModel):
    """学习进度响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    section_id: int = Field(description="小节ID")
    resource_id: int = Field(description="资源ID")
    progress: float = Field(description="学习进度（百分比）")
    position: int = Field(description="播放位置（秒）")
    is_completed: bool = Field(description="是否完成")
    last_play_at: datetime | None = Field(default=None, description="最后播放时间")

    model_config = {"from_attributes": True}


class ContinueLearningResponse(BaseModel):
    """继续学习响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID")
    resource_id: int | None = Field(default=None, description="资源ID")
    position: int = Field(default=0, description="播放位置（秒）")


class PlayUrlResponse(BaseModel):
    """播放地址响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    play_url: str = Field(description="播放地址")
    duration: int = Field(description="时长（秒）")
    is_free: bool = Field(description="是否免费")


class PreviewResponse(BaseModel):
    """文档预览响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    preview_url: str = Field(description="预览地址")
    file_type: str = Field(description="文件类型")