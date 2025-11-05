"""Shopline API 数据模型 - CreateProductVariationBody"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from typing_extensions import Literal

# 导入相关模型
from .translatable import Translatable


class CreateProductVariationBody(BaseModel):
    """Payload for creating product variation"""
    pass