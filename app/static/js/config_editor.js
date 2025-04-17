document.addEventListener('DOMContentLoaded', function() {
    // 初始化配置
    initConfig();
    
    // 标签切换
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // 防止事件冒泡
            e.stopPropagation();
            const tabId = this.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // 上传提供商切换
    const uploadProviderSelect = document.getElementById('UPLOAD_PROVIDER');
    if (uploadProviderSelect) {
        uploadProviderSelect.addEventListener('change', function() {
            toggleProviderConfig(this.value);
        });
    }
    
    // 切换按钮事件
    const toggleSwitches = document.querySelectorAll('.toggle-switch');
    toggleSwitches.forEach(toggleSwitch => {
        toggleSwitch.addEventListener('click', function(e) {
            // 防止事件冒泡
            e.stopPropagation();
            const checkbox = this.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
            }
        });
    });
    
    // 保存按钮
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveConfig);
    }
    
    // 重置按钮
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetConfig);
    }
    
    // 滚动按钮
    window.addEventListener('scroll', toggleScrollButtons);

    // --- 新增：API Key 模态框和搜索相关 ---
    const apiKeyModal = document.getElementById('apiKeyModal');
    const addApiKeyBtn = document.getElementById('addApiKeyBtn');
    const closeApiKeyModalBtn = document.getElementById('closeApiKeyModalBtn');
    const cancelAddApiKeyBtn = document.getElementById('cancelAddApiKeyBtn');
    const confirmAddApiKeyBtn = document.getElementById('confirmAddApiKeyBtn');
    const apiKeyBulkInput = document.getElementById('apiKeyBulkInput');
    const apiKeySearchInput = document.getElementById('apiKeySearchInput');
    const bulkDeleteApiKeyBtn = document.getElementById('bulkDeleteApiKeyBtn'); // 新增
    const bulkDeleteApiKeyModal = document.getElementById('bulkDeleteApiKeyModal'); // 新增
    const closeBulkDeleteModalBtn = document.getElementById('closeBulkDeleteModalBtn'); // 新增
    const cancelBulkDeleteApiKeyBtn = document.getElementById('cancelBulkDeleteApiKeyBtn'); // 新增
    const confirmBulkDeleteApiKeyBtn = document.getElementById('confirmBulkDeleteApiKeyBtn'); // 新增
    const bulkDeleteApiKeyInput = document.getElementById('bulkDeleteApiKeyInput'); // 新增

    // --- 新增：重置确认模态框相关 ---
    const resetConfirmModal = document.getElementById('resetConfirmModal');
    const closeResetModalBtn = document.getElementById('closeResetModalBtn');
    const cancelResetBtn = document.getElementById('cancelResetBtn');
    const confirmResetBtn = document.getElementById('confirmResetBtn');
    // --- 结束：新增 ---


    // 打开模态框
    if (addApiKeyBtn) {
        addApiKeyBtn.addEventListener('click', () => {
            if (apiKeyModal) {
                apiKeyModal.classList.add('show');
            }
            if (apiKeyBulkInput) apiKeyBulkInput.value = ''; // 清空输入框
        });
    }

    // 关闭模态框 (X 按钮)
    if (closeApiKeyModalBtn) {
        closeApiKeyModalBtn.addEventListener('click', () => {
            if (apiKeyModal) {
                apiKeyModal.classList.remove('show');
            }
        });
    }

    // 关闭模态框 (取消按钮)
    if (cancelAddApiKeyBtn) {
        cancelAddApiKeyBtn.addEventListener('click', () => {
            if (apiKeyModal) {
                apiKeyModal.classList.remove('show');
            }
        });
    }

    // 点击模态框外部关闭 (处理两个模态框)
    window.addEventListener('click', (event) => {
        if (event.target == apiKeyModal) {
            apiKeyModal.classList.remove('show');
        }
        if (event.target == resetConfirmModal) {
            resetConfirmModal.classList.remove('show');
        }
        if (event.target == bulkDeleteApiKeyModal) { // 新增对批量删除模态框的处理
            bulkDeleteApiKeyModal.classList.remove('show');
        }
    });

    // 确认添加 API Key
    if (confirmAddApiKeyBtn) {
        confirmAddApiKeyBtn.addEventListener('click', handleBulkAddApiKeys);
    }

    // API Key 搜索 (稍后实现具体逻辑)
    if (apiKeySearchInput) {
        apiKeySearchInput.addEventListener('input', handleApiKeySearch);
    }

    // --- 新增：批量删除 API Key 相关事件 ---
    // 打开批量删除模态框
    if (bulkDeleteApiKeyBtn) {
        bulkDeleteApiKeyBtn.addEventListener('click', () => {
            if (bulkDeleteApiKeyModal) {
                bulkDeleteApiKeyModal.classList.add('show');
            }
            if (bulkDeleteApiKeyInput) bulkDeleteApiKeyInput.value = ''; // 清空输入框
        });
    }

    // 关闭批量删除模态框 (X 按钮)
    if (closeBulkDeleteModalBtn) {
        closeBulkDeleteModalBtn.addEventListener('click', () => {
            if (bulkDeleteApiKeyModal) {
                bulkDeleteApiKeyModal.classList.remove('show');
            }
        });
    }

    // 关闭批量删除模态框 (取消按钮)
    if (cancelBulkDeleteApiKeyBtn) {
        cancelBulkDeleteApiKeyBtn.addEventListener('click', () => {
            if (bulkDeleteApiKeyModal) {
                bulkDeleteApiKeyModal.classList.remove('show');
            }
        });
    }

    // 确认批量删除 API Key
    if (confirmBulkDeleteApiKeyBtn) {
        confirmBulkDeleteApiKeyBtn.addEventListener('click', handleBulkDeleteApiKeys);
    }
    // --- 结束：批量删除 API Key 相关 ---
    // --- 结束：API Key 相关 ---

    // --- 新增：重置确认模态框事件监听 (移到 DOMContentLoaded 内部) ---
    if (closeResetModalBtn) {
        closeResetModalBtn.addEventListener('click', () => {
            if (resetConfirmModal) {
                resetConfirmModal.classList.remove('show');
            }
        });
    }
    if (cancelResetBtn) {
        cancelResetBtn.addEventListener('click', () => {
            if (resetConfirmModal) {
                resetConfirmModal.classList.remove('show');
            }
        });
    }
    if (confirmResetBtn) {
        // 调用之前定义的 executeReset 函数
        confirmResetBtn.addEventListener('click', () => {
             if (resetConfirmModal) {
                 resetConfirmModal.classList.remove('show'); // 关闭模态框
             }
             executeReset(); // 执行重置逻辑
        });
    }
    // --- 结束：重置相关 ---

    // 移除了静态生成令牌按钮的事件监听器，现在按钮是动态生成的

    // 认证令牌生成按钮事件绑定
    const generateAuthTokenBtn = document.getElementById('generateAuthTokenBtn');
    const authTokenInput = document.getElementById('AUTH_TOKEN');
    if (generateAuthTokenBtn && authTokenInput) {
        generateAuthTokenBtn.addEventListener('click', function() {
            const newToken = generateRandomToken();
            authTokenInput.value = newToken;
            showNotification('已生成新认证令牌', 'success');
        });
    }
}); // <-- DOMContentLoaded 结束括号

// 初始化配置
async function initConfig() {
    try {
        showNotification('正在加载配置...', 'info');
        const response = await fetch('/api/config');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const config = await response.json();
        
        // 确保数组字段有默认值
        if (!config.API_KEYS || !Array.isArray(config.API_KEYS) || config.API_KEYS.length === 0) {
            config.API_KEYS = ['请在此处输入 API 密钥'];
        }
        
        if (!config.ALLOWED_TOKENS || !Array.isArray(config.ALLOWED_TOKENS) || config.ALLOWED_TOKENS.length === 0) {
            config.ALLOWED_TOKENS = [''];
        }
        
        if (!config.IMAGE_MODELS || !Array.isArray(config.IMAGE_MODELS) || config.IMAGE_MODELS.length === 0) {
            config.IMAGE_MODELS = ['gemini-1.5-pro-latest'];
        }
        
        if (!config.SEARCH_MODELS || !Array.isArray(config.SEARCH_MODELS) || config.SEARCH_MODELS.length === 0) {
            config.SEARCH_MODELS = ['gemini-1.5-flash-latest'];
        }
        
        if (!config.FILTERED_MODELS || !Array.isArray(config.FILTERED_MODELS) || config.FILTERED_MODELS.length === 0) {
            config.FILTERED_MODELS = ['gemini-1.0-pro-latest'];
        }
        
        populateForm(config);
        
        // 确保上传提供商有默认值
        const uploadProvider = document.getElementById('UPLOAD_PROVIDER');
        if (uploadProvider && !uploadProvider.value) {
            uploadProvider.value = 'smms'; // 设置默认值为 smms
            toggleProviderConfig('smms');
        }
        
        showNotification('配置加载成功', 'success');
    } catch (error) {
        console.error('加载配置失败:', error);
        showNotification('加载配置失败: ' + error.message, 'error');
        
        // 加载失败时，使用默认配置
        const defaultConfig = {
            API_KEYS: [''],
            ALLOWED_TOKENS: [''],
            IMAGE_MODELS: ['gemini-1.5-pro-latest'],
            SEARCH_MODELS: ['gemini-1.5-flash-latest'],
            FILTERED_MODELS: ['gemini-1.0-pro-latest'],
            UPLOAD_PROVIDER: 'smms'
        };
        
        populateForm(defaultConfig);
        toggleProviderConfig('smms');
    }
}

// 填充表单
function populateForm(config) {
    for (const [key, value] of Object.entries(config)) {
        // 首先检查是否是数组类型
        if (Array.isArray(value)) {
            const container = document.getElementById(`${key}_container`);
            if (container) {
                // 清除现有项
                const existingItems = container.querySelectorAll('.array-item');
                existingItems.forEach(item => item.remove());
                // 添加数组项
                value.forEach(item => {
                    // 确保只添加非空字符串项（如果需要）
                    // if (item && typeof item === 'string' && item.trim() !== '') {
                 addArrayItemWithValue(key, item);
            // }
                });
            }
            // 处理完数组后，跳过本次循环的剩余部分
            continue;
        }

        // 如果不是数组，再尝试查找对应的单个元素
        const element = document.getElementById(key);
        if (element) {
            if (typeof value === 'boolean') {
                element.checked = value;
            } else {
                // 处理其他类型 (确保 value 不是 null 或 undefined)
                element.value = value ?? ''; // 使用空字符串作为默认值
            }
        }
        // 如果既不是数组，也找不到对应 ID 的元素，则忽略该配置项
    }

    // 初始化上传提供商配置 (保持不变)
    const uploadProvider = document.getElementById('UPLOAD_PROVIDER');
    if (uploadProvider) {
        toggleProviderConfig(uploadProvider.value);
    }
}

// --- 新增：处理批量添加 API Key 的逻辑 ---
function handleBulkAddApiKeys() {
    const apiKeyBulkInput = document.getElementById('apiKeyBulkInput');
    const apiKeyContainer = document.getElementById('API_KEYS_container');
    const apiKeyModal = document.getElementById('apiKeyModal');

    if (!apiKeyBulkInput || !apiKeyContainer || !apiKeyModal) return;

    const bulkText = apiKeyBulkInput.value;
    const keyRegex = /AIzaSy\S{33}/g; // 全局匹配
    const extractedKeys = bulkText.match(keyRegex) || [];

    // 获取当前已有的 keys
    const currentKeyInputs = apiKeyContainer.querySelectorAll('.array-input');
    const currentKeys = Array.from(currentKeyInputs).map(input => input.value).filter(key => key.trim() !== '');

    // 合并并去重
    const combinedKeys = new Set([...currentKeys, ...extractedKeys]);
    const uniqueKeys = Array.from(combinedKeys);

    // 清空现有列表显示
    const existingItems = apiKeyContainer.querySelectorAll('.array-item');
    existingItems.forEach(item => item.remove());

    // 重新填充列表
    uniqueKeys.forEach(key => {
        addArrayItemWithValue('API_KEYS', key);
    });

    // 关闭模态框
    apiKeyModal.classList.remove('show');
    showNotification(`添加/更新了 ${uniqueKeys.length} 个唯一密钥`, 'success');
}

// --- 新增：处理 API Key 搜索的逻辑 ---
function handleApiKeySearch() {
    const apiKeySearchInput = document.getElementById('apiKeySearchInput');
    const apiKeyContainer = document.getElementById('API_KEYS_container');

    if (!apiKeySearchInput || !apiKeyContainer) return;

    const searchTerm = apiKeySearchInput.value.toLowerCase();
    const keyItems = apiKeyContainer.querySelectorAll('.array-item');

    keyItems.forEach(item => {
        const input = item.querySelector('.array-input');
        if (input) {
            const key = input.value.toLowerCase();
            if (key.includes(searchTerm)) {
                item.style.display = 'flex'; // 或者 'block'，取决于你的布局
            } else {
                item.style.display = 'none';
            }
        }
    });
}

// --- 新增：处理批量删除 API Key 的逻辑 ---
function handleBulkDeleteApiKeys() {
    const bulkDeleteTextarea = document.getElementById('bulkDeleteApiKeyInput'); // Use the textarea ID
    const apiKeyContainer = document.getElementById('API_KEYS_container');
    const bulkDeleteModal = document.getElementById('bulkDeleteApiKeyModal');

    if (!bulkDeleteTextarea || !apiKeyContainer || !bulkDeleteModal) return;

    const bulkText = bulkDeleteTextarea.value;
    if (!bulkText.trim()) {
        showNotification('请粘贴需要删除的 API 密钥', 'warning');
        return;
    }

    // Use the same regex as for adding keys to extract keys to delete
    const keyRegex = /AIzaSy\S{33}/g;
    const keysToDelete = new Set(bulkText.match(keyRegex) || []); // Create a Set for efficient lookup

    if (keysToDelete.size === 0) {
        showNotification('未在输入内容中提取到有效的 API 密钥格式', 'warning');
        // Optionally clear the textarea or keep it as is
        // bulkDeleteTextarea.value = '';
        return;
    }

    const keyItems = apiKeyContainer.querySelectorAll('.array-item');
    let deleteCount = 0;

    keyItems.forEach(item => {
        const input = item.querySelector('.array-input');
        // Check if the input exists and its value is in the set of keys to delete
        if (input && keysToDelete.has(input.value)) {
            item.remove(); // Remove the entire array item element
            deleteCount++;
        }
    });

    // Close the modal
    bulkDeleteModal.classList.remove('show');

    // Provide feedback
    if (deleteCount > 0) {
        showNotification(`成功删除了 ${deleteCount} 个匹配的密钥`, 'success');
    } else {
        // This message implies keys were extracted but not found in the current list
        showNotification('列表中未找到您输入的任何密钥进行删除', 'info');
    }

    // Clear the textarea after processing
    bulkDeleteTextarea.value = '';
}

// 切换标签
function switchTab(tabId) {
    // 更新标签按钮状态
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabId) {
            // 激活状态：主色背景，白色文字，添加阴影
            button.classList.remove('bg-white', 'bg-opacity-50', 'text-gray-700', 'hover:bg-opacity-70');
            button.classList.add('bg-primary-600', 'text-white', 'shadow-md');
        } else {
            // 非激活状态：白色背景，灰色文字，无阴影
            button.classList.remove('bg-primary-600', 'text-white', 'shadow-md');
            button.classList.add('bg-white', 'bg-opacity-50', 'text-gray-700', 'hover:bg-opacity-70');
        }
    });
    
    // 更新内容区域
    const sections = document.querySelectorAll('.config-section');
    sections.forEach(section => {
        if (section.id === `${tabId}-section`) {
            section.classList.add('active');
        } else {
            section.classList.remove('active');
        }
    });
}

// 切换上传提供商配置
function toggleProviderConfig(provider) {
    const providerConfigs = document.querySelectorAll('.provider-config');
    providerConfigs.forEach(config => {
        if (config.getAttribute('data-provider') === provider) {
            config.classList.add('active');
        } else {
            config.classList.remove('active');
        }
    });
}


// 添加数组项
function addArrayItem(key) {
    const container = document.getElementById(`${key}_container`);
    if (!container) return;
    
    addArrayItemWithValue(key, '');
}

// 添加带值的数组项
function addArrayItemWithValue(key, value) {
    const container = document.getElementById(`${key}_container`);
    if (!container) return;
    
    const arrayItem = document.createElement('div');
    // 主容器使用 Flexbox
    arrayItem.className = 'array-item flex items-center mb-2 gap-2'; // 添加 gap-2 来分隔元素

    // 创建一个包装器 div 来包含输入框和生成按钮
    const inputWrapper = document.createElement('div');
    // 这个包装器占据主要空间，并使用 Flexbox
    inputWrapper.className = 'flex items-center flex-grow border border-gray-300 rounded-md focus-within:border-primary-500 focus-within:ring focus-within:ring-primary-200 focus-within:ring-opacity-50';

    const input = document.createElement('input');
    input.type = 'text';
    input.name = `${key}[]`;
    input.value = value;
    // 输入框占据包装器内的主要空间，移除边框和圆角，因为包装器已有
    input.className = 'array-input flex-grow px-3 py-2 border-none rounded-l-md focus:outline-none'; // 移除右侧圆角

    inputWrapper.appendChild(input); // 将输入框添加到包装器

    // 只为 ALLOWED_TOKENS 添加生成按钮
    if (key === 'ALLOWED_TOKENS') {
        const generateBtn = document.createElement('button');
        generateBtn.type = 'button';
        // 按钮样式，放在输入框右侧，有背景和内边距，调整颜色
        generateBtn.className = 'generate-btn px-2 py-2 text-gray-500 hover:text-primary-600 focus:outline-none rounded-r-md bg-gray-100 hover:bg-gray-200 transition-colors'; // 添加背景和右侧圆角
        generateBtn.innerHTML = '<i class="fas fa-dice"></i>';
        generateBtn.title = '生成随机令牌';
        generateBtn.addEventListener('click', function() {
            const newToken = generateRandomToken();
            input.value = newToken;
            showNotification('已生成新令牌', 'success');
        });
        inputWrapper.appendChild(generateBtn); // 将生成按钮添加到包装器
    } else {
        // 如果不是 ALLOWED_TOKENS，确保输入框有右侧圆角
        input.classList.add('rounded-r-md');
    }

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    // 删除按钮样式，保持不变
    removeBtn.className = 'remove-btn text-gray-400 hover:text-red-500 focus:outline-none transition-colors duration-150';
    removeBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
    removeBtn.title = '删除';
    removeBtn.addEventListener('click', function() {
        arrayItem.remove();
    });

    // 将包装器（包含输入框和可能的生成按钮）和删除按钮添加到主容器
    arrayItem.appendChild(inputWrapper);
    arrayItem.appendChild(removeBtn);

    // 插入到容器末尾
    container.appendChild(arrayItem);
}

// 收集表单数据
function collectFormData() {
    const formData = {};
    
    // 处理普通输入
    const inputs = document.querySelectorAll('input[type="text"], input[type="number"], select');
    inputs.forEach(input => {
        if (!input.name.includes('[]')) {
            if (input.type === 'number') {
                formData[input.name] = parseFloat(input.value);
            } else {
                formData[input.name] = input.value;
            }
        }
    });
    
    // 处理复选框
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        formData[checkbox.name] = checkbox.checked;
    });
    
    // 处理数组
    const arrayContainers = document.querySelectorAll('.array-container');
    arrayContainers.forEach(container => {
        const key = container.id.replace('_container', '');
        const arrayInputs = container.querySelectorAll('.array-input');
        formData[key] = Array.from(arrayInputs).map(input => input.value).filter(value => value.trim() !== '');
    });
    
    return formData;
}

// 辅助函数：停止定时任务
async function stopScheduler() {
    try {
        const response = await fetch('/api/scheduler/stop', { method: 'POST' });
        if (!response.ok) {
            console.warn(`停止定时任务失败: ${response.status}`);
        } else {
            console.log('定时任务已停止');
        }
    } catch (error) {
        console.error('调用停止定时任务API时出错:', error);
    }
}

// 辅助函数：启动定时任务
async function startScheduler() {
    try {
        const response = await fetch('/api/scheduler/start', { method: 'POST' });
        if (!response.ok) {
            console.warn(`启动定时任务失败: ${response.status}`);
        } else {
            console.log('定时任务已启动');
        }
    } catch (error) {
        console.error('调用启动定时任务API时出错:', error);
    }
}

// 保存配置
async function saveConfig() {
    try {
        const formData = collectFormData();

        showNotification('正在保存配置...', 'info');

        // 1. 停止定时任务
        await stopScheduler();
        
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 移除居中的 saveStatus 提示
        
        showNotification('配置保存成功', 'success');

        // 3. 启动新的定时任务
        await startScheduler();

    } catch (error) {
        console.error('保存配置失败:', error);
        // 保存失败时，也尝试重启定时任务，以防万一
        await startScheduler();
        // 移除居中的 saveStatus 提示
        
        showNotification('保存配置失败: ' + error.message, 'error');
    }
}

// 重置配置 (现在只负责打开模态框)
function resetConfig(event) { 
    // 阻止事件冒泡和默认行为
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('resetConfig called. Event target:', event ? event.target.id : 'No event');
    
    // 确保只有当事件来自重置按钮时才显示模态框
    if (!event || event.target.id === 'resetBtn' || event.currentTarget.id === 'resetBtn') {
        const resetConfirmModal = document.getElementById('resetConfirmModal');
        if (resetConfirmModal) {
            resetConfirmModal.classList.add('show');
        } else {
            // Fallback if modal doesn't exist for some reason
            console.error("Reset confirmation modal not found! Falling back to default confirm.");
            // Fallback to original confirm behavior
            if (!confirm('确定要重置所有配置吗？这将恢复到默认值。')) {
                return;
            }
            // If confirmed, proceed with the reset logic directly (less ideal)
            executeReset();
        }
    }
}

// --- 新增：将实际重置逻辑提取到一个单独的函数 ---
async function executeReset() {
    try {
        showNotification('正在重置配置...', 'info');

        // 1. 停止定时任务
        await stopScheduler();
        const response = await fetch('/api/config/reset', { method: 'POST' });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const config = await response.json();
        populateForm(config);
        showNotification('配置已重置为默认值', 'success');

        // 3. 启动新的定时任务
        await startScheduler();

    } catch (error) {
        console.error('重置配置失败:', error);
        showNotification('重置配置失败: ' + error.message, 'error');
        // 重置失败时，也尝试重启定时任务
        await startScheduler();
    }
}
// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;

    // 统一样式为黑色半透明，与 keys_status.js 保持一致
    notification.classList.remove('bg-danger-500');
    notification.classList.add('bg-black');
    notification.style.backgroundColor = 'rgba(0,0,0,0.8)';
    notification.style.color = '#fff';

    // 应用过渡效果
    notification.style.opacity = "1";
    notification.style.transform = "translate(-50%, 0)";

    // 设置自动消失
    setTimeout(() => {
        notification.style.opacity = "0";
        notification.style.transform = "translate(-50%, 10px)";
    }, 3000);
}

// 刷新页面
function refreshPage(button) {
    button.classList.add('loading');
    location.reload();
}

// 滚动到顶部
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 滚动到底部
function scrollToBottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

// 切换滚动按钮显示
function toggleScrollButtons() {
    const scrollButtons = document.querySelector('.scroll-buttons');
    
    if (window.scrollY > 200) {
        scrollButtons.style.display = 'flex';
    } else {
        scrollButtons.style.display = 'none';
    }
}

// --- 新增：生成随机令牌函数 ---
function generateRandomToken() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_';
    const length = 48;
    let result = 'sk-';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}
// --- 结束：生成随机令牌函数 ---
