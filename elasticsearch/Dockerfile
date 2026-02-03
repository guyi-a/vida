# Elasticsearch Dockerfile（含IK中文分词插件）

FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 安装IK中文分词插件
# 优先使用国内镜像源（华为云），如果失败则使用GitHub源
RUN bin/elasticsearch-plugin install -b \
    https://mirrors.huaweicloud.com/elasticsearch-analysis-ik/8.11.0/elasticsearch-analysis-ik-8.11.0.zip || \
    bin/elasticsearch-plugin install -b \
    https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip

# 验证插件安装
RUN bin/elasticsearch-plugin list | grep analysis-ik || echo "Warning: IK plugin installation may have failed"

