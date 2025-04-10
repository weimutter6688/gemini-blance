// 错误日志页面JavaScript (Updated for new structure, no Bootstrap)

// 页面滚动功能
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// 刷新页面功能
function refreshPage(button) {
    if (button) {
        // Use 'loading' class consistent with config_editor.css animation
        button.classList.add('loading');
        // Disable button while refreshing
        button.disabled = true;
    }

    // Fetch new data instead of full reload for a smoother experience
    loadErrorLogs().finally(() => {
        if (button) {
            // Remove loading class and re-enable button after fetch completes
            button.classList.remove('loading');
            button.disabled = false;
        }
    });
    // Optional: Keep reload as fallback or if preferred
    // setTimeout(() => {
    //     window.location.reload();
    // }, 500);
}

// 全局变量
let currentPage = 1;
let pageSize = 20;
// let totalPages = 1; // totalPages will be calculated dynamically based on API response if available, or based on fetched data length
let errorLogs = []; // Store fetched logs for details view

// DOM Elements Cache
let pageSizeSelector;
let refreshBtn;
let tableBody;
let paginationElement;
let loadingIndicator;
let noDataMessage;
let errorMessage;
let logDetailModal;
let modalCloseBtns; // Collection of close buttons for the modal

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    pageSizeSelector = document.getElementById('pageSize');
    refreshBtn = document.getElementById('refreshBtn');
    tableBody = document.getElementById('errorLogsTable');
    paginationElement = document.getElementById('pagination');
    loadingIndicator = document.getElementById('loadingIndicator');
    noDataMessage = document.getElementById('noDataMessage');
    errorMessage = document.getElementById('errorMessage');
    logDetailModal = document.getElementById('logDetailModal');
    // Get all elements that should close the modal
    modalCloseBtns = document.querySelectorAll('#closeLogDetailModalBtn, #closeModalFooterBtn');

    // Initialize page size selector
    if (pageSizeSelector) {
        pageSizeSelector.value = pageSize;
        pageSizeSelector.addEventListener('change', function() {
            pageSize = parseInt(this.value);
            currentPage = 1; // Reset to first page
            loadErrorLogs();
        });
    }

    // Initialize refresh button (using the one inside the controls container)
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Add loading state to the button itself
            this.classList.add('loading');
            this.disabled = true;
            loadErrorLogs().finally(() => {
                 this.classList.remove('loading');
                 this.disabled = false;
            });
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
});

// 加载错误日志数据
async function loadErrorLogs() {
    showLoading(true);
    showError(false);
    showNoData(false);

    const offset = (currentPage - 1) * pageSize;

    try {
        const response = await fetch(`/api/logs/errors?limit=${pageSize}&offset=${offset}`);
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

    logs.forEach(log => {
        const row = document.createElement('tr');

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

        row.innerHTML = `
            <td>${log.id}</td>
            <td>${log.gemini_key || '无'}</td>
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

    // Populate modal content
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
    pageItem.className = `page-item ${!enabled ? 'disabled' : ''} ${isActive ? 'active' : ''}`;

    const pageLink = document.createElement('a');
    pageLink.className = 'page-link';
    pageLink.href = '#'; // Prevent page jump
    pageLink.innerHTML = text;

    if (enabled && clickHandler) {
        pageLink.addEventListener('click', function(e) {
            e.preventDefault();
            clickHandler();
        });
    } else if (!enabled) {
         pageLink.addEventListener('click', e => e.preventDefault()); // Prevent click on disabled
    }


    pageItem.appendChild(pageLink);
    parentElement.appendChild(pageItem);
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
