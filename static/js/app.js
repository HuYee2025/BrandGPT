/*
 * 餐饮品牌AI顾问 - 前端交互逻辑
 */

// 显示提示消息
function showMessage(message, type = 'info') {
    const flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) return;

    const div = document.createElement('div');
    div.className = `flash-message flash-${type}`;
    div.textContent = message;

    flashContainer.appendChild(div);

    // 3秒后自动移除
    setTimeout(() => {
        div.remove();
    }, 3000);
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }

    // 小于1小时
    if (diff < 3600000) {
        return Math.floor(diff / 60000) + '分钟前';
    }

    // 小于1天
    if (diff < 86400000) {
        return Math.floor(diff / 3600000) + '小时前';
    }

    // 小于7天
    if (diff < 604800000) {
        return Math.floor(diff / 86400000) + '天前';
    }

    // 超过7天
    return date.toLocaleDateString('zh-CN');
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('餐饮品牌AI顾问已加载');

    // 自动聚焦登录输入框
    const firstInput = document.querySelector('.auth-form input');
    if (firstInput) {
        firstInput.focus();
    }
});

// 导出工具函数（供其他脚本使用）
window.utils = {
    showMessage,
    formatDate,
    debounce,
    throttle
};
