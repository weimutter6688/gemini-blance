function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    } else {
        return new Promise((resolve, reject) => {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (successful) {
                    resolve();
                } else {
                    reject(new Error('复制失败'));
                }
            } catch (err) {
                document.body.removeChild(textArea);
                reject(err);
            }
        });
    }
}

function copyKeys(type) {
    const keys = Array.from(document.querySelectorAll(`#${type}Keys .key-text`)).map(span => span.dataset.fullKey);
    const jsonKeys = JSON.stringify(keys);
    
    copyToClipboard(jsonKeys)
        .then(() => {
            showCopyStatus(`已成功复制${type === 'valid' ? '有效' : '无效'}密钥到剪贴板`);
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showCopyStatus('复制失败，请重试');
        });
}

function copyKey(key) {
    copyToClipboard(key)
        .then(() => {
            showCopyStatus(`已成功复制密钥到剪贴板`);
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showCopyStatus('复制失败，请重试');
        });
}

function showCopyStatus(message, type = 'success') {
    const statusElement = document.getElementById('copyStatus');
    statusElement.textContent = message;
    statusElement.className = type; // 设置样式类
    statusElement.style.opacity = 1;
    setTimeout(() => {
        statusElement.style.opacity = 0;
        setTimeout(() => {
            statusElement.className = ''; // 清除样式类
        }, 300);
    }, 2000);
}

async function verifyKey(key, button) {
    try {
        // 禁用按钮并显示加载状态
        button.disabled = true;
        const originalHtml = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 验证中';

        const response = await fetch(`/gemini/v1beta/verify-key/${key}`, {
            method: 'POST'
        });
        const data = await response.json();

        // 根据验证结果更新UI
        if (data.status === 'valid') {
            showCopyStatus('密钥验证成功', 'success');
            button.style.backgroundColor = '#27ae60';
        } else {
            showCopyStatus('密钥验证失败', 'error');
            button.style.backgroundColor = '#e74c3c';
        }

        // 3秒后恢复按钮原始状态
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.disabled = false;
            button.style.backgroundColor = '';
        }, 3000);

    } catch (error) {
        console.error('验证失败:', error);
        showCopyStatus('验证请求失败', 'error');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-check-circle"></i> 验证';
    }
}

function scrollToTop() {
    const container = document.querySelector('.container');
    container.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function scrollToBottom() {
    const container = document.querySelector('.container');
    container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
    });
}

function updateScrollButtons() {
    const container = document.querySelector('.container');
    const scrollButtons = document.querySelector('.scroll-buttons');
    if (container.scrollHeight > container.clientHeight) {
        scrollButtons.style.display = 'flex';
    } else {
        scrollButtons.style.display = 'none';
    }
}

function refreshPage(button) {
    button.classList.add('loading');
    button.disabled = true;
    
    setTimeout(() => {
        window.location.reload();
    }, 300);
}

function toggleSection(header, sectionId) {
    const toggleIcon = header.querySelector('.toggle-icon');
    const content = header.nextElementSibling;
    
    toggleIcon.classList.toggle('collapsed');
    content.classList.toggle('collapsed');
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查滚动按钮
    updateScrollButtons();

    // 监听展开/折叠事件
    document.querySelectorAll('.key-list h2').forEach(header => {
        header.addEventListener('click', () => {
            setTimeout(updateScrollButtons, 300);
        });
    });

    // 更新版权年份
    const copyrightYear = document.querySelector('.copyright script');
    if (copyrightYear) {
        copyrightYear.textContent = new Date().getFullYear();
    }
});

// Service Worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker注册成功:', registration.scope);
            })
            .catch(error => {
                console.log('ServiceWorker注册失败:', error);
            });
    });
}
function toggleKeyVisibility(button) {
    const keyInfoDiv = button.closest('.key-info');
    const keyTextSpan = keyInfoDiv.querySelector('.key-text');
    const eyeIcon = button.querySelector('i');
    const fullKey = keyTextSpan.dataset.fullKey;
    const maskedKey = fullKey.substring(0, 4) + '...' + fullKey.substring(fullKey.length - 4);

    if (keyTextSpan.textContent === maskedKey) {
        keyTextSpan.textContent = fullKey;
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
        button.title = '隐藏密钥';
    } else {
        keyTextSpan.textContent = maskedKey;
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
        button.title = '显示密钥';
    }
}
