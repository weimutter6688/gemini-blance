// 错误日志页面JavaScript (Updated for new structure, no Bootstrap)

// 页面滚动功能
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// Refresh function removed as the buttons are gone.
// If refresh functionality is needed elsewhere, it can be triggered directly by calling loadErrorLogs().

// 全局变量
let currentPage = 1;
let pageSize = 10;
// let totalPages = 1; // totalPages will be calculated dynamically based on API response if available, or based on fetched data length
let errorLogs = []; // Store fetched logs for details view
let currentSearch = { // Store current search parameters
    key: '',
    error: '',
    startDate: '',
    endDate: ''
};

// DOM Elements Cache
let pageSizeSelector;
// let refreshBtn; // Removed, as the button is deleted
let tableBody;
let paginationElement;
let loadingIndicator;
let noDataMessage;
let errorMessage;
let logDetailModal;
let modalCloseBtns; // Collection of close buttons for the modal
let keySearchInput;
let errorSearchInput;
let startDateInput;
let endDateInput;
let searchBtn;
let pageInput; // 新增：页码输入框
let goToPageBtn; // 新增：跳转按钮

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    pageSizeSelector = document.getElementById('pageSize');
    // refreshBtn = document.getElementById('refreshBtn'); // Removed
    tableBody = document.getElementById('errorLogsTable');
    paginationElement = document.getElementById('pagination');
    loadingIndicator = document.getElementById('loadingIndicator');
    noDataMessage = document.getElementById('noDataMessage');
    errorMessage = document.getElementById('errorMessage');
    logDetailModal = document.getElementById('logDetailModal');
    // Get all elements that should close the modal
    modalCloseBtns = document.querySelectorAll('#closeLogDetailModalBtn, #closeModalFooterBtn');
    keySearchInput = document.getElementById('keySearch');
    errorSearchInput = document.getElementById('errorSearch');
    startDateInput = document.getElementById('startDate');
    endDateInput = document.getElementById('endDate');
    searchBtn = document.getElementById('searchBtn');
    pageInput = document.getElementById('pageInput'); // 新增
    goToPageBtn = document.getElementById('goToPageBtn'); // 新增

    // Initialize page size selector
    if (pageSizeSelector) {
        pageSizeSelector.value = pageSize;
        pageSizeSelector.addEventListener('change', function() {
            pageSize = parseInt(this.value);
            currentPage = 1; // Reset to first page
            loadErrorLogs();
        });
    }

    // Refresh button event listener removed

    // Initialize search button
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            // Update search parameters from input fields
            currentSearch.key = keySearchInput ? keySearchInput.value.trim() : '';
            currentSearch.error = errorSearchInput ? errorSearchInput.value.trim() : '';
            currentSearch.startDate = startDateInput ? startDateInput.value : '';
            currentSearch.endDate = endDateInput ? endDateInput.value : '';
            currentPage = 1; // Reset to first page on new search
            loadErrorLogs();
        });
    }

    // Initialize modal close buttons
    if (logDetailModal && modalCloseBtns) {
        modalCloseBtns.forEach(btn => {
            btn.addEventListener('click', closeLogDetailModal);
        });
        // Optional: Close modal if clicking outside the content
        logDetailModal.addEventListener('click', function(event) {
            if (event.target === logDetailModal) {
                closeLogDetailModal();
            }
        });
    }

    // Initial load of error logs
    loadErrorLogs();

    // Add event listeners for copy buttons inside the modal
    setupCopyButtons();

    // 新增：为页码跳转按钮添加事件监听器
    if (goToPageBtn && pageInput) {
        goToPageBtn.addEventListener('click', function() {
            const targetPage = parseInt(pageInput.value);
            // 需要获取总页数来验证输入
            // 暂时无法直接获取 totalPages，需要在 updatePagination 中存储或重新计算
            // 简单的验证：必须是正整数
            if (!isNaN(targetPage) && targetPage >= 1) {
                // 理想情况下，应检查 targetPage <= totalPages
                // 但 totalPages 可能未知，所以暂时只跳转
                currentPage = targetPage;
                loadErrorLogs();
                pageInput.value = ''; // 清空输入框
            } else {
                showNotification('请输入有效的页码', 'error', 2000);
                pageInput.value = ''; // 清空无效输入
            }
        });
        // 允许按 Enter 键跳转
        pageInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                goToPageBtn.click(); // 触发按钮点击
            }
        });
    }
});

// Fallback copy function using document.execCommand
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    let successful = false;
    try {
        successful = document.execCommand('copy');
    } catch (err) {
        console.error('Fallback copy failed:', err);
        successful = false;
    }

    document.body.removeChild(textArea);
    return successful;
}

// Helper function to handle feedback after copy attempt (both modern and fallback)
function handleCopyResult(buttonElement, success) {
     const originalIcon = buttonElement.querySelector('i').className; // Store original icon class
     const iconElement = buttonElement.querySelector('i');
     if (success) {
        iconElement.className = 'fas fa-check text-success-500'; // Use checkmark icon class
        showNotification('已复制到剪贴板', 'success', 2000);
     } else {
        iconElement.className = 'fas fa-times text-danger-500'; // Use error icon class
        showNotification('复制失败', 'error', 3000);
     }
     setTimeout(() => { iconElement.className = originalIcon; }, success ? 2000 : 3000); // Restore original icon class
}

// Function to set up copy button listeners (using modern API with fallback)
function setupCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const textToCopy = targetElement.textContent;
                let copySuccess = false;

                // Try modern clipboard API first (requires HTTPS or localhost)
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(textToCopy).then(() => {
                        handleCopyResult(this, true); // Use helper for feedback
                    }).catch(err => {
                        console.error('Clipboard API failed, attempting fallback:', err);
                        // Attempt fallback if modern API fails
                        copySuccess = fallbackCopyTextToClipboard(textToCopy);
                        handleCopyResult(this, copySuccess); // Use helper for feedback
                    });
                } else {
                    // Use fallback if modern API is not available or context is insecure
                    console.warn("Clipboard API not available or context insecure. Using fallback copy method.");
                    copySuccess = fallbackCopyTextToClipboard(textToCopy);
                    handleCopyResult(this, copySuccess); // Use helper for feedback
                }
            } else {
                console.error('Target element not found:', targetId);
                showNotification('复制出错：找不到目标元素', 'error');
            }
        });
    });
}

// 加载错误日志数据
async function loadErrorLogs() {
    showLoading(true);
    showError(false);
    showNoData(false);

    const offset = (currentPage - 1) * pageSize;

    try {
        // Construct the API URL with search parameters
        let apiUrl = `/api/logs/errors?limit=${pageSize}&offset=${offset}`;
        if (currentSearch.key) {
            apiUrl += `&key_search=${encodeURIComponent(currentSearch.key)}`;
        }
        if (currentSearch.error) {
            apiUrl += `&error_search=${encodeURIComponent(currentSearch.error)}`;
        }
        if (currentSearch.startDate) {
            apiUrl += `&start_date=${encodeURIComponent(currentSearch.startDate)}`;
        }
        if (currentSearch.endDate) {
            apiUrl += `&end_date=${encodeURIComponent(currentSearch.endDate)}`;
        }

        const response = await fetch(apiUrl);
        if (!response.ok) {
            // Try to get error message from response body
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                // Ignore if response is not JSON
            }
            throw new Error(errorData?.detail || `网络响应异常: ${response.statusText}`);
        }
        const data = await response.json();
        // Assuming the API returns an object like { logs: [], total: count }
        // If it only returns an array, we can't get the total count accurately for pagination
        if (Array.isArray(data)) {
            errorLogs = data;
            renderErrorLogs(errorLogs); // Pass data directly
            updatePagination(errorLogs.length, -1); // Indicate unknown total
        } else if (data && Array.isArray(data.logs)) {
            errorLogs = data.logs;
            renderErrorLogs(errorLogs); // Pass logs array
            updatePagination(errorLogs.length, data.total || -1); // Pass total count if available
        } else {
             throw new Error('无法识别的API响应格式');
        }


        showLoading(false);

        if (errorLogs.length === 0) {
            showNoData(true);
        }
    } catch (error) {
        console.error('获取错误日志失败:', error);
        showLoading(false);
        showError(true, error.message); // Show specific error message
    }
}


// 渲染错误日志表格
function renderErrorLogs(logs) {
    if (!tableBody) return;
    tableBody.innerHTML = ''; // Clear previous entries

    if (!logs || logs.length === 0) {
        // Handled by showNoData
        return;
    }

    const startIndex = (currentPage - 1) * pageSize; // Calculate starting index for the current page

    logs.forEach((log, index) => { // Add index parameter to forEach
        const row = document.createElement('tr');
        const sequentialId = startIndex + index + 1; // Calculate sequential ID for the current page
        // Format date
        let formattedTime = 'N/A';
        try {
            const requestTime = new Date(log.request_time);
            if (!isNaN(requestTime)) {
                 formattedTime = requestTime.toLocaleString('zh-CN', {
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
                });
            }
        } catch (e) { console.error("Error formatting date:", e); }


        // Truncate error log content for display
        const errorLogContent = log.error_log ? log.error_log.substring(0, 100) + (log.error_log.length > 100 ? '...' : '') : '无';

        // Mask the Gemini key for display in the table
        const maskKey = (key) => {
            if (!key || key.length < 8) return key || '无'; // Don't mask short keys or null
            return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
        };
        const maskedKey = maskKey(log.gemini_key);

        row.innerHTML = `
            <td>${sequentialId}</td> <!-- Use sequential ID -->
            <td title="${log.gemini_key || ''}">${maskedKey}</td>
            <td>${log.error_type || '未知'}</td>
            <td class="error-log-content" title="${log.error_log || ''}">${errorLogContent}</td>
            <td>${log.model_name || '未知'}</td>
            <td>${formattedTime}</td>
            <td>
                <button class="btn-view-details" data-log-id="${log.id}">
                    查看详情
                </button>
            </td>
        `;

        tableBody.appendChild(row);
    });

    // Add event listeners to new 'View Details' buttons
    document.querySelectorAll('.btn-view-details').forEach(button => {
        button.addEventListener('click', function() {
            const logId = parseInt(this.getAttribute('data-log-id'));
            showLogDetails(logId);
        });
    });
}

// 显示错误日志详情 (Custom Modal Logic)
function showLogDetails(logId) {
    const log = errorLogs.find(l => l.id === logId);
    if (!log || !logDetailModal) return;

    // Format date
     let formattedTime = 'N/A';
     try {
         const requestTime = new Date(log.request_time);
         if (!isNaN(requestTime)) {
              formattedTime = requestTime.toLocaleString('zh-CN', {
                 year: 'numeric', month: '2-digit', day: '2-digit',
                 hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
             });
         }
     } catch (e) { console.error("Error formatting date:", e); }


    // Format request message (handle potential JSON)
    let formattedRequestMsg = '无';
    if (log.request_msg) {
        try {
            // Check if it's already an object/array
            if (typeof log.request_msg === 'object' && log.request_msg !== null) {
                 formattedRequestMsg = JSON.stringify(log.request_msg, null, 2);
            }
            // Check if it's a JSON string
            else if (typeof log.request_msg === 'string' && log.request_msg.trim().startsWith('{') || log.request_msg.trim().startsWith('[')) {
                formattedRequestMsg = JSON.stringify(JSON.parse(log.request_msg), null, 2);
            }
             else {
                formattedRequestMsg = String(log.request_msg);
            }
        } catch (e) {
            formattedRequestMsg = String(log.request_msg); // Fallback to string
            console.warn("Could not parse request_msg as JSON:", e);
        }
    }

    // Populate modal content (show full key in modal)
    document.getElementById('modalGeminiKey').textContent = log.gemini_key || '无';
    document.getElementById('modalErrorType').textContent = log.error_type || '未知';
    document.getElementById('modalErrorLog').textContent = log.error_log || '无';
    document.getElementById('modalRequestMsg').textContent = formattedRequestMsg;
    document.getElementById('modalModelName').textContent = log.model_name || '未知';
    document.getElementById('modalRequestTime').textContent = formattedTime;

    // Show the modal
    logDetailModal.classList.add('show');
    // Optional: Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

// Close Log Detail Modal
function closeLogDetailModal() {
     if (logDetailModal) {
        logDetailModal.classList.remove('show');
        // Optional: Restore body scrolling
        document.body.style.overflow = '';
     }
}


// 更新分页控件
function updatePagination(currentItemCount, totalItems) {
    if (!paginationElement) return;
    paginationElement.innerHTML = ''; // Clear existing pagination

    // Calculate total pages only if totalItems is known and valid
    let totalPages = 1;
    if (totalItems >= 0) {
        totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    } else if (currentItemCount < pageSize && currentPage === 1) {
        // If less items than page size fetched on page 1, assume it's the only page
        totalPages = 1;
    } else {
        // If total is unknown and more items might exist, we can't build full pagination
        // We can show Prev/Next based on current page and if items were returned
        console.warn("Total item count unknown, pagination will be limited.");
        // Basic Prev/Next for unknown total
        addPaginationLink(paginationElement, '&laquo;', currentPage > 1, () => { currentPage--; loadErrorLogs(); });
        addPaginationLink(paginationElement, currentPage.toString(), true, null, true); // Current page number (non-clickable)
        addPaginationLink(paginationElement, '&raquo;', currentItemCount === pageSize, () => { currentPage++; loadErrorLogs(); }); // Next enabled if full page was returned
        return; // Exit here for limited pagination
    }


    const maxPagesToShow = 5; // Max number of page links to show
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    // Adjust startPage if endPage reaches the limit first
     if (endPage === totalPages) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }


    // Previous Button
    addPaginationLink(paginationElement, '&laquo;', currentPage > 1, () => { currentPage--; loadErrorLogs(); });

    // First Page Button
    if (startPage > 1) {
        addPaginationLink(paginationElement, '1', true, () => { currentPage = 1; loadErrorLogs(); });
        if (startPage > 2) {
            addPaginationLink(paginationElement, '...', false); // Ellipsis
        }
    }

    // Page Number Buttons
    for (let i = startPage; i <= endPage; i++) {
        addPaginationLink(paginationElement, i.toString(), true, () => { currentPage = i; loadErrorLogs(); }, i === currentPage);
    }

     // Last Page Button
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
             addPaginationLink(paginationElement, '...', false); // Ellipsis
        }
        addPaginationLink(paginationElement, totalPages.toString(), true, () => { currentPage = totalPages; loadErrorLogs(); });
    }


    // Next Button
    addPaginationLink(paginationElement, '&raquo;', currentPage < totalPages, () => { currentPage++; loadErrorLogs(); });
}

// Helper function to add pagination links
function addPaginationLink(parentElement, text, enabled, clickHandler, isActive = false) {
    const pageItem = document.createElement('li');
    // 移除 'page-item' 和 'active' 类，使用 Tailwind 类进行样式化
    // pageItem.className = `page-item ${!enabled ? 'disabled' : ''} ${isActive ? 'active' : ''}`;

    const pageLink = document.createElement('a');
    // 使用 Tailwind 类进行样式化
    pageLink.className = `px-3 py-1 rounded-md text-sm transition duration-150 ease-in-out ${
        isActive
            ? 'bg-primary-600 text-white font-semibold shadow-md cursor-default' // 突出当前页样式
            : enabled
                ? 'bg-white text-gray-700 hover:bg-primary-50 hover:text-primary-600 border border-gray-300' // 可点击页码样式
                : 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200' // 禁用状态样式 (如 '...')
    }`;
    pageLink.href = '#'; // Prevent page jump
    pageLink.innerHTML = text;

    if (enabled && clickHandler) {
        pageLink.addEventListener('click', function(e) {
            e.preventDefault();
            clickHandler();
        });
    } else if (!enabled) {
         pageLink.addEventListener('click', e => e.preventDefault()); // Prevent click on disabled or active
    } else if (isActive) {
        pageLink.addEventListener('click', e => e.preventDefault()); // Prevent click on active page
    }

    // 不再需要 li 元素，直接将 a 元素添加到父元素
    // pageItem.appendChild(pageLink);
    parentElement.appendChild(pageLink);
}


// 显示/隐藏状态指示器 (using 'active' class)
function showLoading(show) {
    if (loadingIndicator) loadingIndicator.style.display = show ? 'block' : 'none';
}

function showNoData(show) {
     if (noDataMessage) noDataMessage.style.display = show ? 'block' : 'none';
}

function showError(show, message = '加载错误日志失败，请稍后重试。') {
    if (errorMessage) {
        errorMessage.style.display = show ? 'block' : 'none';
        if (show) {
            // Update the error message content
            const p = errorMessage.querySelector('p');
            if (p) p.textContent = message;
        }
    }
}

// Function to show temporary status notifications (like copy success)
function showNotification(message, type = 'success', duration = 3000) {
    const notificationElement = document.getElementById('copyStatus'); // Or a more generic ID if needed
    if (!notificationElement) return;

    notificationElement.textContent = message;
    notificationElement.className = `notification ${type} show`; // Add 'show' class

    // Hide after duration
    setTimeout(() => {
        notificationElement.classList.remove('show');
    }, duration);
}

// Example Usage (if copy functionality is added later):
// showNotification('密钥已复制!', 'success');
// showNotification('复制失败!', 'error');
