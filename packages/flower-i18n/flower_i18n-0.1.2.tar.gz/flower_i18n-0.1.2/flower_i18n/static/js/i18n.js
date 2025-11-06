/**
 * Flower i18n - Language switching functionality
 */

(function() {
    'use strict';

    // Translation data
    const translations = {
        'en_US': {
            'nav.workers': 'Workers',
            'nav.tasks': 'Tasks',
            'nav.broker': 'Broker',
            'nav.documentation': 'Documentation',
            'workers.title': 'Workers',
            'workers.worker': 'Worker',
            'workers.name': 'Name',
            'workers.status': 'Status',
            'workers.active': 'Active',
            'workers.processed': 'Processed',
            'workers.failed': 'Failed',
            'workers.succeeded': 'Succeeded',
            'workers.retried': 'Retried',
            'workers.load_average': 'Load Average',
            'tasks.title': 'Tasks',
            'tasks.name': 'Name',
            'tasks.uuid': 'UUID',
            'tasks.state': 'State',
            'tasks.args': 'args',
            'tasks.kwargs': 'kwargs',
            'tasks.result': 'Result',
            'tasks.received': 'Received',
            'tasks.started': 'Started',
            'tasks.runtime': 'Runtime',
            'tasks.worker': 'Worker',
            'tasks.exchange': 'Exchange',
            'tasks.routing_key': 'Routing Key',
            'tasks.retries': 'Retries',
            'tasks.revoked': 'Revoked',
            'tasks.exception': 'Exception',
            'tasks.expires': 'Expires',
            'tasks.eta': 'ETA',
            'broker.title': 'Broker',
            'broker.url': 'URL',
            'broker.transport': 'Transport',
            'broker.queue': 'Queue',
            'broker.messages': 'Messages',
            'broker.unacked': 'Unacked',
            'broker.ready': 'Ready',
            'broker.consumers': 'Consumers',
            'broker.idle_since': 'Idle since',
            'state.pending': 'Pending',
            'state.started': 'Started',
            'state.success': 'Success',
            'state.failure': 'Failure',
            'state.retry': 'Retry',
            'state.revoked': 'Revoked',
            'common.refresh': 'Refresh',
            'common.search': 'Search',
            'common.filter': 'Filter',
            'common.export': 'Export',
            'common.settings': 'Settings',
            'common.language': 'Language',
            'common.loading': 'Loading...',
            'common.no_data': 'No data available',
            'common.error': 'Error',
            'common.close': 'Close',
            'common.total': 'Total',
            'worker.pool': 'Pool',
            'worker.broker': 'Broker',
            'worker.queues': 'Queues',
            'worker.tasks': 'Tasks',
            'worker.limits': 'Limits',
            'worker.config': 'Config',
            'worker.system': 'System',
            'worker.other': 'Other',
            'worker.shutdown': 'Shut Down',
            'worker.restart_pool': 'Restart Pool',
            'worker.refresh': 'Refresh',
            'worker.refresh_all': 'Refresh All',
            'worker.pool_size_control': 'Pool size control',
            'worker.pool_size': 'Pool size',
            'worker.grow': 'Grow',
            'worker.shrink': 'Shrink',
            'worker.auto_scale': 'Auto scale',
            'worker.autoscale': 'Autoscale',
            'worker.worker_pid': 'Worker PID',
            'worker.prefetch_count': 'Prefetch Count',
            'worker.pool_options': 'Worker pool options',
            'worker.broker_options': 'Broker options',
            'worker.config_options': 'Configuration options',
            'worker.system_stats': 'System usage statistics',
            'worker.other_stats': 'Other statistics',
            'worker.queue_arguments': 'Queue arguments'
        },
        'zh_CN': {
            'nav.workers': '工作进程',
            'nav.tasks': '任务',
            'nav.broker': '消息代理',
            'nav.documentation': '文档',
            'workers.title': '工作进程',
            'workers.worker': '工作进程',
            'workers.name': '名称',
            'workers.status': '状态',
            'workers.active': '活跃',
            'workers.processed': '已处理',
            'workers.failed': '失败',
            'workers.succeeded': '成功',
            'workers.retried': '重试',
            'workers.load_average': '负载平均值',
            'tasks.title': '任务',
            'tasks.name': '名称',
            'tasks.uuid': 'UUID',
            'tasks.state': '状态',
            'tasks.args': '参数',
            'tasks.kwargs': '关键字参数',
            'tasks.result': '结果',
            'tasks.received': '接收时间',
            'tasks.started': '开始时间',
            'tasks.runtime': '运行时间',
            'tasks.worker': '工作进程',
            'tasks.exchange': '交换机',
            'tasks.routing_key': '路由键',
            'tasks.retries': '重试次数',
            'tasks.revoked': '已撤销',
            'tasks.exception': '异常',
            'tasks.expires': '过期时间',
            'tasks.eta': '预计时间',
            'broker.title': '消息代理',
            'broker.url': '地址',
            'broker.transport': '传输方式',
            'broker.queue': '队列',
            'broker.messages': '消息数',
            'broker.unacked': '未确认',
            'broker.ready': '就绪',
            'broker.consumers': '消费者',
            'broker.idle_since': '空闲时长',
            'state.pending': '等待中',
            'state.started': '运行中',
            'state.success': '成功',
            'state.failure': '失败',
            'state.retry': '重试',
            'state.revoked': '已撤销',
            'common.refresh': '刷新',
            'common.search': '搜索',
            'common.filter': '筛选',
            'common.export': '导出',
            'common.settings': '设置',
            'common.language': '语言',
            'common.loading': '加载中...',
            'common.no_data': '暂无数据',
            'common.error': '错误',
            'common.close': '关闭',
            'common.total': '总计',
            'worker.pool': '进程池',
            'worker.broker': '消息代理',
            'worker.queues': '队列',
            'worker.tasks': '任务',
            'worker.limits': '限制',
            'worker.config': '配置',
            'worker.system': '系统',
            'worker.other': '其他',
            'worker.shutdown': '关闭',
            'worker.restart_pool': '重启进程池',
            'worker.refresh': '刷新',
            'worker.refresh_all': '全部刷新',
            'worker.pool_size_control': '进程池大小控制',
            'worker.pool_size': '进程池大小',
            'worker.grow': '增加',
            'worker.shrink': '减少',
            'worker.auto_scale': '自动伸缩',
            'worker.autoscale': '自动伸缩',
            'worker.worker_pid': '工作进程 PID',
            'worker.prefetch_count': '预取数量',
            'worker.pool_options': '工作进程池选项',
            'worker.broker_options': '消息代理选项',
            'worker.config_options': '配置选项',
            'worker.system_stats': '系统使用统计',
            'worker.other_stats': '其他统计',
            'worker.queue_arguments': '队列参数'
        }
    };

    // Get current locale from cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Set cookie
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    }

    // Get translation
    function translate(key, locale) {
        if (translations[locale] && translations[locale][key]) {
            return translations[locale][key];
        }
        return key;
    }

    // Apply translations to all elements with data-i18n attribute
    function applyTranslations(locale) {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = translate(key, locale);
            element.textContent = translation;
        });
    }

    // Switch language
    function switchLanguage(locale) {
        setCookie('flower_locale', locale, 365);
        applyTranslations(locale);
        updateLanguageSwitcher(locale);
    }

    // Update language switcher display
    function updateLanguageSwitcher(locale) {
        const dropdownToggle = document.querySelector('#languageDropdown');
        if (dropdownToggle) {
            const icon = dropdownToggle.querySelector('svg');
            const iconHTML = icon ? icon.outerHTML : '';
            dropdownToggle.innerHTML = iconHTML + (locale === 'zh_CN' ? ' 中文' : ' English');
        }

        // Update active state
        document.querySelectorAll('[data-locale]').forEach(item => {
            if (item.getAttribute('data-locale') === locale) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // Initialize language switcher
    function initLanguageSwitcher() {
        const currentLocale = getCookie('flower_locale') || 'en_US';

        // Apply translations immediately
        applyTranslations(currentLocale);

        // Create language switcher dropdown
        const languageSwitcher = `
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle text-dark" href="#" id="languageDropdown"
                   role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                         class="bi bi-translate" viewBox="0 0 16 16">
                        <path d="M4.545 6.714 4.11 8H3l1.862-5h1.284L8 8H6.833l-.435-1.286H4.545zm1.634-.736L5.5 3.956h-.049l-.679 2.022H6.18z"/>
                        <path d="M0 2a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v3h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-3H2a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2zm7.138 9.995c.193.301.402.583.63.846-.748.575-1.673 1.001-2.768 1.292.178.217.451.635.555.867 1.125-.359 2.08-.844 2.886-1.494.777.665 1.739 1.165 2.93 1.472.133-.254.414-.673.629-.89-1.125-.253-2.057-.694-2.82-1.284.681-.747 1.222-1.651 1.621-2.757H14V8h-3v1.047h.765c-.318.844-.74 1.546-1.272 2.13a6.066 6.066 0 0 1-.415-.492 1.988 1.988 0 0 1-.94.31z"/>
                    </svg>
                    ${currentLocale === 'zh_CN' ? ' 中文' : ' English'}
                </a>
                <ul class="dropdown-menu" aria-labelledby="languageDropdown">
                    <li><a class="dropdown-item ${currentLocale === 'en_US' ? 'active' : ''}"
                           href="#" data-locale="en_US">English</a></li>
                    <li><a class="dropdown-item ${currentLocale === 'zh_CN' ? 'active' : ''}"
                           href="#" data-locale="zh_CN">中文</a></li>
                </ul>
            </li>
        `;

        // Find the navbar nav element and add language switcher
        const navbarNav = document.querySelector('.navbar-nav.mr-auto');
        if (navbarNav) {
            navbarNav.insertAdjacentHTML('beforeend', languageSwitcher);

            // Add event listeners
            document.querySelectorAll('[data-locale]').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    const locale = this.getAttribute('data-locale');
                    switchLanguage(locale);
                });
            });
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLanguageSwitcher);
    } else {
        initLanguageSwitcher();
    }

    // Export to global scope if needed
    window.FlowerI18n = {
        switchLanguage: switchLanguage,
        getCurrentLocale: function() {
            return getCookie('flower_locale') || 'en_US';
        },
        translate: translate
    };
})();