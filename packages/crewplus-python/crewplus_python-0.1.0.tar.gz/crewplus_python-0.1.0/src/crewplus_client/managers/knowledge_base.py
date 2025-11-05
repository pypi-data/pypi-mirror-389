# -*- coding: utf-8 -*-
# @create: 2025-10-20
# @update: 2025-10-20
# @desc  : 封装所有与知识库（Knowledge Base）资源相关的 API 操作。

from typing import List, TYPE_CHECKING, Optional
from ..models.knowledge_base import KnowledgeBase

# 使用 TYPE_CHECKING 来避免循环导入，同时为类型检查器提供信息
if TYPE_CHECKING:
    from ..client import CrewPlusClient

class KnowledgeBaseManager:
    """
    管理知识库资源的类。
    
    提供创建、查询、更新和删除知识库的方法。
    """
    def __init__(self, client: "CrewPlusClient"):
        """
        初始化 KnowledgeBaseManager。

        Args:
            client (CrewPlusClient): 用于执行 API 请求的客户端实例。
        """
        self._client = client

    def create(self, coll_name: str, coll_id: int, vector_store: str, description: str = "") -> KnowledgeBase:
        """
        创建一个新的知识库。

        Args:
            coll_name (str): 集合的业务名称。
            coll_id (int): 集合的唯一标识符 (来自 SaaS 系统的整数 ID)。
            vector_store (str): 要使用的向量存储实例的名称。
            description (str, optional): 知识库的描述。默认为 ""。

        Returns:
            KnowledgeBase: 新创建的知识库对象。
        """
        # 后端创建接口的路径是单数形式
        params = {"vector_store": vector_store}
        payload = {"coll_name": coll_name, "coll_id": coll_id, "description": description}

        response_data = self._client._request(
            "POST",
            "/crewplus/v2/knowledgebase",
            params=params,
            json=payload
        )
        return KnowledgeBase.model_validate(response_data)

    def get(self, kb_id: int) -> KnowledgeBase:
        """
        根据 ID 获取单个知识库的详细信息。

        Args:
            kb_id (int): 知识库的 ID。

        Returns:
            KnowledgeBase: 匹配的知识库对象。
        """
        # 后端获取单个资源的路径是单数形式
        response_data = self._client._request("GET", f"/crewplus/v2/knowledgebase/{kb_id}")
        return KnowledgeBase.model_validate(response_data)
        
    def find_by_coll_name(self, coll_name: str) -> KnowledgeBase:
        """
        根据集合名称查找知识库。

        Args:
            coll_name (str): 集合的业务名称。

        Returns:
            KnowledgeBase: 匹配的知识库对象。
        """
        response_data = self._client._request("GET", f"/crewplus/v2/knowledgebase/find/{coll_name}")
        return KnowledgeBase.model_validate(response_data)

    def update(
        self, 
        kb_id: int, 
        coll_name: Optional[str] = None, 
        coll_id: Optional[int] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> KnowledgeBase:
        """
        更新一个已存在的知识库。

        Args:
            kb_id (int): 要更新的知识库的 ID。
            coll_name (Optional[str], optional): 新的集合业务名称。
            coll_id (Optional[int], optional): 新的集合唯一标识符。
            description (Optional[str], optional): 新的描述。
            is_active (Optional[bool], optional): 新的激活状态。

        Returns:
            KnowledgeBase: 更新后的知识库对象。
        """
        payload = {
            "coll_name": coll_name,
            "coll_id": coll_id,
            "description": description,
            "is_active": is_active,
        }
        # 移除未提供的参数（值为 None），避免覆盖已有值
        cleaned_payload = {k: v for k, v in payload.items() if v is not None}
        
        response_data = self._client._request(
            "PUT",
            f"/crewplus/v2/knowledgebase/{kb_id}",
            json=cleaned_payload
        )
        return KnowledgeBase.model_validate(response_data)

    def list(self, **params) -> List[KnowledgeBase]:
        """
        获取知识库列表，支持通过参数进行筛选。

        Args:
            **params: 传递给 API 的查询参数, 例如 limit, offset, name__icontains 等。

        Returns:
            List[KnowledgeBase]: 知识库对象列表。
        """
        # 后端获取列表的路径是复数形式
        response_data = self._client._request("GET", "/crewplus/v2/knowledgebases", params=params) or []
        return [KnowledgeBase.model_validate(item) for item in response_data]

    def delete(self, kb_id: int) -> None:
        """
        删除一个知识库。

        此方法封装了后端的批量删除接口，提供了一个更方便的单体删除功能。

        Args:
            kb_id (int): 要删除的知识库的 ID。
        """
        # 后端删除接口是复数形式，并且需要一个 ID 列表
        self._client._request(
            "DELETE",
            "/crewplus/v2/knowledgebases",
            json={"ids": [kb_id]}
        )
