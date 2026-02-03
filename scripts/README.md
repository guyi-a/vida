# 脚本说明

## sync_videos_to_es.py

同步历史视频数据到Elasticsearch的脚本。

### 使用方法

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# 运行同步脚本
python scripts/sync_videos_to_es.py
```

### 功能说明

- 自动检查并创建ES索引（如果不存在）
- 批量同步所有已发布的视频到ES
- 显示同步进度和结果统计
- 支持分批处理，避免内存占用过大

### 注意事项

- 确保Elasticsearch服务已启动
- 确保数据库连接正常
- 同步过程中不要中断，否则可能需要重新运行

