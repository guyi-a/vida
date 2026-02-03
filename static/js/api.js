// API 基础配置
const API_BASE_URL = '/api/v1';
const API_TEST_URL = '/api/test/infra';

// 工具函数
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function getAuthHeaders() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// 显示错误提示
function showMessage(message, type = 'error') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    // 添加到页面顶部
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(messageDiv, mainContent.firstChild);
    } else {
        // 如果没有main-content，添加到body
        document.body.insertBefore(messageDiv, document.body.firstChild);
    }
    
    // 3秒后自动消失（info类型5秒）
    const timeout = type === 'info' ? 5000 : 3000;
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, timeout);
}

// 解析API响应
async function apiRequest(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        // 先尝试解析 JSON
        let data;
        try {
            data = await response.json();
        } catch (e) {
            // 如果不是 JSON，使用文本
            const text = await response.text();
            throw new Error(text || `请求失败: ${response.status} ${response.statusText}`);
        }
        
        // 检查 HTTP 状态码
        if (!response.ok) {
            // 后端可能返回 error 对象格式
            const errorMessage = data.error?.message || data.detail || data.message || `请求失败: ${response.status}`;
            throw new Error(errorMessage);
        }
        
        // 检查业务状态（如果存在 success 字段）
        if (data.success === false) {
            throw new Error(data.message || '请求失败');
        }
        
        return data;
    } catch (error) {
        // 只在有错误消息时显示
        if (error.message) {
            showMessage(error.message);
        }
        throw error;
    }
}

// Auth API
const AuthAPI = {
    // 用户登录
    login: async (username, password) => {
        return await apiRequest(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },
    
    // 用户注册
    register: async (username, password) => {
        return await apiRequest(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },
    
    // 退出登录
    logout: async () => {
        await apiRequest(`${API_BASE_URL}/auth/logout`, {
            method: 'POST'
        });
    },
    
    // 获取当前用户信息
    getCurrentUser: async () => {
        return await apiRequest(`${API_BASE_URL}/users/me`, {
            method: 'GET'
        });
    }
};

// Video API
const VideoAPI = {
    // 获取视频流
    getFeed: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/videos/feed?${params}`);
    },
    
    // 获取视频详情
    getDetail: async (videoId) => {
        return await apiRequest(`${API_BASE_URL}/videos/${videoId}`);
    },
    
    // 上传视频
    upload: async (file, title, description) => {
        const formData = new FormData();
        formData.append('video_file', file);
        formData.append('title', title);
        formData.append('description', description);
        
        const response = await fetch(`${API_BASE_URL}/videos/upload`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '上传失败');
        }
        return data;
    },
    
    // 获取我的视频列表
    getMyVideos: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/videos/my/list?${params}`);
    },
    
    // 编辑视频
    updateVideo: async (videoId, updateData) => {
        return await apiRequest(`${API_BASE_URL}/videos/${videoId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    },
    
    // 删除视频
    deleteVideo: async (videoId) => {
        return await apiRequest(`${API_BASE_URL}/videos/${videoId}`, {
            method: 'DELETE'
        });
    },
    
    // 获取公开桶文件列表
    getPublicBucketFiles: async (prefix = null) => {
        const params = new URLSearchParams();
        if (prefix) params.append('prefix', prefix);
        return await apiRequest(`${API_BASE_URL}/videos/public-bucket?${params}`);
    }
};

// Favorite API
const FavoriteAPI = {
    // 点赞视频
    favoriteVideo: async (videoId) => {
        return await apiRequest(`${API_BASE_URL}/favorites/${videoId}`, {
            method: 'POST'
        });
    },
    
    // 取消点赞
    unfavoriteVideo: async (videoId) => {
        return await apiRequest(`${API_BASE_URL}/favorites/${videoId}`, {
            method: 'DELETE'
        });
    },
    
    // 查询点赞状态
    getFavoriteStatus: async (videoId) => {
        return await apiRequest(`${API_BASE_URL}/favorites/${videoId}/status`);
    },
    
    // 获取我的点赞列表
    getMyFavorites: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/favorites/my/list?${params}`);
    },
    
    // 批量查询点赞状态
    getBatchFavoriteStatus: async (videoIds) => {
        return await apiRequest(`${API_BASE_URL}/favorites/batch/status`, {
            method: 'POST',
            body: JSON.stringify(videoIds)
        });
    }
};

// Comment API
const CommentAPI = {
    // 发表评论
    createComment: async (videoId, content, parentId = null) => {
        return await apiRequest(`${API_BASE_URL}/comments/${videoId}`, {
            method: 'POST',
            body: JSON.stringify({ content, parent_id: parentId })
        });
    },
    
    // 更新评论
    updateComment: async (commentId, content) => {
        return await apiRequest(`${API_BASE_URL}/comments/${commentId}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
        });
    },
    
    // 删除评论
    deleteComment: async (commentId) => {
        return await apiRequest(`${API_BASE_URL}/comments/${commentId}`, {
            method: 'DELETE'
        });
    },
    
    // 获取视频评论列表
    getVideoComments: async (videoId, page = 1, pageSize = 20, parentId = null) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        if (parentId) params.append('parent_id', parentId);
        return await apiRequest(`${API_BASE_URL}/comments/video/${videoId}?${params}`);
    },
    
    // 获取视频评论树
    getVideoCommentsTree: async (videoId, page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/comments/video/${videoId}/tree?${params}`);
    },
    
    // 获取评论的回复列表
    getCommentReplies: async (commentId, page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/comments/${commentId}/replies?${params}`);
    },
    
    // 获取我的评论列表
    getMyComments: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/comments/my/list?${params}`);
    }
};

// Relation API (关注/粉丝)
const RelationAPI = {
    // 关注用户
    followUser: async (userId) => {
        return await apiRequest(`${API_BASE_URL}/relations/follow/${userId}`, {
            method: 'POST'
        });
    },
    
    // 取消关注
    unfollowUser: async (userId) => {
        return await apiRequest(`${API_BASE_URL}/relations/unfollow/${userId}`, {
            method: 'POST'
        });
    },
    
    // 获取用户的关注列表
    getUserFollowing: async (userId, page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/relations/following/${userId}?${params}`);
    },
    
    // 获取用户的粉丝列表
    getUserFollowers: async (userId, page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/relations/followers/${userId}?${params}`);
    },
    
    // 获取我的关注列表
    getMyFollowing: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/relations/following/my/list?${params}`);
    },
    
    // 获取我的粉丝列表
    getMyFollowers: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/relations/followers/my/list?${params}`);
    },
    
    // 查询关注状态
    getFollowStatus: async (userId) => {
        return await apiRequest(`${API_BASE_URL}/relations/following/${userId}/status`);
    },
    
    // 批量查询关注状态
    getBatchFollowStatus: async (userIds) => {
        return await apiRequest(`${API_BASE_URL}/relations/batch/status`, {
            method: 'POST',
            body: JSON.stringify(userIds)
        });
    },
    
    // 获取互相关注列表
    getMutualFollowers: async (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page, page_size: pageSize });
        return await apiRequest(`${API_BASE_URL}/relations/mutual?${params}`);
    }
};

// User API
const UserAPI = {
    // 获取用户信息
    getUserInfo: async (userId) => {
        return await apiRequest(`${API_BASE_URL}/users/${userId}`);
    },
    
    // 更新用户信息
    updateUserInfo: async (userId, updateData) => {
        return await apiRequest(`${API_BASE_URL}/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    },
    
    // 上传用户头像
    uploadAvatar: async (file) => {
        const formData = new FormData();
        formData.append('avatar_file', file);
        
        const response = await fetch(`${API_BASE_URL}/users/avatar/upload`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '上传失败');
        }
        return data;
    },
    
    // 上传用户背景图
    uploadBanner: async (file) => {
        const formData = new FormData();
        formData.append('banner_file', file);
        
        const response = await fetch(`${API_BASE_URL}/users/banner/upload`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '上传失败');
        }
        return data;
    }
};

// MinIO 测试 API
const MinIOAPI = {
    // 上传文件到 public bucket
    uploadToPublic: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_TEST_URL}/minio/upload-public`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '上传失败');
        }
        return data;
    },
    
    // 列出 public bucket 中的视频文件
    listPublicVideos: async () => {
        const response = await fetch(`${API_TEST_URL}/minio/public-videos`);
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '获取列表失败');
        }
        return data;
    }
};

// Search API
const SearchAPI = {
    // 搜索视频
    searchVideos: async (query, options = {}) => {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (options.author_id) params.append('author_id', options.author_id);
        if (options.video_id) params.append('video_id', options.video_id);
        if (options.sort) params.append('sort', options.sort);
        if (options.start_time) params.append('start_time', options.start_time);
        if (options.end_time) params.append('end_time', options.end_time);
        if (options.page) params.append('page', options.page);
        if (options.page_size) params.append('page_size', options.page_size);
        
        return await apiRequest(`${API_BASE_URL}/search/videos?${params}`);
    }
};

// Agent API
const AgentAPI = {
    // 同步调用Agent对话
    invoke: async (message, chatId) => {
        return await apiRequest(`${API_BASE_URL}/agent/invoke`, {
            method: 'POST',
            body: JSON.stringify({ message, chat_id: chatId })
        });
    },
    
    // 流式调用Agent对话
    stream: async (message, chatId, onChunk, onComplete, onError) => {
        try {
            const response = await fetch(`${API_BASE_URL}/agent/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({ message, chat_id: chatId })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || '请求失败');
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.code === 200) {
                                if (data.message === 'done') {
                                    if (onComplete) onComplete(data.data?.chat_id);
                                } else if (data.message === 'streaming' && data.data?.content) {
                                    if (onChunk) onChunk(data.data.content);
                                }
                            } else {
                                if (onError) onError(new Error(data.message || '请求失败'));
                            }
                        } catch (e) {
                            console.error('解析SSE数据失败:', e);
                        }
                    }
                }
            }
        } catch (error) {
            if (onError) {
                onError(error);
            } else {
                throw error;
            }
        }
    }
};

// 导出 API 对象
window.API = {
    auth: AuthAPI,
    video: VideoAPI,
    favorite: FavoriteAPI,
    comment: CommentAPI,
    relation: RelationAPI,
    user: UserAPI,
    search: SearchAPI,
    agent: AgentAPI,
    minio: MinIOAPI
};