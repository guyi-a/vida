# Vida 前端静态文件

这是 Vida 视频应用平台的前端静态文件，包含了完整的前端用户界面，支持视频浏览、用户管理、点赞评论等功能。

## 文件结构

```
static/
├── index.html                 # 主页面文件
├── css/
│   └── styles.css            # 样式文件
├── js/
│   ├── api.js                # API 接口封装
│   ├── app.js                # 应用程序逻辑
│   └── ui.js                 # UI 交互逻辑
└── manifest.json             # PWA 配置文件
```

## 功能特性

### 核心功能
- **视频播放**: 支持在线视频播放和预览
- **用户认证**: 登录、注册、个人资料管理
- **视频管理**: 上传、编辑、删除个人视频
- **社交网络**: 关注/取关、粉丝管理
- **互动功能**: 点赞、评论、回复

### 用户界面
- **响应式设计**: 支持桌面端和移动端
- **现代化 UI**: 使用 Inter 字体和精致的设计
- **模态框交互**: 优雅的信息展示和操作界面
- **实时反馈**: 操作结果即时提示

## 支持的 API 接口

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/logout` - 退出登录
- `GET /api/v1/user/me` - 获取当前用户信息

### 视频相关
- `GET /api/v1/videos/feed` - 获取视频流
- `GET /api/v1/videos/{video_id}` - 获取视频详情
- `POST /api/v1/videos/upload` - 上传视频
- `GET /api/v1/videos/my/list` - 获取我的视频列表
- `PUT /api/v1/videos/{video_id}` - 编辑视频
- `DELETE /api/v1/videos/{video_id}` - 删除视频
- `GET /api/v1/videos/public-bucket` - 获取公开桶文件列表

### 点赞功能
- `POST /api/v1/favorites/{video_id}` - 点赞视频
- `DELETE /api/v1/favorites/{video_id}` - 取消点赞
- `GET /api/v1/favorites/{video_id}/status` - 查询点赞状态
- `GET /api/v1/favorites/my/list` - 获取我的点赞列表
- `POST /api/v1/favorites/batch/status` - 批量查询点赞状态

### 评论功能
- `POST /api/v1/comments/{video_id}` - 发表评论
- `PUT /api/v1/comments/{comment_id}` - 更新评论
- `DELETE /api/v1/comments/{comment_id}` - 删除评论
- `GET /api/v1/comments/video/{video_id}` - 获取视频评论列表
- `GET /api/v1/comments/video/{video_id}/tree` - 获取评论树
- `GET /api/v1/comments/{comment_id}/replies` - 获取评论回复
- `GET /api/v1/comments/my/list` - 获取我的评论列表

### 关注/粉丝功能
- `POST /api/v1/relations/follow/{user_id}` - 关注用户
- `DELETE /api/v1/relations/unfollow/{user_id}` - 取消关注
- `GET /api/v1/relations/following/{user_id}` - 获取用户关注列表
- `GET /api/v1/relations/followers/{user_id}` - 获取用户粉丝列表
- `GET /api/v1/relations/following/my/list` - 获取我的关注列表
- `GET /api/v1/relations/followers/my/list` - 获取我的粉丝列表
- `GET /api/v1/relations/following/{user_id}/status` - 查询关注状态
- `POST /api/v1/relations/batch/status` - 批量查询关注状态
- `GET /api/v1/relations/mutual` - 获取互相关注列表

### 用户管理
- `GET /api/v1/user/{user_id}` - 获取用户信息
- `PUT /api/v1/user/update` - 更新用户信息
- `POST /api/v1/user/avatar/upload` - 上传头像

### 测试接口
- `POST /api/test/infra/minio/upload-public` - 上传到公开桶
- `GET /api/test/infra/minio/public-videos` - 获取公开桶视频列表

## 使用说明

### 直接访问
1. 确保后端服务正在运行（通常在 `http://localhost:8000`）
2. 在浏览器中打开 `static/index.html` 文件
3. 开始使用应用功能

### 集成到 FastAPI 服务
可以将静态文件集成到 FastAPI 服务中：

```python
from fastapi.staticfiles import StaticFiles

# 在 FastAPI 应用中添加静态文件支持
app.mount("/static", StaticFiles(directory="static"), name="static")
```

然后通过 `http://localhost:8000/static/index.html` 访问前端界面。

### 开发说明
- 所有 API 调用都封装在 `api.js` 文件中
- 使用相对路径调用 API，会自动使用当前服务器的地址
- 前端支持 Token 认证，登录后会自动保存和发送认证信息
- 响应式设计适配移动端和桌面端

## 技术栈
- **HTML5**: 现代网页结构
- **CSS3**: 响应式样式和动画效果
- **JavaScript ES6**: 应用程序逻辑
- **Font Awesome**: 图标库
- **Google Fonts**: Inter 字体

## 浏览器兼容性
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+
- 移动端浏览器支持

## 注意事项

1. **CORS 配置**: 确保后端服务配置了正确的 CORS 允许列表
2. **认证 Token**: 前端会自动处理 JWT token 的存储和发送
3. **文件大小限制**: 视频上传限制为 500MB
4. **网络请求**: API 错误会自动显示提示信息
5. **离线使用**: 可作为 PWA 安装到桌面使用

## 扩展开发

### 添加新功能
1. 在 `api.js` 中添加对应的 API 调用方法
2. 在 `app.js` 中实现业务逻辑
3. 在 `ui.js` 中添加用户交互功能
4. 在 `index.html` 中添加必要的 UI 元素

### 修改样式
- 统一定义的样式变量在 `styles.css` 文件的开头
- 响应式断点在 `@media` 查询中定义
- 颜色和字体大小采用一致性设计规范

### 性能优化
- 组件采用懒加载减少初始加载时间
- 图片和视频使用适当的压缩格式
- API 请求添加了错误处理和重试机制