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
    
    if (keys.length === 0) {
        showCopyStatus('没有可复制的密钥', true);
        return;
    }
    
    const keysText = keys.join('\n');
    
    copyToClipboard(keysText)
        .then(() => {
            showCopyStatus(`已成功复制${keys.length}个${type === 'valid' ? '有效' : '无效'}密钥到剪贴板`);
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showCopyStatus('复制失败，请重试', true);
        });
}

function copyKey(key) {
    copyToClipboard(key)
        .then(() => {
            showCopyStatus(`已成功复制密钥到剪贴板`);
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showCopyStatus('复制失败，请重试', true);
        });
}

function showCopyStatus(message, isError = false) {
    const statusElement = document.getElementById('copyStatus');
    statusElement.textContent = message;
    
    // 添加适当的样式类
    if (isError) {
        statusElement.classList.add('bg-danger-500');
        statusElement.classList.remove('bg-black');
    } else {
        statusElement.classList.remove('bg-danger-500');
        statusElement.classList.add('bg-black');
    }
    
    // 应用过渡效果
    statusElement.style.opacity = "1";
    statusElement.style.transform = "translate(-50%, 0)";
    
    // 设置自动消失
    setTimeout(() => {
        statusElement.style.opacity = "0";
        statusElement.style.transform = "translate(-50%, 10px)";
    }, 3000);
}

async function verifyKey(key, button) {
    try {
        // 禁用按钮并显示加载状态
        button.disabled = true;
        const originalHtml = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 验证中';

        try {
            const response = await fetch(`/gemini/v1beta/verify-key/${key}`, {
                method: 'POST'
            });
            const data = await response.json();

            // 根据验证结果更新UI并显示模态提示框
            if (data.success || data.status === 'valid') {
                // 验证成功，显示成功结果
                button.style.backgroundColor = '#27ae60';
                // 使用结果模态框显示成功消息
                showResultModal(true, '密钥验证成功');
                // 模态框关闭时会自动刷新页面
            } else {
                // 验证失败，显示失败结果
                const errorMsg = data.error || '密钥无效';
                button.style.backgroundColor = '#e74c3c';
                // 使用结果模态框显示失败消息，但不自动刷新页面
                showResultModal(false, '密钥验证失败: ' + errorMsg, true); // 改为true以在关闭时刷新
            }
        } catch (fetchError) {
            console.error('API请求失败:', fetchError);
            showResultModal(false, '验证请求失败: ' + fetchError.message, true); // 改为true以在关闭时刷新
        } finally {
            // 1秒后恢复按钮原始状态
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
                button.style.backgroundColor = '';
            }, 1000);
        }
    } catch (error) {
        console.error('验证失败:', error);
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-check-circle"></i> 验证';
        showResultModal(false, '验证处理失败: ' + error.message, true); // 改为true以在关闭时刷新
    }
}

async function resetKeyFailCount(key, button) {
    try {
        // 禁用按钮并显示加载状态
        button.disabled = true;
        const originalHtml = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 重置中';

        const response = await fetch(`/gemini/v1beta/reset-fail-count/${key}`, {
            method: 'POST'
        });
        const data = await response.json();

        // 根据重置结果更新UI
        if (data.success) {
            showCopyStatus('失败计数重置成功');
            button.style.backgroundColor = '#27ae60';
            setTimeout(() => location.reload(), 1500);
        } else {
            const errorMsg = data.message || '重置失败';
            showCopyStatus('重置失败: ' + errorMsg, true);
            button.style.backgroundColor = '#e74c3c';
        }

        // 1秒后恢复按钮原始状态
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.disabled = false;
            button.style.backgroundColor = '';
        }, 1000);

    } catch (error) {
        console.error('重置失败:', error);
        showCopyStatus('重置请求失败: ' + error.message, true);
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-redo-alt"></i> 重置';
    }
}

function showResetModal(type) {
    const modalElement = document.getElementById('resetModal');
    const titleElement = document.getElementById('resetModalTitle');
    const messageElement = document.getElementById('resetModalMessage');
    const confirmButton = document.getElementById('confirmResetBtn');
    
    // 设置标题和消息
    titleElement.textContent = '批量重置失败次数';
    messageElement.textContent = `确定要批量重置${type === 'valid' ? '有效' : '无效'}密钥的失败次数吗？`;
    
    // 设置确认按钮事件
    confirmButton.onclick = () => executeResetAll(type);
    
    // 显示模态框
    modalElement.classList.remove('hidden');
}

function closeResetModal() {
    document.getElementById('resetModal').classList.add('hidden');
}

// 触发显示模态框
function resetAllKeysFailCount(type, event) {
    // 阻止事件冒泡
    if (event) {
        event.stopPropagation();
    }
    
    // 显示模态确认框
    showResetModal(type);
}

// 执行批量重置
// 关闭模态框并根据参数决定是否刷新页面
function closeResultModal(reload = true) {
    document.getElementById('resultModal').classList.add('hidden');
    if (reload) {
        location.reload(); // 操作完成后刷新页面
    }
}

// 显示操作结果模态框
function showResultModal(success, message, autoReload = true) {
    const modalElement = document.getElementById('resultModal');
    const titleElement = document.getElementById('resultModalTitle');
    const messageElement = document.getElementById('resultModalMessage');
    const iconElement = document.getElementById('resultIcon');
    const confirmButton = document.getElementById('resultModalConfirmBtn');
    
    // 设置标题
    titleElement.textContent = success ? '操作成功' : '操作失败';
    
    // 设置图标
    if (success) {
        iconElement.innerHTML = '<i class="fas fa-check-circle text-success-500"></i>';
        iconElement.className = 'text-5xl mb-3 text-success-500';
    } else {
        iconElement.innerHTML = '<i class="fas fa-times-circle"></i>';
        iconElement.className = 'text-5xl mb-3 text-danger-500';
    }
    
    // 设置消息
    messageElement.textContent = message;
    
    // 设置确认按钮点击事件
    confirmButton.onclick = () => closeResultModal(autoReload);
    
    // 显示模态框
    modalElement.classList.remove('hidden');
}

async function executeResetAll(type) {
    try {
        // 关闭确认模态框
        closeResetModal();
        
        // 使用data-reset-type属性直接找到对应的重置按钮
        const resetButton = document.querySelector(`button[data-reset-type="${type}"]`);
        
        if (!resetButton) {
            // 如果找不到按钮，显示错误并返回
            showResultModal(false, `找不到${type === 'valid' ? '有效' : '无效'}密钥区域的批量重置按钮`);
            return;
        }
        
        // 禁用按钮并显示加载状态
        resetButton.disabled = true;
        const originalHtml = resetButton.innerHTML;
        resetButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 重置中';

        try {
            // 调用API，传递类型参数
            const response = await fetch(`/gemini/v1beta/reset-all-fail-counts?key_type=${type}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`服务器返回错误: ${response.status}`);
            }
            
            const data = await response.json();

            // 根据重置结果显示模态框
            if (data.success) {
                const message = data.reset_count ?
                    `成功重置${data.reset_count}个${type === 'valid' ? '有效' : '无效'}密钥的失败次数` :
                    '所有失败次数重置成功';
                showResultModal(true, message);
            } else {
                const errorMsg = data.message || '批量重置失败';
                showResultModal(false, '批量重置失败: ' + errorMsg);
            }
        } catch (fetchError) {
            console.error('API请求失败:', fetchError);
            showResultModal(false, '批量重置请求失败: ' + fetchError.message);
        } finally {
            // 恢复按钮原始状态
            setTimeout(() => {
                resetButton.innerHTML = originalHtml;
                resetButton.disabled = false;
            }, 500);
        }
    } catch (error) {
        console.error('批量重置失败:', error);
        showResultModal(false, '批量重置处理失败: ' + error.message);
    }
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// 移除这个函数，因为它可能正在干扰按钮的显示
// HTML中已经设置了滚动按钮为flex显示，不需要JavaScript额外控制
function updateScrollButtons() {
    // 不执行任何操作
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

// 筛选有效密钥（根据失败次数阈值）
function filterValidKeys() {
    const thresholdInput = document.getElementById('failCountThreshold');
    const validKeyItems = document.querySelectorAll('#validKeys li');
    // 读取阈值，如果输入无效或为空，则默认为0（不过滤）
    const threshold = parseInt(thresholdInput.value, 10);
    const filterThreshold = isNaN(threshold) || threshold < 0 ? 0 : threshold;

    validKeyItems.forEach(item => {
        const failCount = parseInt(item.dataset.failCount, 10);
        // 如果失败次数大于等于阈值，则显示，否则隐藏
        if (failCount >= filterThreshold) {
            item.style.display = ''; // 显示
        } else {
            item.style.display = 'none'; // 隐藏
        }
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 移除对滚动按钮显示的控制，让它们由HTML/CSS控制
    
    // 监听展开/折叠事件
    document.querySelectorAll('.key-list h2').forEach(header => {
        header.addEventListener('click', () => {
            // 不再调用updateScrollButtons
        });
    });

    // 更新版权年份
    const copyrightYearElement = document.querySelector('.copyright script');
    if (copyrightYearElement && copyrightYearElement.parentNode.classList.contains('copyright')) {
        // 确保只更新版权部分的年份
        copyrightYearElement.textContent = new Date().getFullYear();
    }

    // 添加筛选输入框事件监听
    const thresholdInput = document.getElementById('failCountThreshold');
    if (thresholdInput) {
        // 使用 'input' 事件实时响应输入变化
        thresholdInput.addEventListener('input', filterValidKeys);
        // 初始加载时应用一次筛选（基于默认值1）
        filterValidKeys();
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
    const keyContainer = button.closest('.flex.items-center.gap-1');
    const keyTextSpan = keyContainer.querySelector('.key-text');
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
