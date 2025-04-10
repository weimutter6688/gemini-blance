// 错误日志页面JavaScript

// 页面滚动功能
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function scrollToBottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

// 刷新页面功能
function refreshPage(button) {
    if (button) {
        button.classList.add('rotating');
    }
    
    setTimeout(() => {
        window.location.reload();
    }, 500);
}

// 全局变量
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let errorLogs = [];

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面大小选择器
    const pageSizeSelector = document.getElementById('pageSize');
    pageSizeSelector.value = pageSize;
    pageSizeSelector.addEventListener('change', function() {
        pageSize = parseInt(this.value);
        currentPage = 1; // 重置到第一页
        loadErrorLogs();
    });
    
    // 初始化刷新按钮
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadErrorLogs();
    });
    
    // 加载错误日志数据
    loadErrorLogs();
});

// 加载错误日志数据
function loadErrorLogs() {
    showLoading(true);
    showError(false);
    showNoData(false);
    
    const offset = (currentPage - 1) * pageSize;
    
    fetch(`/api/logs/errors?limit=${pageSize}&offset=${offset}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(data => {
            errorLogs = data;
            renderErrorLogs();
            showLoading(false);
            
            if (errorLogs.length === 0) {
                showNoData(true);
            }
        })
        .catch(error => {
            console.error('获取错误日志失败:', error);
            showLoading(false);
            showError(true);
        });
}

// 渲染错误日志表格
function renderErrorLogs() {
    const tableBody = document.getElementById('errorLogsTable');
    tableBody.innerHTML = '';
    
    errorLogs.forEach(log => {
        const row = document.createElement('tr');
        
        // 格式化日期
        const requestTime = new Date(log.request_time);
        const formattedTime = requestTime.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // 截断错误日志内容
        const errorLogContent = log.error_log ? log.error_log.substring(0, 100) + (log.error_log.length > 100 ? '...' : '') : '无';
        
        row.innerHTML = `
            <td>${log.id}</td>
            <td>${log.gemini_key || '无'}</td>
            <td class="error-log-content">${errorLogContent}</td>
            <td>${log.model_name || '未知'}</td>
            <td>${formattedTime}</td>
            <td>
                <button class="btn btn-sm btn-primary btn-view-details" data-log-id="${log.id}">
                    查看详情
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 添加详情按钮事件监听
    document.querySelectorAll('.btn-view-details').forEach(button => {
        button.addEventListener('click', function() {
            const logId = parseInt(this.getAttribute('data-log-id'));
            showLogDetails(logId);
        });
    });
    
    // 更新分页
    updatePagination();
}

// 显示错误日志详情
function showLogDetails(logId) {
    const log = errorLogs.find(log => log.id === logId);
    if (!log) return;
    
    // 格式化日期
    const requestTime = new Date(log.request_time);
    const formattedTime = requestTime.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // 格式化请求消息
    let formattedRequestMsg = '';
    if (log.request_msg) {
        try {
            if (typeof log.request_msg === 'string') {
                formattedRequestMsg = log.request_msg;
            } else {
                formattedRequestMsg = JSON.stringify(log.request_msg, null, 2);
            }
        } catch (e) {
            formattedRequestMsg = String(log.request_msg);
        }
    } else {
        formattedRequestMsg = '无';
    }
    
    // 填充模态框内容
    document.getElementById('modalGeminiKey').textContent = log.gemini_key || '无';
    document.getElementById('modalErrorLog').textContent = log.error_log || '无';
    document.getElementById('modalRequestMsg').textContent = formattedRequestMsg;
    // Add model name display logic here - assuming an element with id 'modalModelName' exists
    document.getElementById('modalModelName').textContent = log.model_name || '未知';
    document.getElementById('modalRequestTime').textContent = formattedTime;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
    modal.show();
}

// 更新分页控件
function updatePagination() {
    const paginationElement = document.getElementById('pagination');
    paginationElement.innerHTML = '';
    
    // 计算总页数
    const totalCount = errorLogs.length;
    totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
    
    // 上一页按钮
    const prevItem = document.createElement('li');
    prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevItem.innerHTML = `<a class="page-link" href="#" aria-label="上一页"><span aria-hidden="true">&laquo;</span></a>`;
    prevItem.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            loadErrorLogs();
        }
    });
    paginationElement.appendChild(prevItem);
    
    // 页码按钮
    for (let i = 1; i <= totalPages; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageItem.addEventListener('click', function(e) {
            e.preventDefault();
            currentPage = i;
            loadErrorLogs();
        });
        paginationElement.appendChild(pageItem);
    }
    
    // 下一页按钮
    const nextItem = document.createElement('li');
    nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextItem.innerHTML = `<a class="page-link" href="#" aria-label="下一页"><span aria-hidden="true">&raquo;</span></a>`;
    nextItem.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            loadErrorLogs();
        }
    });
    paginationElement.appendChild(nextItem);
}

// 显示/隐藏加载指示器
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (show) {
        loadingIndicator.classList.remove('d-none');
    } else {
        loadingIndicator.classList.add('d-none');
    }
}

// 显示/隐藏错误消息
function showError(show) {
    const errorMessage = document.getElementById('errorMessage');
    if (show) {
        errorMessage.classList.remove('d-none');
    } else {
        errorMessage.classList.add('d-none');
    }
}

// 显示/隐藏无数据消息
function showNoData(show) {
    const noDataMessage = document.getElementById('noDataMessage');
    if (show) {
        noDataMessage.classList.remove('d-none');
    } else {
        noDataMessage.classList.add('d-none');
    }
}
