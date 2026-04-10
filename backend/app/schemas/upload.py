"""上传相关 Pydantic 模型。"""

from pydantic import BaseModel, Field


class ChunkUploadInitRequest(BaseModel):
    """分片上传初始化请求。"""

    file_name: str = Field(min_length=1, max_length=255, description="原始文件名")
    file_size: int = Field(gt=0, description="文件总大小")
    chunk_size: int = Field(gt=0, description="分片大小")
    content_type: str | None = Field(default=None, description="文件 MIME 类型")
    biz_type: str | None = Field(default=None, description="业务类型")


class ChunkUploadInitResponse(BaseModel):
    """分片上传初始化响应。"""

    upload_id: str = Field(description="上传任务 ID")
    chunk_size: int = Field(description="分片大小")
    total_chunks: int = Field(description="总分片数")


class ChunkUploadChunkResponse(BaseModel):
    """分片上传响应。"""

    chunk_index: int = Field(description="当前已保存的分片序号")


class ChunkUploadCompleteRequest(BaseModel):
    """分片上传完成请求。"""

    upload_id: str = Field(min_length=1, description="上传任务 ID")
    file_name: str = Field(min_length=1, max_length=255, description="原始文件名")
    total_chunks: int = Field(gt=0, description="总分片数")


class UploadFileResponse(BaseModel):
    """文件上传统一响应。"""

    file_name: str = Field(description="原始文件名")
    file_url: str = Field(description="文件访问地址")
    url: str = Field(description="兼容前端的文件访问地址")
    file_size: int = Field(description="文件大小（字节）")
    content_type: str | None = Field(default=None, description="文件 MIME 类型")
