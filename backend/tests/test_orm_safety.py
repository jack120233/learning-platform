"""ORM 安全性回归测试。

防止异步 SQLAlchemy 在序列化阶段因未加载的 server_default 字段触发懒加载。
"""

from app.models.base import Base


def test_all_models_enable_eager_defaults():
    """所有 BaseModel 派生模型都应开启 eager_defaults。"""
    for mapper in Base.registry.mappers:
        assert mapper.eager_defaults is True, mapper.class_.__name__
