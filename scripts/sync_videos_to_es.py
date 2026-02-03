"""
同步历史视频数据到Elasticsearch
用于将数据库中已有的视频数据同步到ES索引
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session_maker
from app.crud.video_crud import video_crud
from app.infra.elasticsearch.es_client import get_es_client
from app.infra.elasticsearch.sync_service import bulk_sync_videos_to_es
from app.infra.elasticsearch.index_manager import init_es_indexes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def sync_all_videos_to_es(batch_size: int = 100):
    """
    批量同步所有已发布的视频到ES
    
    Args:
        batch_size: 每批处理的视频数量
    """
    try:
        # 1. 初始化ES索引
        logger.info("检查并初始化ES索引...")
        es_client = get_es_client()
        if not init_es_indexes(es_client):
            logger.error("ES索引初始化失败，请检查ES服务是否正常运行")
            return
        
        # 2. 获取总数
        async with async_session_maker() as db:
            total = await video_crud.count_videos(
                db=db,
                status="published"
            )
            logger.info(f"找到 {total} 个已发布的视频需要同步")
            
            if total == 0:
                logger.info("没有需要同步的视频")
                return
            
            # 3. 分批同步
            total_synced = 0
            total_failed = 0
            skip = 0
            
            while skip < total:
                logger.info(f"正在同步第 {skip // batch_size + 1} 批（{skip + 1}-{min(skip + batch_size, total)}/{total}）...")
                
                # 获取一批视频（包含作者信息）
                videos = await video_crud.list_videos(
                    db=db,
                    skip=skip,
                    limit=batch_size,
                    status="published",
                    load_author=True
                )
                
                if not videos:
                    break
                
                # 构建作者名称字典
                author_names = {}
                for video in videos:
                    if video.author:
                        author_names[video.author_id] = video.author.user_name
                
                # 批量同步到ES
                result = await bulk_sync_videos_to_es(
                    videos=videos,
                    author_names=author_names,
                    es_client=es_client
                )
                
                total_synced += result["success"]
                total_failed += result["failed"]
                
                logger.info(f"本批同步完成：成功 {result['success']} 个，失败 {result['failed']} 个")
                
                skip += batch_size
            
            logger.info(f"\n同步完成！总计：成功 {total_synced} 个，失败 {total_failed} 个")
            
    except Exception as e:
        logger.error(f"同步失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("开始同步历史视频数据到Elasticsearch")
    print("=" * 60)
    
    # 可以自定义批次大小
    batch_size = 100
    
    try:
        asyncio.run(sync_all_videos_to_es(batch_size=batch_size))
        print("\n同步完成！")
    except KeyboardInterrupt:
        print("\n用户中断同步")
    except Exception as e:
        print(f"\n同步失败: {e}")
        sys.exit(1)

