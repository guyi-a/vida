// 主应用程序逻辑

// 当前页面状态
let currentState = {
    page: 1,
    pageSize: 20,
    loading: false,
    user: null,
    currentSection: 'feed'
};

// 登录功能
async function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }
    
    try {
        const response = await API.auth.login(username, password);
        setToken(response.data.token || response.data.access_token);
        
        await loadCurrentUser();
        closeModal('loginModal');
        showMessage('登录成功！', 'success');
        
        // 重新加载当前内容
        if (currentState.currentSection === 'feed') {
            loadVideoFeed();
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 注册功能
async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    
    if (!username || !password || !confirmPassword) {
        showMessage('请填写所有字段', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('密码长度不能少于6位', 'error');
        return;
    }
    
    try {
        await API.auth.register(username, password);
        showMessage('注册成功！请登录', 'success');
        showLoginModal();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 上传视频功能
async function uploadVideo(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('videoFile');
    const titleInput = document.getElementById('videoTitle');
    const descInput = document.getElementById('videoDescription');
    
    const file = fileInput.files[0];
    const title = titleInput.value.trim();
    const description = descInput.value.trim();
    
    if (!file || !title) {
        showMessage('请选择视频文件并填写标题', 'error');
        return;
    }
    
    if (file.size > 500 * 1024 * 1024) { // 500MB
        showMessage('文件大小不能超过500MB', 'error');
        return;
    }
    
    try {
        const response = await API.video.upload(file, title, description || '无描述');
        
        closeModal('uploadModal');
        showMessage('视频上传成功！正在转码中...', 'success');
        
        // 重新加载我的视频列表
        if (currentState.currentSection === 'my-videos') {
            loadMyVideos();
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 加载视频流
async function loadVideoFeed(page = 1) {
    if (currentState.loading) return;
    
    currentState.loading = true;
    currentState.page = page;
    
    const loadingElement = document.getElementById('loading');
    const videoGrid = document.getElementById('videoGrid');
    
    if (page === 1) {
        videoGrid.innerHTML = '';
        loadingElement.style.display = 'block';
    }
    
    try {
        const response = await API.video.getFeed(page, currentState.pageSize);
        const { videos, total, total_pages } = response.data;
        
        if (page === 1) {
            videoGrid.innerHTML = '';
        }
        
        videos.forEach(video => {
            const videoCard = createVideoCard(video);
            videoGrid.appendChild(videoCard);
        });
        
        // 添加分页控件
        if (page === 1 || !document.querySelector('.pagination')) {
            const pagination = createPagination(
                page,
                total_pages,
                loadVideoFeed
            );
            
            // 移除旧的 pagination
            const oldPagination = videoGrid.parentNode.querySelector('.pagination');
            if (oldPagination) {
                oldPagination.remove();
            }
            
            videoGrid.parentNode.appendChild(pagination);
        }
        
        currentState.currentSection = 'feed';
        
    } catch (error) {
        if (error.message.includes('认证')) {
            showLoginModal();
        }
    } finally {
        loadingElement.style.display = 'none';
        currentState.loading = false;
    }
}

// 创建视频卡片
function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.onclick = () => showVideoDetail(video.id);
    
    // 缩略图
    const thumbnail = document.createElement('div');
    thumbnail.className = 'video-thumbnail';
    
    if (video.cover_url) {
        const img = document.createElement('img');
        img.src = video.cover_url;
        img.alt = video.title;
        thumbnail.appendChild(img);
    } else {
        thumbnail.innerHTML = '<i class="fas fa-video fa-3x" style="color: #ccc;"></i>';
    }
    
    // 视频时长
    if (video.duration) {
        const duration = document.createElement('span');
        duration.className = 'duration';
        duration.textContent = formatDuration(video.duration);
        thumbnail.appendChild(duration);
    }
    
    card.appendChild(thumbnail);
    
    // 视频信息
    const info = document.createElement('div');
    info.className = 'video-info';
    
    const title = document.createElement('h3');
    title.className = 'video-title';
    title.textContent = video.title || '无标题';
    info.appendChild(title);
    
    const meta = document.createElement('div');
    meta.className = 'video-meta';
    
    // 作者信息
    const author = document.createElement('div');
    author.className = 'author';
    
    if (video.author) {
        const avatar = document.createElement('img');
        avatar.className = 'author-avatar';
        const authorUsername = video.author.username || video.author.user_name || '用户';
        const authorAvatar = video.author.avatar || '';
        
        if (authorAvatar) {
            avatar.src = authorAvatar;
            avatar.alt = authorUsername;
        } else {
            avatar.classList.add('avatar-placeholder');
            avatar.textContent = authorUsername.charAt(0).toUpperCase();
        }
        author.appendChild(avatar);
        
        const name = document.createElement('span');
        name.textContent = authorUsername;
        name.onclick = (e) => {
            e.stopPropagation();
            showUserProfile(video.author.id);
        };
        author.appendChild(name);
    } else {
        author.innerHTML = '<i class="fas fa-user"></i> <span>未知作者</span>';
    }
    
    meta.appendChild(author);
    
    // 视频统计
    const stats = document.createElement('div');
    stats.className = 'video-stats';
    
    const viewCount = document.createElement('span');
    viewCount.innerHTML = `<i class="fas fa-eye"></i> ${formatCount(video.view_count || 0)}`;
    stats.appendChild(viewCount);
    
    const favoriteCount = document.createElement('span');
    favoriteCount.innerHTML = `<i class="fas fa-heart"></i> ${formatCount(video.favorite_count || 0)}`;
    stats.appendChild(favoriteCount);
    
    meta.appendChild(stats);
    
    info.appendChild(meta);
    card.appendChild(info);
    
    return card;
}

// 加载视频详情
async function loadVideoDetail(videoId) {
    const content = document.getElementById('videoDetailContent');
    if (!content) return;
    
    // 保存videoId到全局状态，以便后续使用
    window.currentVideoId = videoId;
    
    content.innerHTML = '<div class="loading"><div class="spinner"></div><span>正在加载视频详情...</span></div>';
    
    try {
        const response = await API.video.getDetail(videoId);
        const video = response.data;
        
        // 加载点赞状态
        let isFavorited = false;
        try {
            const favoriteResponse = await API.favorite.getFavoriteStatus(videoId);
            isFavorited = favoriteResponse.data.is_favorited;
        } catch (error) {
            // 忽略错误，用户可能未登录
        }
        
        // 加载关注状态（如果作者不是当前用户且已登录）
        let isFollowing = false;
        if (video.author && isLoggedIn() && currentState.user && currentState.user.id !== video.author.id) {
            try {
                const followStatusResponse = await API.relation.getFollowStatus(video.author.id);
                isFollowing = followStatusResponse.data.is_following;
            } catch (error) {
                // 忽略错误
            }
        }
        
        // 生成HTML时传入关注状态
        content.innerHTML = generateVideoDetailHTML(video, isFavorited, isFollowing);
        
        // 加载评论
        loadVideoComments(videoId);
        
    } catch (error) {
        content.innerHTML = `<div class="message message-error">加载失败：${error.message}</div>`;
    }
}

// 在视频详情页面切换关注状态
async function toggleFollowInVideoDetail(userId, buttonElement) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    try {
        const isFollowing = buttonElement.classList.contains('btn-primary');
        
        if (isFollowing) {
            await API.relation.unfollowUser(userId);
            buttonElement.classList.remove('btn-primary');
            buttonElement.classList.add('btn-outline');
            buttonElement.innerHTML = '<i class="fas fa-user-plus"></i> 关注';
            showMessage('已取消关注', 'success');
        } else {
            await API.relation.followUser(userId);
            buttonElement.classList.remove('btn-outline');
            buttonElement.classList.add('btn-primary');
            buttonElement.innerHTML = '<i class="fas fa-user-check"></i> 已关注';
            showMessage('关注成功！', 'success');
        }
        
        // 重新加载视频详情以更新作者的关注数和粉丝数
        const videoId = window.currentVideoId;
        if (videoId) {
            await loadVideoDetail(videoId);
        } else {
            // 如果找不到videoId，尝试更新作者信息
            try {
                const userResponse = await API.user.getUserInfo(userId);
                const user = userResponse.data;
                const authorSection = document.querySelector('.author-section');
                if (authorSection) {
                    const statsElement = authorSection.querySelector('.author-stats');
                    if (statsElement) {
                        statsElement.textContent = `关注 ${formatCount(user.follow_count || 0)} | 粉丝 ${formatCount(user.follower_count || 0)}`;
                    }
                }
            } catch (error) {
                // 忽略错误
            }
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 生成视频详情HTML
function generateVideoDetailHTML(video, isFavorited, isFollowing = false) {
    // 检查是否是当前用户
    const isCurrentUser = currentState.user && video.author && currentState.user.id === video.author.id;
    
    // 生成关注按钮HTML（如果不是当前用户且已登录）
    let followButtonHTML = '';
    if (video.author && !isCurrentUser && isLoggedIn()) {
        const followButtonClass = isFollowing ? 'btn-primary' : 'btn-outline';
        const followButtonIcon = isFollowing ? 'fa-user-check' : 'fa-user-plus';
        const followButtonText = isFollowing ? '已关注' : '关注';
        followButtonHTML = `
            <button class="btn ${followButtonClass}" 
                    onclick="toggleFollowInVideoDetail(${video.author.id}, this)"
                    id="followBtn_video_${video.author.id}">
                <i class="fas ${followButtonIcon}"></i> ${followButtonText}
            </button>
        `;
    }
    
    return `
        <div class="video-detail-container">
            <div class="video-player">
                <video controls poster="${video.cover_url || ''}" style="width: 100%; max-height: 400px; background: #000;">
                    <source src="${video.play_url}" type="video/mp4">
                    您的浏览器不支持视频播放。
                </video>
            </div>
            
            <div class="video-info-detailed">
                <h2>${video.title || '无标题'}</h2>
                <p class="video-description">${video.description || '无描述'}</p>
                
                <div class="video-meta-detailed">
                    <div class="author-section">
                        ${video.author ? `
                            <img src="${video.author.avatar || ''}" alt="${video.author.username || video.author.user_name || '用户'}" 
                                 class="author-avatar-large ${!video.author.avatar ? 'avatar-placeholder' : ''}"
                                 onclick="showUserProfile(${video.author.id})" 
                                 style="cursor: pointer;">
                            <div>
                                <div class="author-name" onclick="showUserProfile(${video.author.id})" style="cursor: pointer;">${video.author.username || video.author.user_name || '用户'}</div>
                                <div class="author-stats">关注 ${formatCount(video.author.follow_count || 0)} | 粉丝 ${formatCount(video.author.follower_count || 0)}</div>
                            </div>
                            ${followButtonHTML}
                        ` : '<div>未知作者</div>'}
                    </div>
                    
                    <div class="video-actions">
                        <button class="btn ${isFavorited ? 'btn-danger' : 'btn-outline'}" 
                                onclick="toggleFavorite(${video.id}, this)">
                            <i class="fas fa-heart"></i> 
                            <span>${isFavorited ? '已点赞' : '点赞'}</span>
                            <span> (${formatCount(video.favorite_count || 0)})</span>
                        </button>
                        
                        <span class="video-views">
                            <i class="fas fa-eye"></i> ${formatCount(video.view_count || 0)} 次观看
                        </span>
                        
                        <span class="video-date">
                            <i class="fas fa-clock"></i> ${formatDate(video.created_at)}
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="comments-section">
                <h3>评论 (${video.comment_count || 0})</h3>
                <div id="commentForm" class="comment-form">
                    <textarea placeholder="写下你的评论..." id="commentContent"></textarea>
                    <button class="btn btn-primary" onclick="submitComment(${video.id})">发表评论</button>
                </div>
                <div id="commentsList" class="comments-list">
                    <!-- 评论将通过JavaScript动态加载 -->
                </div>
            </div>
        </div>
    `;
}

// 加载视频评论
async function loadVideoComments(videoId, page = 1) {
    const commentsList = document.getElementById('commentsList');
    if (!commentsList) return;
    
    try {
        const response = await API.comment.getVideoComments(videoId, page, 20);
        const { comments, total } = response.data;
        
        if (comments.length === 0) {
            commentsList.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">暂无评论</p>';
            return;
        }
        
        commentsList.innerHTML = comments.map(comment => {
            // 后端返回的用户信息在comment对象的顶层，不是嵌套在user中
            const username = comment.username || comment.user?.username || comment.user?.user_name || '匿名用户';
            const avatar = comment.avatar || comment.user?.avatar || '';
            const hasAvatar = !!avatar;
            
            return `
            <div class="comment-item">
                <div class="comment-author">
                    ${hasAvatar ? 
                        `<img src="${avatar}" alt="${username}" class="comment-avatar">` :
                        `<div class="comment-avatar avatar-placeholder">${username.charAt(0).toUpperCase()}</div>`
                    }
                    <span class="comment-username">${username}</span>
                    <span class="comment-time">${formatDate(comment.created_at)}</span>
                </div>
                <div class="comment-content">${comment.content || ''}</div>
            </div>
            `;
        }).join('');
    } catch (error) {
        commentsList.innerHTML = `<div class="message message-error">加载评论失败：${error.message}</div>`;
    }
}

// 提交评论
async function submitComment(videoId) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    const contentInput = document.getElementById('commentContent');
    const content = contentInput.value.trim();
    
    if (!content) {
        showMessage('请输入评论内容', 'error');
        return;
    }
    
    try {
        await API.comment.createComment(videoId, content);
        contentInput.value = '';
        showMessage('评论发表成功！', 'success');
        loadVideoComments(videoId);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 切换点赞状态
async function toggleFavorite(videoId, buttonElement) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    try {
        const isFavorited = buttonElement.classList.contains('btn-danger');
        
        if (isFavorited) {
            await API.favorite.unfavoriteVideo(videoId);
            buttonElement.classList.remove('btn-danger');
            buttonElement.classList.add('btn-outline');
            buttonElement.querySelector('span').textContent = '点赞';
            showMessage('已取消点赞', 'success');
        } else {
            await API.favorite.favoriteVideo(videoId);
            buttonElement.classList.remove('btn-outline');
            buttonElement.classList.add('btn-danger');
            buttonElement.querySelector('span').textContent = '已点赞';
            showMessage('点赞成功！', 'success');
        }
        
        // 重新加载视频详情以更新点赞数
        loadVideoDetail(videoId);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 加载我的视频列表
async function loadMyVideos(page = 1) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    const loadingElement = document.getElementById('loading');
    const videoGrid = document.getElementById('videoGrid');
    
    videoGrid.innerHTML = '';
    loadingElement.style.display = 'block';
    
    try {
        const response = await API.video.getMyVideos(page, currentState.pageSize);
        const { videos, total, total_pages } = response.data;
        
        if (videos.length === 0) {
            videoGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                    <i class="fas fa-video fa-4x" style="color: #ccc; margin-bottom: 20px;"></i>
                    <h3>还没有视频</h3>
                    <p>上传你的第一个视频来开始分享吧！</p>
                    <button class="btn btn-primary mt-3" onclick="showUploadModal()">
                        <i class="fas fa-upload"></i> 上传视频
                    </button>
                </div>
            `;
        } else {
            videos.forEach(video => {
                const videoCard = createVideoCardWithActions(video);
                videoGrid.appendChild(videoCard);
            });
        }
        
        // 添加分页控件
        const pagination = createPagination(page, total_pages, loadMyVideos);
        videoGrid.parentNode.appendChild(pagination);
        
        currentState.currentSection = 'my-videos';
        
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        loadingElement.style.display = 'none';
    }
}

// 创建带操作按钮的视频卡片
function createVideoCardWithActions(video) {
    const card = createVideoCard(video);
    
    // 移除点击事件
    card.onclick = null;
    
    // 添加工具栏
    const toolbar = document.createElement('div');
    toolbar.className = 'video-actions-toolbar';
    toolbar.innerHTML = `
        <button onclick="showVideoDetail(${video.id})" title="查看详情">
            <i class="fas fa-eye"></i>
        </button>
        <button onclick="editVideo(${video.id})" title="编辑">
            <i class="fas fa-edit"></i>
        </button>
        <button onclick="deleteVideoConfirm(${video.id})" title="删除">
            <i class="fas fa-trash"></i>
        </button>
    `;
    
    card.appendChild(toolbar);
    return card;
}

// 编辑视频
async function editVideo(videoId) {
    try {
        const response = await API.video.getDetail(videoId);
        const video = response.data;
        
        document.getElementById('videoTitle').value = video.title || '';
        document.getElementById('videoDescription').value = video.description || '';
        showUploadModal();
        
        // 这里可以添加一个编辑模式标记
        window.editingVideoId = videoId;
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 删除视频确认
function deleteVideoConfirm(videoId) {
    if (confirm('确定要删除这个视频吗？')) {
        deleteVideo(videoId);
    }
}

// 删除视频
async function deleteVideo(videoId) {
    try {
        await API.video.deleteVideo(videoId);
        showMessage('视频删除成功', 'success');
        loadMyVideos();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 加载我的点赞列表
async function loadMyFavorites(page = 1) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    const loadingElement = document.getElementById('loading');
    const videoGrid = document.getElementById('videoGrid');
    
    videoGrid.innerHTML = '';
    loadingElement.style.display = 'block';
    
    try {
        const response = await API.favorite.getMyFavorites(page, currentState.pageSize);
        const { favorites, total, total_pages } = response.data;
        
        if (favorites.length === 0) {
            videoGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                    <i class="fas fa-heart fa-4x" style="color: #ccc; margin-bottom: 20px;"></i>
                    <h3>还没有点赞</h3>
                    <p>去发现一些精彩的视频吧！</p>
                </div>
            `;
        } else {
            favorites.forEach(favorite => {
                // 这里需要获取完整的视频信息
                loadVideoCardByFavorite(favorite, videoGrid);
            });
        }
        
        // 添加分页控件
        const pagination = createPagination(page, total_pages, loadMyFavorites);
        videoGrid.parentNode.appendChild(pagination);
        
        currentState.currentSection = 'favorites';
        
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        loadingElement.style.display = 'none';
    }
}

// 通过点赞记录加载视频卡片
async function loadVideoCardByFavorite(favorite, videoGrid) {
    try {
        const response = await API.video.getDetail(favorite.video_id);
        const videoCard = createVideoCard(response.data);
        videoGrid.appendChild(videoCard);
    } catch (error) {
        console.error('加载视频卡片失败:', error);
    }
}

// 加载关注管理页面
async function loadFollowingPage() {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    const mainContent = document.querySelector('.main-content');
    mainContent.innerHTML = `
        <div class="following-tabs">
            <div class="tab-header">
                <button class="tab-btn active" onclick="loadFollowingList()">我的关注</button>
                <button class="tab-btn" onclick="loadFollowerList()">我的粉丝</button>
                <button class="tab-btn" onclick="loadMutualList()">互相关注</button>
            </div>
            <div class="tab-content" id="followingContent">
                <div class="loading">
                    <div class="spinner"></div>
                    <span>加载中...</span>
                </div>
            </div>
        </div>
    `;
    
    // 默认加载关注列表
    loadFollowingList();
}

// 加载关注列表
async function loadFollowingList(page = 1) {
    const content = document.getElementById('followingContent');
    if (!content) return;
    
    content.innerHTML = '<div class="loading"><div class="spinner"></div><span>加载中...</span></div>';
    
    try {
        const response = await API.relation.getMyFollowing(page, 20);
        const { users, total, total_pages } = response.data;
        
        content.innerHTML = `
            <h3>我关注的用户 (${total})</h3>
            <div class="user-list">
                ${users.map(user => createUserCard(user, 'following')).join('')}
            </div>
            ${createPaginationHTML(page, total_pages, loadFollowingList)}
        `;
        
    } catch (error) {
        content.innerHTML = `<div class="message message-error">加载失败：${error.message}</div>`;
    }
}

// 加载粉丝列表
async function loadFollowerList(page = 1) {
    const content = document.getElementById('followingContent');
    if (!content) return;
    
    content.innerHTML = '<div class="loading"><div class="spinner"></div><span>加载中...</span></div>';
    
    try {
        const response = await API.relation.getMyFollowers(page, 20);
        const { users, total, total_pages } = response.data;
        
        content.innerHTML = `
            <h3>我的粉丝 (${total})</h3>
            <div class="user-list">
                ${users.map(user => createUserCard(user, 'follower')).join('')}
            </div>
            ${createPaginationHTML(page, total_pages, loadFollowerList)}
        `;
        
    } catch (error) {
        content.innerHTML = `<div class="message message-error">加载失败：${error.message}</div>`;
    }
}

// 加载互相关注列表
async function loadMutualList(page = 1) {
    const content = document.getElementById('followingContent');
    if (!content) return;
    
    content.innerHTML = '<div class="loading"><div class="spinner"></div><span>加载中...</span></div>';
    
    try {
        const response = await API.relation.getMutualFollowers(page, 20);
        const { users, total, total_pages } = response.data;
        
        content.innerHTML = `
            <h3>互相关注 (${total})</h3>
            <div class="user-list">
                ${users.map(user => createUserCard(user, 'mutual')).join('')}
            </div>
            ${createPaginationHTML(page, total_pages, loadMutualList)}
        `;
        
    } catch (error) {
        content.innerHTML = `<div class="message message-error">加载失败：${error.message}</div>`;
    }
}

// 创建用户卡片
function createUserCard(user, type) {
    const username = user.user_name || user.username || '用户';
    const followBtnText = type === 'follower' ? '关注' : (type === 'mutual' ? '互相关注' : '已关注');
    const followBtnClass = type === 'follower' ? 'btn-outline' : 'btn-primary';
    
    return `
        <div class="user-card">
            <div class="user-info">
                <img src="${user.avatar || ''}" alt="${username}" 
                     class="user-avatar ${!user.avatar ? 'avatar-placeholder' : ''}"
                     onclick="showUserProfile(${user.id})"
                     style="cursor: pointer;">
                <div class="user-details">
                    <h4>${username}</h4>
                    <p>关注 ${formatCount(user.follow_count || 0)} | 粉丝 ${formatCount(user.follower_count || 0)}</p>
                </div>
            </div>
            <div class="user-actions">
                ${type !== 'mutual' ? `
                <button class="btn ${followBtnClass}" 
                        onclick="toggleFollow(${user.id}, this)"
                        data-user-id="${user.id}">
                    <i class="fas fa-user-${type === 'follower' ? 'plus' : 'check'}"></i>
                    ${followBtnText}
                </button>
                ` : '<span class="btn btn-outline" style="cursor: default;"><i class="fas fa-user-check"></i> 互相关注</span>'}
            </div>
        </div>
    `;
}

// 切换关注状态
async function toggleFollow(userId, buttonElement) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    try {
        const isFollowing = buttonElement.classList.contains('btn-primary');
        
        if (isFollowing) {
            await API.relation.unfollowUser(userId);
            buttonElement.classList.remove('btn-primary');
            buttonElement.classList.add('btn-outline');
            buttonElement.innerHTML = '<i class="fas fa-user-plus"></i> 关注';
            showMessage('已取消关注', 'success');
        } else {
            await API.relation.followUser(userId);
            buttonElement.classList.remove('btn-outline');
            buttonElement.classList.add('btn-primary');
            buttonElement.innerHTML = '<i class="fas fa-user-check"></i> 已关注';
            showMessage('关注成功！', 'success');
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 加载用户资料
async function loadUserProfile(userId) {
    const content = document.getElementById('profileContent');
    if (!content) return;
    
    content.innerHTML = '<div class="loading"><div class="spinner"></div><span>加载中...</span></div>';
    
    try {
        let response;
        if (userId === 'me') {
            response = await API.auth.getCurrentUser();
        } else {
            response = await API.user.getUserInfo(userId);
        }
        
        const user = response.data;
        const username = user.username || user.user_name || '用户';
        const avatar = user.avatar || '';
        const isCurrentUser = userId === 'me' || (currentState.user && currentState.user.id === user.id);
        
        // 如果不是当前用户，查询关注状态
        let isFollowing = false;
        let followButtonHTML = '';
        if (!isCurrentUser && isLoggedIn()) {
            try {
                const followStatusResponse = await API.relation.getFollowStatus(user.id);
                isFollowing = followStatusResponse.data.is_following;
            } catch (error) {
                // 忽略错误
            }
            
            followButtonHTML = `
                <button class="btn ${isFollowing ? 'btn-primary' : 'btn-outline'}" 
                        onclick="toggleFollowInProfile(${user.id}, this)"
                        id="followBtn_${user.id}">
                    <i class="fas fa-user-${isFollowing ? 'check' : 'plus'}"></i>
                    ${isFollowing ? '已关注' : '关注'}
                </button>
            `;
        }
        
        // 如果是当前用户，添加上传头像和背景图的按钮
        let editButtonsHTML = '';
        if (isCurrentUser) {
            editButtonsHTML = `
                <div class="profile-edit-actions" style="margin-top: 20px;">
                    <label for="avatarUpload" class="btn btn-outline" style="cursor: pointer; display: inline-block;">
                        <i class="fas fa-image"></i> 更换头像
                        <input type="file" id="avatarUpload" accept="image/*" style="display: none;" onchange="handleAvatarUpload(event)">
                    </label>
                    <label for="bannerUpload" class="btn btn-outline" style="cursor: pointer; display: inline-block; margin-left: 10px;">
                        <i class="fas fa-image"></i> 更换背景图
                        <input type="file" id="bannerUpload" accept="image/*" style="display: none;" onchange="handleBannerUpload(event)">
                    </label>
                </div>
            `;
        }
        
        content.innerHTML = `
            <div class="profile-container">
                <div class="profile-header" style="background-image: ${user.background_image ? `url('${user.background_image}')` : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}; background-size: cover; background-position: center; padding: 40px 20px; border-radius: 12px; margin-bottom: 20px; position: relative;">
                    ${isCurrentUser ? `
                        <label for="bannerUploadHeader" style="position: absolute; top: 10px; right: 10px; cursor: pointer; background: rgba(0,0,0,0.5); padding: 8px 12px; border-radius: 6px; color: white;">
                            <i class="fas fa-camera"></i>
                            <input type="file" id="bannerUploadHeader" accept="image/*" style="display: none;" onchange="handleBannerUpload(event)">
                        </label>
                    ` : ''}
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="position: relative;">
                            ${avatar ? 
                                `<img src="${avatar}" alt="${username}" class="profile-avatar" style="width: 100px; height: 100px; border-radius: 50%; border: 4px solid white; object-fit: cover;">` :
                                `<div class="profile-avatar avatar-placeholder" style="width: 100px; height: 100px; border-radius: 50%; border: 4px solid white; display: flex; align-items: center; justify-content: center; font-size: 40px; background: linear-gradient(45deg, #007bff, #0056b3); color: white;">${username.charAt(0).toUpperCase()}</div>`
                            }
                            ${isCurrentUser ? `
                                <label for="avatarUploadHeader" style="position: absolute; bottom: 0; right: 0; cursor: pointer; background: #007bff; padding: 6px; border-radius: 50%; color: white; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas fa-camera" style="font-size: 14px;"></i>
                                    <input type="file" id="avatarUploadHeader" accept="image/*" style="display: none;" onchange="handleAvatarUpload(event)">
                                </label>
                            ` : ''}
                        </div>
                        <div>
                            <h2 style="color: white; margin: 0;">${username}</h2>
                            <p style="color: rgba(255,255,255,0.9); margin: 5px 0;">关注 ${formatCount(user.follow_count || 0)} | 粉丝 ${formatCount(user.follower_count || 0)}</p>
                            ${followButtonHTML}
                        </div>
                    </div>
                </div>
                <div class="profile-content">
                    <h3>用户信息</h3>
                    <p>角色: ${user.userRole || 'user'}</p>
                    ${editButtonsHTML}
                </div>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<div class="message message-error">加载失败：${error.message}</div>`;
    }
}

// 在用户资料页面切换关注状态
async function toggleFollowInProfile(userId, buttonElement) {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    try {
        const isFollowing = buttonElement.classList.contains('btn-primary');
        
        if (isFollowing) {
            await API.relation.unfollowUser(userId);
            buttonElement.classList.remove('btn-primary');
            buttonElement.classList.add('btn-outline');
            buttonElement.innerHTML = '<i class="fas fa-user-plus"></i> 关注';
            showMessage('已取消关注', 'success');
        } else {
            await API.relation.followUser(userId);
            buttonElement.classList.remove('btn-outline');
            buttonElement.classList.add('btn-primary');
            buttonElement.innerHTML = '<i class="fas fa-user-check"></i> 已关注';
            showMessage('关注成功！', 'success');
        }
        
        // 重新加载用户资料以更新关注数和粉丝数
        loadUserProfile(userId);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 上传头像
async function handleAvatarUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showMessage('不支持的文件格式，请选择 JPG、PNG、GIF 或 WebP 格式的图片', 'error');
        return;
    }
    
    // 验证文件大小（5MB）
    if (file.size > 5 * 1024 * 1024) {
        showMessage('文件大小不能超过 5MB', 'error');
        return;
    }
    
    try {
        showMessage('正在上传头像...', 'info');
        const response = await API.user.uploadAvatar(file);
        
        showMessage('头像上传成功！', 'success');
        
        // 重新加载用户资料
        await loadUserProfile('me');
        
        // 更新导航栏中的头像
        await loadCurrentUser();
        
    } catch (error) {
        showMessage(error.message || '上传头像失败', 'error');
    }
    
    // 清空文件输入
    event.target.value = '';
}

// 上传背景图
async function handleBannerUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showMessage('不支持的文件格式，请选择 JPG、PNG、GIF 或 WebP 格式的图片', 'error');
        return;
    }
    
    // 验证文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
        showMessage('文件大小不能超过 10MB', 'error');
        return;
    }
    
    try {
        showMessage('正在上传背景图...', 'info');
        const response = await API.user.uploadBanner(file);
        
        showMessage('背景图上传成功！', 'success');
        
        // 重新加载用户资料
        await loadUserProfile('me');
        
    } catch (error) {
        showMessage(error.message || '上传背景图失败', 'error');
    }
    
    // 清空文件输入
    event.target.value = '';
}

// 创建分页HTML
function createPaginationHTML(currentPage, totalPages, callback) {
    if (totalPages <= 1) return '';
    
    return `
        <div class="pagination">
            <button class="pagination-btn" ${currentPage <= 1 ? 'disabled' : ''} 
                    onclick="${currentPage > 1 ? callback.name + '(' + (currentPage - 1) + ')' : ''}">
                <i class="fas fa-chevron-left"></i>
            </button>
            <span>${currentPage} / ${totalPages}</span>
            <button class="pagination-btn" ${currentPage >= totalPages ? 'disabled' : ''}
                    onclick="${currentPage < totalPages ? callback.name + '(' + (currentPage + 1) + ')' : ''}">
                <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    `;
}

// 工具函数
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatCount(count) {
    if (count >= 1000000) {
        return (count / 1000000).toFixed(1) + 'M';
    } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'K';
    }
    return count.toString();
}

function formatDate(dateString) {
    if (!dateString) return '未知时间';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) {
        return '刚刚';
    } else if (diff < 3600000) {
        return Math.floor(diff / 60000) + '分钟前';
    } else if (diff < 86400000) {
        return Math.floor(diff / 3600000) + '小时前';
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

// 搜索功能
let currentSearchQuery = '';
let currentSearchPage = 1;

async function performSearch(query = null) {
    const searchInput = document.getElementById('searchInput');
    const queryText = query || searchInput.value.trim();
    
    if (!queryText) {
        // 如果没有搜索词，返回视频流
        loadVideoFeed();
        updateSectionTitle('精彩视频');
        return;
    }
    
    currentSearchQuery = queryText;
    currentSearchPage = 1;
    
    const loadingElement = document.getElementById('loading');
    const videoGrid = document.getElementById('videoGrid');
    
    videoGrid.innerHTML = '';
    loadingElement.style.display = 'block';
    
    try {
        const response = await API.search.searchVideos(queryText, {
            page: currentSearchPage,
            page_size: currentState.pageSize,
            sort: 'relevance'
        });
        
        const { videos, total, total_pages } = response.data;
        
        if (videos.length === 0) {
            videoGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                    <i class="fas fa-search fa-4x" style="color: #ccc; margin-bottom: 20px;"></i>
                    <h3>没有找到相关视频</h3>
                    <p>试试其他关键词吧</p>
                </div>
            `;
        } else {
            videos.forEach(video => {
                const videoCard = createSearchVideoCard(video);
                videoGrid.appendChild(videoCard);
            });
            
            // 添加分页控件
            const pagination = createPagination(currentSearchPage, total_pages, (page) => {
                currentSearchPage = page;
                performSearch();
            });
            
            const oldPagination = videoGrid.parentNode.querySelector('.pagination');
            if (oldPagination) {
                oldPagination.remove();
            }
            
            videoGrid.parentNode.appendChild(pagination);
        }
        
        updateSectionTitle(`搜索结果: "${queryText}" (${total}个结果)`);
        currentState.currentSection = 'search';
        
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        loadingElement.style.display = 'none';
    }
}

// 创建搜索结果视频卡片（支持高亮）
function createSearchVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.onclick = () => showVideoDetail(video.id);
    
    // 缩略图
    const thumbnail = document.createElement('div');
    thumbnail.className = 'video-thumbnail';
    
    if (video.cover_url) {
        const img = document.createElement('img');
        img.src = video.cover_url;
        img.alt = video.title;
        thumbnail.appendChild(img);
    } else {
        thumbnail.innerHTML = '<i class="fas fa-video fa-3x" style="color: #ccc;"></i>';
    }
    
    // 视频时长
    if (video.duration) {
        const duration = document.createElement('span');
        duration.className = 'duration';
        duration.textContent = formatDuration(video.duration);
        thumbnail.appendChild(duration);
    }
    
    card.appendChild(thumbnail);
    
    // 视频信息
    const info = document.createElement('div');
    info.className = 'video-info';
    
    const title = document.createElement('h3');
    title.className = 'video-title';
    // 如果有高亮，使用高亮内容，否则使用原始标题
    if (video.highlight && video.highlight.title && video.highlight.title.length > 0) {
        title.innerHTML = video.highlight.title[0];
    } else {
        title.textContent = video.title || '无标题';
    }
    info.appendChild(title);
    
    // 描述（如果有高亮）
    if (video.highlight && video.highlight.description && video.highlight.description.length > 0) {
        const desc = document.createElement('p');
        desc.className = 'video-description-preview';
        desc.innerHTML = video.highlight.description[0];
        info.appendChild(desc);
    }
    
    const meta = document.createElement('div');
    meta.className = 'video-meta';
    
    // 作者信息
    const author = document.createElement('div');
    author.className = 'author';
    
    if (video.author_name) {
        const name = document.createElement('span');
        name.textContent = video.author_name;
        author.appendChild(name);
    } else {
        author.innerHTML = '<i class="fas fa-user"></i> <span>未知作者</span>';
    }
    
    meta.appendChild(author);
    
    // 视频统计
    const stats = document.createElement('div');
    stats.className = 'video-stats';
    
    const viewCount = document.createElement('span');
    viewCount.innerHTML = `<i class="fas fa-eye"></i> ${formatCount(video.view_count || 0)}`;
    stats.appendChild(viewCount);
    
    const favoriteCount = document.createElement('span');
    favoriteCount.innerHTML = `<i class="fas fa-heart"></i> ${formatCount(video.favorite_count || 0)}`;
    stats.appendChild(favoriteCount);
    
    meta.appendChild(stats);
    
    info.appendChild(meta);
    card.appendChild(info);
    
    return card;
}

// Agent对话功能
let currentChatId = null;

function generateChatId() {
    return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function sendChatMessage() {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // 初始化chat_id
    if (!currentChatId) {
        currentChatId = generateChatId();
    }
    
    // 添加用户消息到界面
    addChatMessage('user', message);
    chatInput.value = '';
    
    // 禁用发送按钮
    const sendBtn = document.getElementById('sendChatBtn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 发送中...';
    
    // 添加AI回复占位符
    const botMessageId = `bot-${Date.now()}`;
    addChatMessage('bot', '', botMessageId);
    const botMessageElement = document.getElementById(botMessageId);
    const botContentElement = botMessageElement.querySelector('.message-content');
    
    try {
        // 使用流式API
        let fullReply = '';
        
        await API.agent.stream(
            message,
            currentChatId,
            (chunk) => {
                // 接收流式数据块
                fullReply += chunk;
                botContentElement.innerHTML = `<p>${escapeHtml(fullReply)}</p>`;
                // 滚动到底部
                scrollChatToBottom();
            },
            (chatId) => {
                // 完成
                currentChatId = chatId;
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 发送';
            },
            (error) => {
                // 错误处理
                botContentElement.innerHTML = `<p style="color: #dc3545;">错误: ${escapeHtml(error.message)}</p>`;
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 发送';
            }
        );
    } catch (error) {
        // 如果流式API失败，尝试同步API
        try {
            const response = await API.agent.invoke(message, currentChatId);
            if (response.code === 200 && response.ai_reply) {
                botContentElement.innerHTML = `<p>${escapeHtml(response.ai_reply)}</p>`;
                currentChatId = response.chat_id || currentChatId;
            } else {
                botContentElement.innerHTML = `<p style="color: #dc3545;">${escapeHtml(response.message || '请求失败')}</p>`;
            }
        } catch (e) {
            botContentElement.innerHTML = `<p style="color: #dc3545;">错误: ${escapeHtml(e.message)}</p>`;
        }
        
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 发送';
    }
}

function addChatMessage(role, content, messageId = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    if (messageId) {
        messageDiv.id = messageId;
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    if (role === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }
    messageDiv.appendChild(avatar);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    if (content) {
        contentDiv.innerHTML = `<p>${escapeHtml(content)}</p>`;
    }
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}