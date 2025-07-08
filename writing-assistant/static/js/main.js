/**
 * AI智能写作辅导软件 - 增强版JavaScript工具库
 */

// 页面加载时间标记
window.pageLoadTime = Date.now();

// 全局工具对象
const Utils = {
    // API请求配置
    apiConfig: {
        baseURL: '/api',
        timeout: 30000,
        retryCount: 3,
        retryDelay: 1000
    },

    // 缓存管理
    cache: new Map(),
    
    // 事件监听器管理
    eventListeners: new Map(),

    /**
     * 增强的API请求函数
     */
    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiConfig.baseURL}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };

        const config = { ...defaultOptions, ...options };
        
        // 添加请求ID用于追踪
        const requestId = this.generateId();
        console.log(`[API Request ${requestId}] ${config.method} ${url}`);

        let lastError;
        
        // 重试机制
        for (let attempt = 1; attempt <= this.apiConfig.retryCount; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.apiConfig.timeout);
                
                config.signal = controller.signal;
                
                const response = await fetch(url, config);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log(`[API Response ${requestId}] Success`, data);
                
                return data;
                
            } catch (error) {
                lastError = error;
                console.warn(`[API Request ${requestId}] Attempt ${attempt} failed:`, error.message);
                
                if (attempt < this.apiConfig.retryCount && error.name !== 'AbortError') {
                    await this.delay(this.apiConfig.retryDelay * attempt);
                    continue;
                }
                
                break;
            }
        }
        
        console.error(`[API Request ${requestId}] All attempts failed:`, lastError);
        throw lastError;
    },

    /**
     * 增强的提示消息系统 - 使用全局顶部提示
     */
    showAlert(message, type = 'info', duration = 5000, actions = []) {
        const globalAlert = document.getElementById('globalAlert');
        const alertMessage = document.getElementById('alertMessage');
        const alertIcon = document.getElementById('alertIcon');
        
        if (!globalAlert || !alertMessage || !alertIcon) {
            console.warn('Global alert elements not found, falling back to toast');
            return this.showToast(message, type, duration, actions);
        }
        
        // 图标映射
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        // 设置消息内容和图标
        alertMessage.textContent = message;
        alertIcon.className = icons[type] + ' me-2';
        
        // 重置样式类
        globalAlert.className = 'alert alert-dismissible fade show';
        if (type === 'error') {
            globalAlert.classList.add('alert-danger');
        } else {
            globalAlert.classList.add('alert-' + type);
        }
        
        // 显示警告框
        globalAlert.style.display = 'block';
        
        // 自动消失
        if (duration > 0) {
            setTimeout(() => {
                if (globalAlert.classList.contains('show')) {
                    const bsAlert = new bootstrap.Alert(globalAlert);
                    bsAlert.close();
                }
            }, duration);
        }
        
        // 监听关闭事件
        globalAlert.addEventListener('closed.bs.alert', () => {
            globalAlert.style.display = 'none';
            globalAlert.className = 'alert alert-dismissible fade';
        }, { once: true });
        
        return 'global-alert';
    },

    /**
     * 备用的Toast提示系统
     */
    showToast(message, type = 'info', duration = 5000, actions = []) {
        const alertId = this.generateId();
        const alertContainer = this.getOrCreateAlertContainer();
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.setAttribute('role', 'alert');
        alertElement.setAttribute('data-alert-id', alertId);
        
        // 图标映射
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        let actionsHtml = '';
        if (actions.length > 0) {
            actionsHtml = '<div class="alert-actions mt-2">';
            actions.forEach(action => {
                actionsHtml += `<button type="button" class="btn btn-sm btn-outline-${type} me-2" onclick="${action.onClick}">${action.text}</button>`;
            });
            actionsHtml += '</div>';
        }
        
        alertElement.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="${icons[type]} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <div>${message}</div>
                    ${actionsHtml}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        // 添加动画类
        alertElement.classList.add('slide-in-right');
        
        alertContainer.appendChild(alertElement);
        
        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                this.removeAlert(alertId);
            }, duration);
        }
        
        // 添加点击事件
        const closeBtn = alertElement.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            this.removeAlert(alertId);
        });
        
        return alertId;
    },

    /**
     * 移除提示消息
     */
    removeAlert(alertId) {
        const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertElement) {
            alertElement.classList.add('fade-out');
            setTimeout(() => {
                alertElement.remove();
            }, 300);
        }
    },

    /**
     * 获取或创建提示消息容器
     */
    getOrCreateAlertContainer() {
        let container = document.getElementById('alert-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'alert-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    },

    /**
     * 加载状态管理
     */
    showLoading(element, text = '加载中...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;
        
        // 保存原始内容
        element.dataset.originalContent = element.innerHTML;
        element.dataset.originalDisabled = element.disabled;
        
        // 设置加载状态
        element.disabled = true;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${text}
        `;
        
        element.classList.add('loading');
    },

    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;
        
        // 恢复原始状态
        element.innerHTML = element.dataset.originalContent || '';
        element.disabled = element.dataset.originalDisabled === 'true';
        
        element.classList.remove('loading');
        
        // 清理数据属性
        delete element.dataset.originalContent;
        delete element.dataset.originalDisabled;
    },

    /**
     * 模态框管理
     */
    showModal(options) {
        const modalId = options.id || this.generateId();
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-hidden', 'true');
        
        const size = options.size ? `modal-${options.size}` : '';
        const backdrop = options.backdrop !== false ? 'data-bs-backdrop="static"' : '';
        
        modal.innerHTML = `
            <div class="modal-dialog ${size}" ${backdrop}>
                <div class="modal-content">
                    ${options.header ? `
                        <div class="modal-header">
                            <h5 class="modal-title">${options.title || ''}</h5>
                            ${options.closable !== false ? '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' : ''}
                        </div>
                    ` : ''}
                    <div class="modal-body">
                        ${options.content || ''}
                    </div>
                    ${options.footer ? `
                        <div class="modal-footer">
                            ${options.footer}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal, {
            backdrop: options.backdrop !== false ? 'static' : true,
            keyboard: options.keyboard !== false
        });
        
        // 事件监听
        if (options.onShow) {
            modal.addEventListener('show.bs.modal', options.onShow);
        }
        
        if (options.onHide) {
            modal.addEventListener('hide.bs.modal', options.onHide);
        }
        
        // 自动清理
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
        
        bsModal.show();
        return bsModal;
    },

    /**
     * 确认对话框
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const modal = this.showModal({
                title: options.title || '确认操作',
                content: `<p>${message}</p>`,
                footer: `
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        ${options.cancelText || '取消'}
                    </button>
                    <button type="button" class="btn btn-${options.type || 'primary'}" id="confirm-btn">
                        ${options.confirmText || '确认'}
                    </button>
                `,
                onShow: () => {
                    const confirmBtn = document.getElementById('confirm-btn');
                    confirmBtn.addEventListener('click', () => {
                        modal.hide();
                        resolve(true);
                    });
                },
                onHide: () => {
                    resolve(false);
                }
            });
        });
    },

    /**
     * 表单验证
     */
    validateForm(form, rules = {}) {
        if (typeof form === 'string') {
            form = document.querySelector(form);
        }
        
        const errors = [];
        const formData = new FormData(form);
        
        Object.entries(rules).forEach(([fieldName, rule]) => {
            const value = formData.get(fieldName);
            const field = form.querySelector(`[name="${fieldName}"]`);
            
            // 清除之前的错误状态
            this.clearFieldError(field);
            
            // 必填验证
            if (rule.required && (!value || value.trim() === '')) {
                const error = `${rule.label || fieldName} 不能为空`;
                errors.push(error);
                this.setFieldError(field, error);
                return;
            }
            
            if (value) {
                // 最小长度验证
                if (rule.minLength && value.length < rule.minLength) {
                    const error = `${rule.label || fieldName} 最少需要 ${rule.minLength} 个字符`;
                    errors.push(error);
                    this.setFieldError(field, error);
                }
                
                // 最大长度验证
                if (rule.maxLength && value.length > rule.maxLength) {
                    const error = `${rule.label || fieldName} 最多只能 ${rule.maxLength} 个字符`;
                    errors.push(error);
                    this.setFieldError(field, error);
                }
                
                // 正则验证
                if (rule.pattern && !rule.pattern.test(value)) {
                    const error = rule.message || `${rule.label || fieldName} 格式不正确`;
                    errors.push(error);
                    this.setFieldError(field, error);
                }
                
                // 自定义验证
                if (rule.validator && typeof rule.validator === 'function') {
                    const result = rule.validator(value);
                    if (result !== true) {
                        const error = result || `${rule.label || fieldName} 验证失败`;
                        errors.push(error);
                        this.setFieldError(field, error);
                    }
                }
            }
        });
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * 设置字段错误状态
     */
    setFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        
        feedback.textContent = message;
    },

    /**
     * 清除字段错误状态
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    },

    /**
     * 本地存储管理
     */
    storage: {
        set(key, value, expiry = null) {
            const item = {
                value: value,
                timestamp: Date.now(),
                expiry: expiry
            };
            localStorage.setItem(key, JSON.stringify(item));
        },

        get(key, defaultValue = null) {
            try {
                const item = JSON.parse(localStorage.getItem(key));
                if (!item) return defaultValue;
                
                // 检查过期时间
                if (item.expiry && Date.now() > item.timestamp + item.expiry) {
                    localStorage.removeItem(key);
                    return defaultValue;
                }
                
                return item.value;
            } catch {
                return defaultValue;
            }
        },

        remove(key) {
            localStorage.removeItem(key);
        },

        clear() {
            localStorage.clear();
        }
    },

    /**
     * 防抖函数
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * 节流函数
     */
    throttle(func, delay) {
        let lastCall = 0;
        return function (...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    },

    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * 生成唯一ID
     */
    generateId() {
        return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * 格式化日期
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (!date) return '';
        
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },

    /**
     * 字数统计
     */
    countWords(text) {
        if (!text) return 0;
        // 移除空白字符后计算长度
        return text.replace(/\s/g, '').length;
    },

    /**
     * 文本截断
     */
    truncateText(text, maxLength, suffix = '...') {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength - suffix.length) + suffix;
    },

    /**
     * 复制到剪贴板
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showAlert('已复制到剪贴板', 'success', 2000);
            return true;
        } catch (error) {
            console.error('复制失败:', error);
            this.showAlert('复制失败', 'error', 3000);
            return false;
        }
    },

    /**
     * 文件下载
     */
    downloadFile(content, filename, type = 'text/plain') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    /**
     * 图片压缩
     */
    compressImage(file, quality = 0.8, maxWidth = 1920, maxHeight = 1080) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                // 计算新尺寸
                let { width, height } = img;
                
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                
                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                // 绘制压缩后的图片
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(resolve, file.type, quality);
            };
            
            img.src = URL.createObjectURL(file);
        });
    },

    /**
     * 设备检测
     */
    device: {
        isMobile: () => /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
        isTablet: () => /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent),
        isDesktop: () => !this.isMobile() && !this.isTablet(),
        isIOS: () => /iPad|iPhone|iPod/.test(navigator.userAgent),
        isAndroid: () => /Android/.test(navigator.userAgent),
        isSafari: () => /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent),
        isChrome: () => /Chrome/.test(navigator.userAgent),
        isFirefox: () => /Firefox/.test(navigator.userAgent)
    },

    /**
     * 性能监控
     */
    performance: {
        mark(name) {
            if (window.performance && window.performance.mark) {
                window.performance.mark(name);
            }
        },

        measure(name, startMark, endMark) {
            if (window.performance && window.performance.measure) {
                window.performance.measure(name, startMark, endMark);
                const entries = window.performance.getEntriesByName(name);
                return entries[entries.length - 1];
            }
        },

        getNavigationTiming() {
            if (window.performance && window.performance.getEntriesByType) {
                const navigation = window.performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    totalTime: navigation.loadEventEnd - navigation.fetchStart
                };
            }
        }
    },

    // 获取用户设置
    getUserSettings: function() {
        return {
            grade: localStorage.getItem('userGrade') || '',
            subject: localStorage.getItem('userSubject') || '',
            aiProvider: localStorage.getItem('aiProvider') || '',
            aiModel: localStorage.getItem('aiModel') || '',
            aiBaseUrl: localStorage.getItem('aiBaseUrl') || ''
        };
    },
    
    // 保存用户设置
    saveUserSettings: function(settings) {
        Object.keys(settings).forEach(key => {
            localStorage.setItem(key, settings[key]);
        });
    }
};

// 键盘快捷键管理
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            try {
                const key = this.getKeyString(e);
                
                // 如果无法识别键，直接返回
                if (!key) {
                    return;
                }
                
                const handler = this.shortcuts.get(key);
                
                if (handler) {
                    e.preventDefault();
                    handler(e);
                }
            } catch (error) {
                console.warn('键盘快捷键处理错误:', error);
            }
        });
    }

    getKeyString(e) {
        const parts = [];
        
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        if (e.metaKey) parts.push('meta');
        
        // 检查 e.key 是否存在，避免 undefined 错误
        if (e.key && typeof e.key === 'string') {
            parts.push(e.key.toLowerCase());
        } else {
            // 如果 e.key 不可用，使用 keyCode 作为备选
            const keyCode = e.keyCode || e.which;
            if (keyCode) {
                parts.push(`key${keyCode}`);
            } else {
                return null; // 无法识别的键
            }
        }
        
        return parts.join('+');
    }

    register(keyString, handler, description = '') {
        this.shortcuts.set(keyString, handler);
        console.log(`注册快捷键: ${keyString} - ${description}`);
    }

    unregister(keyString) {
        this.shortcuts.delete(keyString);
    }

    getAll() {
        return Array.from(this.shortcuts.keys());
    }
}

// 自动保存管理
class AutoSave {
    constructor(options = {}) {
        this.interval = options.interval || 30000; // 30秒
        this.callback = options.callback;
        this.enabled = options.enabled !== false;
        this.timer = null;
        this.lastSaveTime = 0;
        this.changes = false;
    }

    start() {
        if (!this.enabled || !this.callback) return;
        
        this.timer = setInterval(() => {
            if (this.changes && Date.now() - this.lastSaveTime > this.interval) {
                this.save();
            }
        }, 5000); // 每5秒检查一次
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    markChanged() {
        this.changes = true;
    }

    async save() {
        if (!this.changes) return;
        
        try {
            await this.callback();
            this.changes = false;
            this.lastSaveTime = Date.now();
            console.log('自动保存成功');
        } catch (error) {
            console.error('自动保存失败:', error);
        }
    }

    forceSave() {
        return this.save();
    }
}

// 全局实例
const shortcuts = new KeyboardShortcuts();
const autoSave = new AutoSave();

// 注册默认快捷键
shortcuts.register('ctrl+s', (e) => {
    autoSave.forceSave();
    Utils.showAlert('手动保存', 'info', 2000);
}, '保存');

shortcuts.register('ctrl+/', (e) => {
    Utils.showModal({
        title: '键盘快捷键',
        content: `
            <div class="shortcut-list">
                <div class="shortcut-item">
                    <kbd>Ctrl + S</kbd>
                    <span>保存当前内容</span>
                </div>
                <div class="shortcut-item">
                    <kbd>Ctrl + /</kbd>
                    <span>显示快捷键帮助</span>
                </div>
                <div class="shortcut-item">
                    <kbd>Esc</kbd>
                    <span>关闭模态框</span>
                </div>
            </div>
            <style>
                .shortcut-list { line-height: 2; }
                .shortcut-item { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
                kbd { background: #f8f9fa; padding: 0.25rem 0.5rem; border-radius: 4px; }
            </style>
        `,
        size: 'sm'
    });
}, '显示快捷键帮助');

shortcuts.register('escape', (e) => {
    // 关闭最顶层的模态框
    const modals = document.querySelectorAll('.modal.show');
    if (modals.length > 0) {
        const topModal = modals[modals.length - 1];
        const bsModal = bootstrap.Modal.getInstance(topModal);
        if (bsModal) {
            bsModal.hide();
        }
    }
}, '关闭模态框');

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    // 添加页面加载动画
    document.body.classList.add('fade-in');
    
    // 启动性能监控
    Utils.performance.mark('page-interactive');
    
    // 全局错误处理已在文件底部定义，这里移除重复
    
    // 添加网络状态监控
    window.addEventListener('online', () => {
        Utils.showAlert('网络连接已恢复', 'success', 3000);
    });
    
    window.addEventListener('offline', () => {
        Utils.showAlert('网络连接已断开', 'warning');
    });
    
    // 添加页面可见性监控
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // 页面隐藏时强制保存
            autoSave.forceSave();
        }
    });
    
    // 启动自动保存
    autoSave.start();
    
    console.log('AI智能写作辅导软件已加载完成');
});

// 页面卸载前保存
window.addEventListener('beforeunload', (e) => {
    if (autoSave.changes) {
        autoSave.forceSave();
        e.preventDefault();
        e.returnValue = '您有未保存的更改，确定要离开吗？';
    }
});

// 导出工具对象
window.Utils = Utils;
window.KeyboardShortcuts = KeyboardShortcuts;
window.AutoSave = AutoSave;

// 用户设置管理
const UserSettings = {
    // 更新用户学习设置
    updateUserSettings: async function() {
        const grade = document.getElementById('navGradeSelect')?.value;
        const subject = document.getElementById('navSubjectSelect')?.value;
        
        if (!grade || !subject) {
            console.warn('年级或学科未选择');
            return;
        }
        
        try {
            const result = await Utils.apiRequest('/users/settings', {
                method: 'PUT',
                body: JSON.stringify({ grade, subject })
            });
            
            if (result && result.success) {
                Utils.showAlert('学习设置更新成功', 'success', 3000);
                Utils.saveUserSettings({ userGrade: grade, userSubject: subject });
            } else {
                Utils.showAlert(result?.message || '设置更新失败', 'danger');
            }
        } catch (error) {
            console.error('更新用户设置失败:', error);
            // 静默处理错误，不显示错误提示
            Utils.saveUserSettings({ userGrade: grade, userSubject: subject });
        }
    },
    
    // 更新AI设置
    updateAISettings: function() {
        const provider = document.getElementById('navAIProvider')?.value;
        const model = document.getElementById('navAIModel')?.value;
        const baseUrl = document.getElementById('navAIBaseUrl')?.value;
        const apiKey = document.getElementById('navAPIKey')?.value;
        
        if (!provider) {
            console.warn('请选择AI供应商');
            return;
        }
        
        // 根据供应商类型验证必需参数
        if (provider === 'Ollama' || provider === 'LMStudio') {
            if (!model || !baseUrl) {
                console.warn('本地服务需要选择模型和设置Base URL');
                return;
            }
        } else {
            if (!model) {
                console.warn('云端服务需要选择模型');
                return;
            }
        }
        
        try {
            const settings = {
                aiProvider: provider,
                aiModel: model,
                aiBaseUrl: baseUrl || ''  // 所有供应商都保存base URL
            };
            
            // 如果不是本地服务，也保存API Key
            if (provider !== 'Ollama' && provider !== 'LMStudio') {
                settings.aiApiKey = apiKey || '';
            }
            
            Utils.saveUserSettings(settings);
            
            Utils.showAlert('AI设置已保存', 'success', 3000);
            
            // 如果是Ollama或LMStudio，刷新模型列表
            if (provider === 'Ollama' || provider === 'LMStudio') {
                this.refreshAIModels();
            }
        } catch (error) {
            console.error('保存AI设置失败:', error);
            Utils.showAlert('保存AI设置失败', 'error');
        }
    },
    
    // 刷新AI模型列表
    refreshAIModels: async function() {
        const provider = document.getElementById('navAIProvider')?.value;
        const baseUrl = document.getElementById('navAIBaseUrl')?.value;
        
        if (!provider || !baseUrl) return;
        
        try {
            const endpoint = provider === 'Ollama' ? '/api/ai/models/ollama' : '/api/ai/models/lmstudio';
            const response = await fetch(`${endpoint}?base_url=${encodeURIComponent(baseUrl)}`);
            const result = await response.json();
            
            if (result.success && result.data.length > 0) {
                const modelSelect = document.getElementById('navAIModel');
                if (modelSelect) {
                    modelSelect.innerHTML = '';
                    
                    result.data.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                    
                    Utils.showAlert(`已刷新${provider}模型列表`, 'info');
                }
            }
        } catch (error) {
            console.warn('刷新模型列表失败:', error);
            Utils.showAlert('刷新模型列表失败', 'warning');
        }
    },
    
    // 测试AI连接
    testAIConnection: async function() {
        const settings = Utils.getUserSettings();
        
        Utils.showLoading(true);
        
        try {
            const response = await fetch('/api/ai/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: settings.aiProvider,
                    model: settings.aiModel,
                    base_url: settings.aiBaseUrl
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                Utils.showAlert('AI连接测试成功', 'success');
            } else {
                Utils.showAlert(result.message || 'AI连接测试失败', 'danger');
            }
        } catch (error) {
            console.error('AI连接测试失败:', error);
            Utils.showAlert('网络错误，请检查网络连接', 'danger');
        } finally {
            Utils.showLoading(false);
        }
    },
    
    // 初始化用户设置
    init: function() {
        const settings = Utils.getUserSettings();
        
        // 设置表单值
        const gradeSelect = document.getElementById('navGradeSelect');
        const subjectSelect = document.getElementById('navSubjectSelect');
        const providerSelect = document.getElementById('navAIProvider');
        const modelSelect = document.getElementById('navAIModel');
        const baseUrlInput = document.getElementById('navAIBaseUrl');
        const apiKeyInput = document.getElementById('navAPIKey');
        const baseUrlSection = document.getElementById('navBaseUrlSection');
        
        if (gradeSelect) gradeSelect.value = settings.grade;
        if (subjectSelect) subjectSelect.value = settings.subject;
        if (providerSelect) providerSelect.value = settings.aiProvider;
        if (modelSelect) modelSelect.value = settings.aiModel;
        if (baseUrlInput) baseUrlInput.value = settings.aiBaseUrl || '';
        if (apiKeyInput) apiKeyInput.value = settings.aiApiKey || '';
        
        // 永远显示Base URL字段
        if (baseUrlSection) baseUrlSection.style.display = 'block';
        
        // 如果有供应商选择，触发模型选项更新
        if (settings.aiProvider) {
            updateNavModelOptions();
        }
    }
};

// 导航功能
const Navigation = {
    // 初始化导航高亮
    initNavHighlight: function() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href)) {
                link.classList.add('active');
            }
        });
    },
    
    // 显示用户资料
    showUserProfile: function() {
        Utils.showAlert('个人资料功能正在开发中', 'info');
    },
    
    // 显示帮助
    showHelp: function() {
        Utils.showAlert('帮助中心功能正在开发中', 'info');
    },
    
    // 显示FAQ
    showFAQ: function() {
        Utils.showAlert('常见问题功能正在开发中', 'info');
    },
    
    // 显示联系我们
    showContact: function() {
        Utils.showAlert('联系我们功能正在开发中', 'info');
    },
    
    // 显示隐私政策
    showPrivacy: function() {
        Utils.showAlert('隐私政策功能正在开发中', 'info');
    },
    
    // 退出登录功能已移除
};

// 主题管理
const ThemeManager = {
    // 切换主题
    toggle: function() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // 更新图标
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        Utils.showAlert(`已切换到${newTheme === 'dark' ? '深色' : '浅色'}主题`, 'info', 2000);
    },
    
    // 初始化主题
    init: function() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // 更新图标
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
};

// 返回顶部功能
const BackToTop = {
    init: function() {
        const backToTopBtn = document.getElementById('backToTop');
        if (!backToTopBtn) return;
        
        window.addEventListener('scroll', Utils.throttle(() => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        }, 100));
        
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
};

// 全局函数（供HTML调用）
function updateUserSettings() {
    UserSettings.updateUserSettings();
}

function updateAISettings() {
    UserSettings.updateAISettings();
}

function refreshAIModels() {
    UserSettings.refreshAIModels();
}

function testAIConnection() {
    UserSettings.testAIConnection();
}

// 导航栏AI设置模型选项更新
function updateNavModelOptions() {
    const provider = document.getElementById('navAIProvider')?.value;
    const modelSelect = document.getElementById('navAIModel');
    const apiKeySection = document.getElementById('navApiKeySection');
    const baseUrlSection = document.getElementById('navBaseUrlSection');
    const baseUrlInput = document.getElementById('navAIBaseUrl');
    const apiKeyInput = document.getElementById('navAPIKey');
    
    if (!provider || !modelSelect) return;
    
    // 永远显示Base URL字段
    baseUrlSection.style.display = 'block';
    
    // 根据供应商类型显示/隐藏API Key字段
    if (provider === 'Ollama' || provider === 'LMStudio') {
        // 本地服务：隐藏API Key
        apiKeySection.style.display = 'none';
        
        // 设置默认BaseUrl（如果当前为空）
        if (!baseUrlInput.value) {
            if (provider === 'Ollama') {
                baseUrlInput.value = 'http://localhost:11434';
            } else if (provider === 'LMStudio') {
                baseUrlInput.value = 'http://localhost:1234';
            }
        }
        
        // 清空API Key
        apiKeyInput.value = '';
        
        // 获取本地模型列表
        modelSelect.innerHTML = '<option value="">加载中...</option>';
        UserSettings.refreshAIModels();
    } else if (provider) {
        // 云端服务：显示API Key
        apiKeySection.style.display = 'block';
        
        // 设置默认BaseUrl（如果当前为空）
        if (!baseUrlInput.value) {
            const defaultBaseUrls = {
                'OpenAI': 'https://api.openai.com/v1',
                'Anthropic': 'https://api.anthropic.com',
                'Google': 'https://generativelanguage.googleapis.com/v1beta',
                'Groq': 'https://api.groq.com/openai/v1',
                'DeepSeek': 'https://api.deepseek.com'
            };
            baseUrlInput.value = defaultBaseUrls[provider] || '';
        }
        
        // 预定义的云端模型列表
        const AI_MODELS = {
            'OpenAI': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
            'Anthropic': ['claude-3-5-haiku-latest', 'claude-3-5-sonnet-latest'],
            'Google': ['gemini-2.0-flash-exp', 'gemini-1.5-pro'],
            'Groq': ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'],
            'DeepSeek': ['deepseek-chat', 'deepseek-reasoner']
        };
        
        if (AI_MODELS[provider]) {
            modelSelect.innerHTML = '<option value="">请选择模型</option>';
            AI_MODELS[provider].forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        } else {
            modelSelect.innerHTML = '<option value="">暂无可用模型</option>';
        }
    } else {
        // 未选择供应商：隐藏API Key字段，但保持Base URL显示
        apiKeySection.style.display = 'none';
        modelSelect.innerHTML = '<option value="">请先选择供应商</option>';
        
        // 清空API Key但保留Base URL
        apiKeyInput.value = '';
    }
}

function showUserProfile() {
    Navigation.showUserProfile();
}

function showHelp() {
    Navigation.showHelp();
}

function showFAQ() {
    Navigation.showFAQ();
}

function showContact() {
    Navigation.showContact();
}

function showPrivacy() {
    Navigation.showPrivacy();
}

// 退出登录功能已移除

function toggleTheme() {
    ThemeManager.toggle();
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI智能写作辅导软件初始化...');
    
    // 隐藏加载进度条
    setTimeout(() => {
        const loadingBar = document.getElementById('loading-bar');
        if (loadingBar) {
            loadingBar.style.opacity = '0';
        }
    }, 500);
    
    // 初始化各个模块
    BackToTop.init();
    ThemeManager.init();
    Navigation.initNavHighlight();
    
    // 仅在登录状态下初始化用户设置
    if (document.getElementById('navGradeSelect')) {
        UserSettings.init();
    }
    
    console.log('页面初始化完成');
});

// 页面离开前的清理
window.addEventListener('beforeunload', function() {
    // 保存当前状态
    const currentSettings = Utils.getUserSettings();
    Utils.saveUserSettings(currentSettings);
});

// 未处理的Promise拒绝
window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise拒绝:', event.reason);
    // 阻止默认的错误处理，避免显示错误提示
    event.preventDefault();
});

// 错误处理
window.addEventListener('error', function(event) {
    console.error('页面错误:', event.error);
    
    // 页面加载时间标记
    if (!window.pageLoadTime) {
        window.pageLoadTime = Date.now();
    }
    
    // 更严格的错误过滤，避免误报
    if (event.error && event.error.message && 
        Date.now() - window.pageLoadTime > 3000 && // 页面加载3秒后才显示错误
        !event.error.message.includes('Script error') &&
        !event.error.message.includes('Non-Error promise rejection') &&
        !event.error.message.includes('ResizeObserver') &&
        !event.error.message.includes('Loading CSS chunk') &&
        !event.error.message.includes('Cannot read properties of undefined') &&
        !event.error.message.includes('getKeyString') &&
        !event.error.message.includes('KeyboardShortcuts') &&
        !event.error.message.includes('Utils') &&
        !event.error.message.includes('undefined') &&
        event.error.stack && 
        !event.filename?.includes('main.js') &&
        !event.filename?.includes('login')) {
        // 只有在真正的代码错误时才显示，排除键盘快捷键相关错误
        Utils.showAlert('页面出现错误，请刷新重试', 'danger');
    }
});

// 导出给其他文件使用
window.WritingAssistant = {
    Utils,
    UserSettings,
    Navigation,
    ThemeManager,
    BackToTop
};