/**
 * Aurica Authentication Helper
 * Include this script in any page that requires authentication
 * Supports centralized authentication flow ONLY
 */

(function() {
    'use strict';

    // Configuration - ALL authentication goes through centralized auth server
    const CONFIG = window.AUTH_CONFIG || {
        AUTH_SERVER: 'https://api.oneaurica.com',  // Always use centralized auth server
        AUTH_CHECK_URL: '/auth-app/api/authenticate/current-user',
        LOGIN_URL: '/auth-app/api/centralized_auth/login',
        LOGOUT_URL: '/auth-app/api/authenticate/logout',
        VERIFY_URL: '/auth-app/api/centralized_auth/verify-token'
    };

    /**
     * Get authentication token from URL parameters or storage
     * @returns {string|null} Token or null
     */
    function getTokenFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        if (token) {
            // Store token for future use
            localStorage.setItem('auth_token', token);
            
            // Clean URL by removing token parameter
            urlParams.delete('token');
            const newSearch = urlParams.toString();
            const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '');
            window.history.replaceState({}, '', newUrl);
        }
        
        return token;
    }

    /**
     * Check if the user is authenticated
     * @returns {Promise<object|null>} User data if authenticated, null otherwise
     */
    async function checkAuth() {
        // First check if there's a token in the URL (from redirect)
        const tokenFromURL = getTokenFromURL();
        
        // Get token from localStorage (might have been set by getTokenFromURL or previous session)
        let token = localStorage.getItem('auth_token');
        
        // If no token in localStorage, try to check with the server (which will use cookie)
        if (!token && !tokenFromURL) {
            // No token in URL or localStorage, but there might be a cookie
            // Try to check auth anyway - server will use cookie
            try {
                const response = await fetch(CONFIG.AUTH_CHECK_URL, {
                    credentials: 'include'  // Send cookies
                });

                if (response.ok) {
                    const userData = await response.json();
                    // Store token and user data
                    if (userData.token) {
                        localStorage.setItem('auth_token', userData.token);
                        token = userData.token;
                    }
                    localStorage.setItem('username', userData.username);
                    localStorage.setItem('user_id', userData.user_id);
                    return userData;
                } else {
                    return null;
                }
            } catch (error) {
                console.error('Authentication check failed:', error);
                return null;
            }
        }
        
        if (!token) {
            return null;
        }

        try {
            // Check auth on local server (each server validates tokens locally via JWKS)
            const response = await fetch(CONFIG.AUTH_CHECK_URL, {
                credentials: 'include',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                // Store user data
                localStorage.setItem('username', userData.username);
                localStorage.setItem('user_id', userData.user_id);
                return userData;
            } else {
                // Token is invalid, clear it
                localStorage.removeItem('auth_token');
                localStorage.removeItem('username');
                localStorage.removeItem('user_id');
                return null;
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            return null;
        }
    }

    /**
     * Redirect to centralized auth server for login
     */
    function redirectToLogin() {
        const currentUrl = window.location.href;
        
        // ALWAYS redirect to centralized auth server
        const loginUrl = `${CONFIG.AUTH_SERVER}${CONFIG.LOGIN_URL}?redirect_uri=${encodeURIComponent(currentUrl)}`;
        console.log('🔄 Redirecting to centralized auth server:', loginUrl);
        window.location.href = loginUrl;
    }

    /**
     * Initialize authentication check
     * Call this function to require authentication on page load
     */
    async function requireAuth() {
        const userData = await checkAuth();
        
        if (!userData) {
            redirectToLogin();
            return null;
        }

        return userData;
    }

    /**
     * Logout function - handles centralized auth
     */
    async function logout() {
        const AUTH_SERVER = 'https://api.oneaurica.com';
        const currentOrigin = window.location.origin;
        
        // Clear local storage first
        localStorage.removeItem('auth_token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_id');

        // Clear session storage
        sessionStorage.removeItem('redirect_uri');
        sessionStorage.removeItem('redirect_state');
        
        // If on localhost/non-auth server, redirect to centralized auth server logout
        if (currentOrigin !== AUTH_SERVER) {
            console.log('🔄 Redirecting to centralized auth server for logout...');
            // Redirect to auth server with logout parameter
            // This will show the login page after logout
            window.location.href = `${AUTH_SERVER}/auth-app/static/?logout=true`;
            return;
        }
        
        // On auth server, call logout API
        try {
            await fetch('/auth-app/api/authenticate/logout', {
                method: 'POST',
                credentials: 'include'
            });
            console.log('✅ Logged out from auth server');
        } catch (error) {
            console.error('Logout error:', error);
        }

        // Redirect to login page
        window.location.href = '/auth-app/static/';
    }

    /**
     * Get current user data
     * @returns {Promise<object|null>}
     */
    async function getCurrentUser() {
        return await checkAuth();
    }

    /**
     * Make an authenticated API request
     * @param {string} url - API endpoint URL
     * @param {object} options - Fetch options
     * @returns {Promise<Response>}
     */
    async function authenticatedFetch(url, options = {}) {
        const token = localStorage.getItem('auth_token');
        
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        const response = await fetch(url, mergedOptions);

        // If unauthorized, redirect to login
        if (response.status === 401) {
            redirectToLogin();
            throw new Error('Authentication required');
        }

        return response;
    }

    // Expose API
    window.AuricaAuth = {
        checkAuth,
        requireAuth,
        logout,
        getCurrentUser,
        authenticatedFetch,
        redirectToLogin
    };

    // Auto-check authentication if configured
    if (window.AuricaAuthConfig && window.AuricaAuthConfig.autoCheck) {
        document.addEventListener('DOMContentLoaded', async () => {
            await requireAuth();
        });
    }
})();
