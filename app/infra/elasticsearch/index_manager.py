"""
Elasticsearch索引管理模块
提供索引创建、删除、别名管理等功能
"""

import logging
from typing import Optional
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.infra.elasticsearch.es_client import get_es_client

logger = logging.getLogger(__name__)


def get_index_mapping() -> dict:
    """
    获取videos索引的mapping配置
    
    Returns:
        dict: 索引settings和mappings配置
    """
    return {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "ik_max_word_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                        "filter": ["lowercase", "stop"]
                    },
                    "ik_smart_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_smart",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "long", "index": True},
                "author_id": {"type": "long", "index": True},
                "author_name": {"type": "keyword", "index": True},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word_analyzer",
                    "search_analyzer": "ik_smart_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 200
                        }
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "ik_max_word_analyzer",
                    "search_analyzer": "ik_smart_analyzer"
                },
                "status": {"type": "keyword", "index": True},
                "publish_time": {"type": "long", "index": True},
                "view_count": {"type": "long", "index": True},
                "favorite_count": {"type": "long", "index": True},
                "comment_count": {"type": "long", "index": True},
                "hot_score": {"type": "float", "index": True},
                "duration": {"type": "integer", "index": True},
                "created_at": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                },
                "updated_at": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                }
            }
        }
    }


def create_index(es_client: Optional[Elasticsearch] = None, index_name: Optional[str] = None) -> bool:
    """
    创建Elasticsearch索引
    
    Args:
        es_client: ES客户端实例，如果为None则自动获取
        index_name: 索引名称，如果为None则使用配置中的默认值
        
    Returns:
        bool: 创建是否成功
    """
    if es_client is None:
        es_client = get_es_client()
    
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
    
    try:
        # 检查索引是否已存在
        if es_client.indices.exists(index=index_name):
            logger.info(f"索引 {index_name} 已存在，跳过创建")
            return True
        
        # 创建索引
        logger.info(f"开始创建索引 {index_name}...")
        mapping = get_index_mapping()
        es_client.indices.create(index=index_name, body=mapping)
        logger.info(f"索引 {index_name} 创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"创建索引 {index_name} 失败: {e}", exc_info=True)
        return False


def delete_index(es_client: Optional[Elasticsearch] = None, index_name: Optional[str] = None) -> bool:
    """
    删除Elasticsearch索引
    
    Args:
        es_client: ES客户端实例，如果为None则自动获取
        index_name: 索引名称，如果为None则使用配置中的默认值
        
    Returns:
        bool: 删除是否成功
    """
    if es_client is None:
        es_client = get_es_client()
    
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
    
    try:
        if not es_client.indices.exists(index=index_name):
            logger.info(f"索引 {index_name} 不存在，跳过删除")
            return True
        
        es_client.indices.delete(index=index_name)
        logger.info(f"索引 {index_name} 删除成功")
        return True
        
    except Exception as e:
        logger.error(f"删除索引 {index_name} 失败: {e}", exc_info=True)
        return False


def init_es_indexes(es_client: Optional[Elasticsearch] = None) -> bool:
    """
    初始化Elasticsearch索引
    检查videos索引是否存在，不存在则自动创建
    
    Args:
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        bool: 初始化是否成功
    """
    if es_client is None:
        try:
            es_client = get_es_client()
        except Exception as e:
            logger.warning(f"无法连接到Elasticsearch: {e}")
            return False
    
    index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
    
    try:
        # 检查索引是否存在
        if es_client.indices.exists(index=index_name):
            logger.info(f"索引 {index_name} 已存在，跳过创建")
            return True
        
        # 创建索引
        logger.info(f"开始创建索引 {index_name}...")
        mapping = get_index_mapping()
        es_client.indices.create(index=index_name, body=mapping)
        logger.info(f"索引 {index_name} 创建成功")
        
        # 设置别名（可选）
        try:
            alias_name = f"{index_name}_alias"
            es_client.indices.put_alias(index=index_name, name=alias_name)
            logger.info(f"索引别名 {alias_name} 设置成功")
        except Exception as e:
            logger.warning(f"设置索引别名失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"初始化索引失败: {e}", exc_info=True)
        return False


def check_index_health(es_client: Optional[Elasticsearch] = None, index_name: Optional[str] = None) -> bool:
    """
    检查索引健康状态
    
    Args:
        es_client: ES客户端实例，如果为None则自动获取
        index_name: 索引名称，如果为None则使用配置中的默认值
        
    Returns:
        bool: 索引是否存在且健康
    """
    if es_client is None:
        es_client = get_es_client()
    
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
    
    try:
        if not es_client.indices.exists(index=index_name):
            return False
        
        # 检查集群健康状态
        health = es_client.cluster.health(index=index_name, wait_for_status="yellow", timeout="5s")
        return health["status"] in ["green", "yellow"]
        
    except Exception as e:
        logger.error(f"检查索引健康状态失败: {e}")
        return False

