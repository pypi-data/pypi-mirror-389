/**
 * Flower i18n - Language switching functionality
 */

(function() {
    'use strict';

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

    // Switch language
    function switchLanguage(locale) {
        setCookie('flower_locale', locale, 365);
        location.reload();
    }

    // Initialize language switcher
    function initLanguageSwitcher() {
        const currentLocale = getCookie('flower_locale') || 'en_US';

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
                    ${currentLocale === 'zh_CN' ? '中文' : 'English'}
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
        }
    };
})();