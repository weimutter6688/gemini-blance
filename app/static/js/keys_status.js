// 统计数据可视化交互效果

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

// 添加统计项动画效果
function initStatItemAnimations() {
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            item.style.transform = 'scale(1.05)';
            const icon = item.querySelector('.stat-icon');
            if (icon) {
                icon.style.opacity = '0.2';
                icon.style.transform = 'scale(1.1) rotate(0deg)';
            }
        });
        
        item.addEventListener('mouseleave', () => {
            item.style.transform = '';
            const icon = item.querySelector('.stat-icon');
            if (icon) {
                icon.style.opacity = '';
                icon.style.transform = '';
            }
        });
    });
}

function copyKeys(type) {
    // 选择对应区域内所有可见的 li 元素下的 key-text span
    const visibleKeyItems = document.querySelectorAll(`#${type}Keys li:not([style*="display: none"]) .key-text`);
    const keys = Array.from(visibleKeyItems).map(span => span.dataset.fullKey);

    if (keys.length === 0) {
        showNotification('没有可复制的筛选后密钥', 'warning'); // 修改提示信息
        return;
    }

    const keysText = keys.join('\n');

    copyToClipboard(keysText)
        .then(() => {
            showNotification(`已成功复制 ${keys.length} 个筛选后的${type === 'valid' ? '有效' : '无效'}密钥`); // 修改提示信息
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showNotification('复制失败，请重试', 'error');
        });
}

function copyKey(key) {
    copyToClipboard(key)
        .then(() => {
            showNotification(`已成功复制密钥`);
        })
        .catch((err) => {
            console.error('无法复制文本: ', err);
            showNotification('复制失败，请重试', 'error');
        });
}

// 移除 showCopyStatus 函数，因为它已被 showNotification 替代

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
            showNotification('失败计数重置成功');
            // 成功时保留绿色背景一会儿
            button.style.backgroundColor = '#27ae60';
            // 稍后刷新页面
            setTimeout(() => location.reload(), 1000);
        } else {
            const errorMsg = data.message || '重置失败';
            showNotification('重置失败: ' + errorMsg, 'error');
            // 失败时保留红色背景一会儿
            button.style.backgroundColor = '#e74c3c';
        }

        // 立即恢复按钮状态，除非成功或失败时需要短暂显示颜色
        if (!data.success) {
             // 如果失败，1秒后恢复按钮
             setTimeout(() => {
                 button.innerHTML = originalHtml;
                 button.disabled = false;
                 button.style.backgroundColor = '';
             }, 1000);
        } else {
             // 如果成功，在刷新前恢复按钮（虽然用户可能看不到）
             button.innerHTML = originalHtml;
             button.disabled = false;
             // 背景色会在刷新时重置
        }

    } catch (error) {
        console.error('重置失败:', error);
        showNotification('重置请求失败: ' + error.message, 'error');
        // 确保在捕获到错误时恢复按钮状态
        button.innerHTML = originalHtml; // 需要确保 originalHtml 在此作用域可用
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-redo-alt"></i> 重置';
    }
}

function showResetModal(type) {
    const modalElement = document.getElementById('resetModal');
    const titleElement = document.getElementById('resetModalTitle');
    const messageElement = document.getElementById('resetModalMessage');
    const confirmButton = document.getElementById('confirmResetBtn');

    // 获取当前筛选后可见的、且包含 data-fail-count 属性的密钥数量
    // 根据密钥类型选择合适的选择器
    let keySelector;
    if (type === 'valid') {
        // 对于有效密钥，可能需要基于失败次数筛选，保留 data-fail-count (虽然批量重置通常不需要筛选)
        // 如果批量重置有效密钥也应重置所有可见的，可以将此行改为下面 else 中的选择器
        keySelector = `#${type}Keys li[data-fail-count]:not([style*="display: none"])`;
    } else {
        // 对于无效密钥，我们想要重置所有可见的无效密钥，不依赖 data-fail-count
        keySelector = `#${type}Keys li:not([style*="display: none"])`;
    }
    const visibleKeyItems = document.querySelectorAll(keySelector);
    const count = visibleKeyItems.length;

    // 设置标题和消息
    titleElement.textContent = '批量重置失败次数';
    if (count > 0) {
        messageElement.textContent = `确定要批量重置筛选出的 ${count} 个${type === 'valid' ? '有效' : '无效'}密钥的失败次数吗？`;
        confirmButton.disabled = false; // 确保按钮可用
    } else {
        messageElement.textContent = `当前没有筛选出可重置的${type === 'valid' ? '有效' : '无效'}密钥。`;
        confirmButton.disabled = true; // 没有可重置的密钥时禁用确认按钮
    }


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
    // 支持长文本和换行，内容插入到div而不是p
    if (typeof message === 'string') {
        // 如果内容包含换行或长文本，自动转为可滚动
        messageElement.textContent = '';
        messageElement.innerText = message;
    } else if (message instanceof Node) {
        messageElement.innerHTML = '';
        messageElement.appendChild(message);
    } else {
        messageElement.textContent = String(message);
    }
    
    // 设置确认按钮点击事件
    confirmButton.onclick = () => closeResultModal(autoReload);
    
    // 显示模态框
    modalElement.classList.remove('hidden');
}

async function executeResetAll(type) {
    try {
        // 关闭确认模态框
        closeResetModal();

        // 找到对应的重置按钮以显示加载状态
        const resetButton = document.querySelector(`button[data-reset-type="${type}"]`);
        if (!resetButton) {
            showResultModal(false, `找不到${type === 'valid' ? '有效' : '无效'}密钥区域的批量重置按钮`);
            return;
        }

        // 获取筛选后可见的密钥
        const visibleKeyItems = document.querySelectorAll(`#${type}Keys li:not([style*="display: none"]) .key-text`);
        const keysToReset = Array.from(visibleKeyItems).map(span => span.dataset.fullKey);

        if (keysToReset.length === 0) {
            showNotification(`没有需要重置的筛选后${type === 'valid' ? '有效' : '无效'}密钥`, 'warning');
            return;
        }

        // 禁用按钮并显示加载状态
        resetButton.disabled = true;
        const originalHtml = resetButton.innerHTML;
        resetButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 重置中';

        try {
            // 调用新的后端 API 来重置选定的密钥
            const response = await fetch(`/gemini/v1beta/reset-selected-fail-counts`, { // 假设的新 API 端点
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keys: keysToReset, key_type: type }) // 发送密钥列表和类型
            });

            if (!response.ok) {
                 // 尝试解析错误信息
                 let errorMsg = `服务器返回错误: ${response.status}`;
                 try {
                     const errorData = await response.json();
                     errorMsg = errorData.message || errorMsg;
                 } catch (e) {
                     // 如果解析失败，使用原始错误信息
                 }
                 
                 throw new Error(errorMsg);
            }

            const data = await response.json();

            // 根据重置结果显示模态框
            if (data.success) {
                const message = data.reset_count !== undefined ? // 检查 reset_count 是否存在
                    `成功重置 ${data.reset_count} 个筛选后的${type === 'valid' ? '有效' : '无效'}密钥的失败次数` :
                    `成功重置 ${keysToReset.length} 个筛选后的密钥`; // 如果后端没返回数量，使用前端计算的数量
                showResultModal(true, message); // 成功后刷新页面
            } else {
                const errorMsg = data.message || '批量重置失败';
                // 失败后不自动刷新页面，让用户看到错误信息
                showResultModal(false, '批量重置失败: ' + errorMsg, false);
            }
        } catch (fetchError) {
            console.error('API请求失败:', fetchError);
            showResultModal(false, '批量重置请求失败: ' + fetchError.message, false); // 失败后不自动刷新
        } finally {
            // 恢复按钮状态
             resetButton.innerHTML = originalHtml;
             resetButton.disabled = false;
        }
    } catch (error) {
        console.error('批量重置处理失败:', error);
        showResultModal(false, '批量重置处理失败: ' + error.message, false); // 失败后不自动刷新
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

// 重写切换区域显示/隐藏函数，以更好地支持新样式
function toggleSection(header, sectionId) {
    const toggleIcon = header.querySelector('.toggle-icon');
    const content = header.nextElementSibling;
    
    if (toggleIcon && content) {
        // 添加旋转动画
        toggleIcon.classList.toggle('collapsed');
        
        // 控制内容区域的可见性
        if (!content.classList.contains('collapsed')) {
            // 收起内容
            content.style.maxHeight = '0px';
            content.style.opacity = '0';
            content.style.overflow = 'hidden';
            content.classList.add('collapsed');
            
            // 为动画添加延迟
            setTimeout(() => {
                content.style.padding = '0';
            }, 100);
        } else {
            // 展开内容
            content.classList.remove('collapsed');
            content.style.padding = '1rem';
            content.style.maxHeight = '2000px'; // 使用足够大的高度
            content.style.opacity = '1';
            
            // 为动画添加延迟
            setTimeout(() => {
                content.style.overflow = 'visible';
            }, 300);
        }
    }
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
    // 初始化统计区块动画
    initStatItemAnimations();
    
    // 添加数字滚动动画效果
    const animateCounters = () => {
        const statValues = document.querySelectorAll('.stat-value');
        statValues.forEach(valueElement => {
            const finalValue = parseInt(valueElement.textContent, 10);
            if (!isNaN(finalValue)) {
                // 保存原始值以便稍后恢复
                if (!valueElement.dataset.originalValue) {
                    valueElement.dataset.originalValue = valueElement.textContent;
                }
                
                // 数字滚动动画
                let startValue = 0;
                const duration = 1500;
                const startTime = performance.now();
                
                const updateCounter = (currentTime) => {
                    const elapsedTime = currentTime - startTime;
                    if (elapsedTime < duration) {
                        const progress = elapsedTime / duration;
                        // 使用缓动函数使动画更自然
                        const easeOutValue = 1 - Math.pow(1 - progress, 3);
                        const currentValue = Math.floor(easeOutValue * finalValue);
                        valueElement.textContent = currentValue;
                        requestAnimationFrame(updateCounter);
                    } else {
                        // 恢复为原始值，以确保准确性
                        valueElement.textContent = valueElement.dataset.originalValue;
                    }
                    
                    
                    window.showVerifyModal = function(type, event) {
                        // 阻止事件冒泡（如果从按钮点击触发）
                        if (event) {
                            event.stopPropagation();
                        }
                    
                        const modalElement = document.getElementById('verifyModal');
                        const titleElement = document.getElementById('verifyModalTitle');
                        const messageElement = document.getElementById('verifyModalMessage');
                        const confirmButton = document.getElementById('confirmVerifyBtn');
                    
                        // 获取当前筛选后可见的、且包含 data-fail-count 属性的密钥数量
                        // 注意：对于验证，我们可能想验证所有筛选出的密钥，无论其 data-fail-count 如何，
                        // 但为了与重置保持一致，并且通常只验证有效/无效列表中的项，我们保留 data-fail-count 检查。
                        // 如果要验证所有可见项（包括没有 data-fail-count 的），可以移除 [data-fail-count] 选择器。
                        const visibleKeyItems = document.querySelectorAll(`#${type}Keys li[data-fail-count]:not([style*="display: none"])`);
                        const count = visibleKeyItems.length;
                    
                        // 设置标题和消息
                        titleElement.textContent = '批量验证密钥';
                        if (count > 0) {
                            messageElement.textContent = `确定要批量验证筛选出的 ${count} 个${type === 'valid' ? '有效' : '无效'}密钥吗？此操作可能需要一些时间。`;
                            confirmButton.disabled = false; // 确保按钮可用
                        } else {
                            messageElement.textContent = `当前没有筛选出可验证的${type === 'valid' ? '有效' : '无效'}密钥。`;
                            confirmButton.disabled = true; // 没有可验证的密钥时禁用确认按钮
                        }
                    
                        // 设置确认按钮事件
                        confirmButton.onclick = () => executeVerifyAll(type);
                    
                        // 显示模态框
                        modalElement.classList.remove('hidden');
                    }
                    
                    window.closeVerifyModal = function() {
                        document.getElementById('verifyModal').classList.add('hidden');
                    }
                    
                    window.executeVerifyAll = async function(type) {
                        try {
                            // 关闭确认模态框
                            closeVerifyModal();
                    
                            // 找到对应的验证按钮以显示加载状态 (需要给按钮添加 data-verify-type 属性)
                            // 或者，我们可以暂时禁用所有按钮或显示一个全局加载指示器
                            // 这里我们暂时只记录日志，实际UI反馈可以后续增强
                            console.log(`Starting bulk verification for ${type} keys...`);
                    
                            // 获取筛选后可见的密钥
                            const visibleKeyItems = document.querySelectorAll(`#${type}Keys li[data-fail-count]:not([style*="display: none"]) .key-text`);
                            const keysToVerify = Array.from(visibleKeyItems).map(span => span.dataset.fullKey);
                    
                            if (keysToVerify.length === 0) {
                                showNotification(`没有需要验证的筛选后${type === 'valid' ? '有效' : '无效'}密钥`, 'warning');
                                return;
                            }
                    
                            // 显示一个通用的加载提示
                            showNotification('开始批量验证，请稍候...', 'info');
                    
                            // 调用新的后端 API 来验证选定的密钥
                            const response = await fetch(`/gemini/v1beta/verify-selected-keys`, { // 假设的新 API 端点
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ keys: keysToVerify }) // 只发送密钥列表
                            });
                    
                            if (!response.ok) {
                                 let errorMsg = `服务器返回错误: ${response.status}`;
                                 try {
                                     const errorData = await response.json();
                                     errorMsg = errorData.message || errorMsg;
                                 } catch (e) { /*忽略解析错误*/ }
                                 throw new Error(errorMsg);
                            }
                    
                            const data = await response.json();
                    
                            // 根据验证结果显示模态框
                            if (data.success) {
                                // 可以在这里构建更详细的消息，例如显示多少有效多少无效
                                const message = `批量验证完成。有效: ${data.valid_count}, 无效: ${data.invalid_count}。页面即将刷新。`;
                                // 验证成功后通常需要刷新页面以更新状态
                                showResultModal(true, message, true); // autoReload = true
                            } else {
                                const errorMsg = data.message || '批量验证失败';
                                // 失败后不自动刷新
                                showResultModal(false, '批量验证失败: ' + errorMsg, false);
                            }
                    
                        } catch (error) {
                            console.error('批量验证处理失败:', error);
                            // 失败后不自动刷新
                            showResultModal(false, '批量验证处理失败: ' + error.message, false);
                        } finally {
                             // 可以在这里移除加载指示器
                             console.log("Bulk verification process finished.");
                        }
                    }
                    
                };
                
                requestAnimationFrame(updateCounter);
            }
        });
    };
    
    // 在页面加载后启动数字动画
    setTimeout(animateCounters, 300);
    
    // 添加卡片悬停效果
    document.querySelectorAll('.stats-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.classList.add('shadow-lg');
            card.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.classList.remove('shadow-lg');
            card.style.transform = '';
        });
    });
    
    // 监听展开/折叠事件
    document.querySelectorAll('.stats-card-title').forEach(header => {
        header.addEventListener('click', () => {
            const card = header.closest('.stats-card');
            if (card) {
                card.classList.toggle('active');
            }
        });
    });
    
    // 添加筛选输入框事件监听
    const thresholdInput = document.getElementById('failCountThreshold');
    if (thresholdInput) {
        // 使用 'input' 事件实时响应输入变化
        thresholdInput.addEventListener('input', filterValidKeys);
        // 初始加载时应用一次筛选
        filterValidKeys();
    }
    
    // --- 批量验证相关函数 (明确挂载到 window) ---
    
    window.showVerifyModal = function(type, event) {
        // 阻止事件冒泡（如果从按钮点击触发）
        if (event) {
            event.stopPropagation();
        }
    
        const modalElement = document.getElementById('verifyModal');
        const titleElement = document.getElementById('verifyModalTitle');
        const messageElement = document.getElementById('verifyModalMessage');
        const confirmButton = document.getElementById('confirmVerifyBtn');
    
        // 获取当前筛选后可见的、且包含 data-fail-count 属性的密钥数量
        // 注意：对于验证，我们可能想验证所有筛选出的密钥，无论其 data-fail-count 如何，
        // 但为了与重置保持一致，并且通常只验证有效/无效列表中的项，我们保留 data-fail-count 检查。
        // 如果要验证所有可见项（包括没有 data-fail-count 的），可以移除 [data-fail-count] 选择器。
        const visibleKeyItems = document.querySelectorAll(`#${type}Keys li[data-fail-count]:not([style*="display: none"])`);
        const count = visibleKeyItems.length;
    
        // 设置标题和消息
        titleElement.textContent = '批量验证密钥';
        if (count > 0) {
            messageElement.textContent = `确定要批量验证筛选出的 ${count} 个${type === 'valid' ? '有效' : '无效'}密钥吗？此操作可能需要一些时间。`;
            confirmButton.disabled = false; // 确保按钮可用
        } else {
            messageElement.textContent = `当前没有筛选出可验证的${type === 'valid' ? '有效' : '无效'}密钥。`;
            confirmButton.disabled = true; // 没有可验证的密钥时禁用确认按钮
        }
    
        // 设置确认按钮事件
        confirmButton.onclick = () => executeVerifyAll(type);
    
        // 显示模态框
        modalElement.classList.remove('hidden');
    }
    
    window.closeVerifyModal = function() {
        document.getElementById('verifyModal').classList.add('hidden');
    }
    
    window.executeVerifyAll = async function(type) {
        try {
            // 关闭确认模态框
            closeVerifyModal();
    
            // 找到对应的验证按钮以显示加载状态 (需要给按钮添加 data-verify-type 属性)
            // 或者，我们可以暂时禁用所有按钮或显示一个全局加载指示器
            // 这里我们暂时只记录日志，实际UI反馈可以后续增强
            console.log(`Starting bulk verification for ${type} keys...`);
    
            // 获取筛选后可见的密钥
            const visibleKeyItems = document.querySelectorAll(`#${type}Keys li[data-fail-count]:not([style*="display: none"]) .key-text`);
            const keysToVerify = Array.from(visibleKeyItems).map(span => span.dataset.fullKey);
    
            if (keysToVerify.length === 0) {
                showNotification(`没有需要验证的筛选后${type === 'valid' ? '有效' : '无效'}密钥`, 'warning');
                return;
            }
    
            // 显示一个通用的加载提示
            showNotification('开始批量验证，请稍候...', 'info');
    
            // 调用新的后端 API 来验证选定的密钥
            const response = await fetch(`/gemini/v1beta/verify-selected-keys`, { // 假设的新 API 端点
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keys: keysToVerify }) // 只发送密钥列表
            });
    
            if (!response.ok) {
                 let errorMsg = `服务器返回错误: ${response.status}`;
                 try {
                     const errorData = await response.json();
                     errorMsg = errorData.message || errorMsg;
                 } catch (e) { /*忽略解析错误*/ }
                 throw new Error(errorMsg);
            }
    
            const data = await response.json();
    
            // 根据验证结果显示模态框
            if (data.success) {
                // 可以在这里构建更详细的消息，例如显示多少有效多少无效
                const message = `批量验证完成。有效: ${data.valid_count}, 无效: ${data.invalid_count}。页面即将刷新。`;
                // 验证成功后通常需要刷新页面以更新状态
                showResultModal(true, message, true); // autoReload = true
            } else {
                const errorMsg = data.message || '批量验证失败';
                // 失败后不自动刷新
                showResultModal(false, '批量验证失败: ' + errorMsg, false);
            }
    
        } catch (error) {
            console.error('批量验证处理失败:', error);
            // 失败后不自动刷新
            showResultModal(false, '批量验证处理失败: ' + error.message, false);
        } finally {
             // 可以在这里移除加载指示器
             console.log("Bulk verification process finished.");
        }
    }

    // --- 滚动和页面控制 ---
    // --- 自动刷新控制 ---
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    const autoRefreshIntervalTime = 60000; // 60秒
    let autoRefreshTimer = null;

    function startAutoRefresh() {
        if (autoRefreshTimer) return; // 防止重复启动
        console.log('启动自动刷新...');
        autoRefreshTimer = setInterval(() => {
            console.log('自动刷新 keys_status 页面...');
            location.reload();
        }, autoRefreshIntervalTime);
    }

    function stopAutoRefresh() {
        if (autoRefreshTimer) {
            console.log('停止自动刷新...');
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }
    }

    if (autoRefreshToggle) {
        // 从 localStorage 读取状态并初始化
        const isAutoRefreshEnabled = localStorage.getItem('autoRefreshEnabled') === 'true';
        autoRefreshToggle.checked = isAutoRefreshEnabled;
        if (isAutoRefreshEnabled) {
            startAutoRefresh();
        }

        // 添加事件监听器
        autoRefreshToggle.addEventListener('change', () => {
            if (autoRefreshToggle.checked) {
                localStorage.setItem('autoRefreshEnabled', 'true');
                startAutoRefresh();
            } else {
                localStorage.setItem('autoRefreshEnabled', 'false');
                stopAutoRefresh();
            }
        });
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

// --- API 调用详情模态框逻辑 ---

// 显示 API 调用详情模态框
async function showApiCallDetails(period) {
    const modal = document.getElementById('apiCallDetailsModal');
    const contentArea = document.getElementById('apiCallDetailsContent');
    const titleElement = document.getElementById('apiCallDetailsModalTitle');

    if (!modal || !contentArea || !titleElement) {
        console.error('无法找到 API 调用详情模态框元素');
        showNotification('无法显示详情，页面元素缺失', 'error');
        return;
    }

    // 设置标题
    let periodText = '';
    switch (period) {
        case '1m': periodText = '最近 1 分钟'; break;
        case '1h': periodText = '最近 1 小时'; break;
        case '24h': periodText = '最近 24 小时'; break;
        default: periodText = '指定时间段';
    }
    titleElement.textContent = `${periodText} API 调用详情`;

    // 显示模态框并设置加载状态
    modal.classList.remove('hidden');
    contentArea.innerHTML = `
        <div class="text-center py-10">
             <i class="fas fa-spinner fa-spin text-primary-600 text-3xl"></i>
             <p class="text-gray-500 mt-2">加载中...</p>
        </div>`;

    try {
        // 调用后端 API 获取数据
        const response = await fetch(`/api/stats/details?period=${period}`);
        if (!response.ok) {
            throw new Error(`服务器错误: ${response.status}`);
        }
        const data = await response.json();

        // 渲染数据
        renderApiCallDetails(data, contentArea);

    } catch (error) {
        console.error('获取 API 调用详情失败:', error);
        contentArea.innerHTML = `
            <div class="text-center py-10 text-danger-500">
                <i class="fas fa-exclamation-triangle text-3xl"></i>
                <p class="mt-2">加载失败: ${error.message}</p>
            </div>`;
    }
}

// 关闭 API 调用详情模态框
function closeApiCallDetailsModal() {
    const modal = document.getElementById('apiCallDetailsModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// 渲染 API 调用详情到模态框
function renderApiCallDetails(data, container) {
    if (!data || data.length === 0) {
        container.innerHTML = `
            <div class="text-center py-10 text-gray-500">
                <i class="fas fa-info-circle text-3xl"></i>
                <p class="mt-2">该时间段内没有 API 调用记录。</p>
            </div>`;
        return;
    }

    // 创建表格
    let tableHtml = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">密钥 (部分)</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">模型</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;

    // 填充表格行
    data.forEach(call => {
        const timestamp = new Date(call.timestamp).toLocaleString();
        const keyDisplay = call.key ? `${call.key.substring(0, 4)}...${call.key.substring(call.key.length - 4)}` : 'N/A';
        const statusClass = call.status === 'success' ? 'text-success-600' : 'text-danger-600';
        const statusIcon = call.status === 'success' ? 'fa-check-circle' : 'fa-times-circle';

        tableHtml += `
            <tr>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${timestamp}</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500 font-mono">${keyDisplay}</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">${call.model || 'N/A'}</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm ${statusClass}">
                    <i class="fas ${statusIcon} mr-1"></i>
                    ${call.status}
                </td>
            </tr>
        `;
    });

    tableHtml += `
            </tbody>
        </table>
    `;

    container.innerHTML = tableHtml;
}
