"""
Elasticsearch客户端封装
提供ES连接管理和客户端实例
"""

import logging
from typing import Optional
from elasticsearch import Elasticsearch
# from elasticsearch.connection import create_connection  # 未使用
# from elasticsearch.exceptions import ConnectionError, RequestError  # 使用内置Exception
from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局ES客户端实例
_es_client: Optional[Elasticsearch] = None


def get_es_client() -> Elasticsearch:
    """
    获取Elasticsearch客户端实例（单例模式）
    
    Returns:
        Elasticsearch: ES客户端实例
    """
    global _es_client
    
    if _es_client is None:
        try:
            # 解析hosts配置（支持多个节点）
            hosts = settings.ELASTICSEARCH_HOSTS.split(",")
            hosts = [host.strip() for host in hosts]
            
            # 创建ES客户端
            _es_client = Elasticsearch(
                hosts=hosts,
                timeout=settings.ELASTICSEARCH_TIMEOUT,
                max_retries=settings.ELASTICSEARCH_MAX_RETRIES,
                retry_on_timeout=True,
                # 连接池配置
                maxsize=25,
                # 健康检查
                sniff_on_start=False,
                sniff_on_connection_fail=False,
            )
            
            # 测试连接
            if not _es_client.ping():
                raise ConnectionError("无法连接到Elasticsearch")
            
            logger.info(f"Elasticsearch客户端初始化成功，连接到: {hosts}")
            
        except Exception as e:
            logger.error(f"Elasticsearch客户端初始化失败: {e}")
            raise
    
    return _es_client


def close_es_client():
    """
    关闭Elasticsearch客户端连接
    """
    global _es_client
    
    if _es_client is not None:
        try:
            _es_client.close()
            logger.info("Elasticsearch客户端连接已关闭")
        except Exception as e:
            logger.error(f"关闭Elasticsearch客户端失败: {e}")
        finally:
            _es_client = None

