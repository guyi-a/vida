// UI 交互相关功能

// 模态框控制
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // 防止背景滚动
        
        // ESC 键关闭模态框
        document.addEventListener('keydown', handleEscapeKey);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // 移除事件监听
        document.removeEventListener('keydown', handleEscapeKey);
        
        // 重置表单
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

function handleEscapeKey(event) {
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal[style*="display: block"]');
        if (openModals.length > 0) {
            const lastModal = openModals[openModals.length - 1];
            closeModal(lastModal.id);
        }
    }
}

// 关闭模态框的事件处理
function setupModalClose() {
    // 点击模态框背景关闭
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeModal(this.id);
            }
        });
    });
}

// 登录相关
function showLoginModal() {
    closeAllModals();
    showModal('loginModal');
}

function showRegisterModal() {
    closeAllModals();
    showModal('registerModal');
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.style.overflow = '';
}

// 上传视频相关
function showUploadModal() {
    if (!isLoggedIn()) {
        showLoginModal();
        return;
    }
    closeAllModals();
    showModal('uploadModal');
}

// 视频详情相关
function showVideoDetail(videoId) {
    closeAllModals();
    // 保存videoId到全局状态
    window.currentVideoId = videoId;
    loadVideoDetail(videoId);
    showModal('videoDetailModal');
}

// 个人资料相关
function showMyProfile() {
    closeAllModals();
    loadUserProfile('me');
    showModal('profileModal');
}

function showUserProfile(userId) {
    closeAllModals();
    loadUserProfile(userId);
    showModal('profileModal');
}

// 页面导航
function showMyVideos() {
    closeAllModals();
    loadMyVideos();
    updateSectionTitle('我的视频');
}

function showFavorites() {
    closeAllModals();
    loadMyFavorites();
    updateSectionTitle('我的点赞');
}

function showFollowing() {
    closeAllModals();
    loadFollowingPage();
    updateSectionTitle('关注管理');
}

// 更新页面标题
function updateSectionTitle(title) {
    const titleElement = document.querySelector('.section-title');
    if (titleElement) {
        titleElement.textContent = title;
    }
}

// 用户登录状态管理
function isLoggedIn() {
    return !!getToken();
}

function updateLoginState(userData = null) {
    const loginBtn = document.getElementById('loginBtn');
    const userMenu = document.getElementById('userMenu');
    
    if (isLoggedIn() && userData) {
        loginBtn.style.display = 'none';
        userMenu.style.display = 'flex';
        
        const userAvatar = document.getElementById('userAvatar');
        const userName = document.getElementById('userName');
        
        // 兼容不同的字段名
        const username = userData.user_name || userData.username || '用户';
        const avatar = userData.avatar || '';
        
        if (avatar) {
            userAvatar.src = avatar;
            userAvatar.alt = username;
            userAvatar.classList.remove('avatar-placeholder');
        } else {
            userAvatar.src = '';
            userAvatar.style.background = 'linear-gradient(45deg, #007bff, #0056b3)';
            userAvatar.textContent = username.charAt(0).toUpperCase();
            userAvatar.classList.add('avatar-placeholder');
        }
        
        userName.textContent = username;
    } else {
        loginBtn.style.display = 'block';
        userMenu.style.display = 'none';
    }
}

// 退出登录
function logout() {
    API.auth.logout().catch(() => {
        // 即使删除失败也清除本地token
    });
    
    removeToken();
    updateLoginState();
    
    // 刷新页面
    location.reload();
}

// 加载用户信息
async function loadCurrentUser() {
    if (!isLoggedIn()) {
        updateLoginState();
        return;
    }
    
    try {
        const response = await API.auth.getCurrentUser();
        updateLoginState(response.data);
    } catch (error) {
        // Token 可能已过期
        removeToken();
        updateLoginState();
        showLoginModal();
    }
}

// 创建分页控件
function createPagination(currentPage, totalPages, onPageChange) {
    const pagination = document.createElement('div');
    pagination.className = 'pagination';
    
    if (totalPages <= 1) {
        return pagination;
    }
    
    // 上一页
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => currentPage > 1 && onPageChange(currentPage - 1);
    pagination.appendChild(prevBtn);
    
    // 页码
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let page = startPage; page <= endPage; page++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `pagination-btn ${page === currentPage ? 'active' : ''}`;
        pageBtn.textContent = page;
        pageBtn.onclick = () => onPageChange(page);
        pagination.appendChild(pageBtn);
    }
    
    // 下一页
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => currentPage < totalPages && onPageChange(currentPage + 1);
    pagination.appendChild(nextBtn);
    
    return pagination;
}

// 切换用户菜单显示
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

// 窗口点击事件处理
function handleGlobalClicks(event) {
    // 处理用户菜单的点击
    const userMenu = document.getElementById('userMenu');
    const dropdown = document.getElementById('userDropdown');
    if (userMenu && dropdown && !userMenu.contains(event.target)) {
        dropdown.style.display = 'none';
    }
}

// 初始化 UI 事件
function initUIEvents() {
    setupModalClose();
    
    // 全局点击事件
    document.addEventListener('click', handleGlobalClicks);
    
    // 加载当前用户信息
    loadCurrentUser();
    
    // 默认加载视频流
    loadVideoFeed();
    updateSectionTitle('精彩视频');
}

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initUIEvents();
});