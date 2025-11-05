/**
 * Auth App Rendering Components
 * Provides rendering functions for authentication-related data
 */

class AuthAppRenderer {
    constructor() {
        this.name = 'auth-app';
        this.version = '1.0.0';
    }

    /**
     * Check if this renderer can handle the given data
     */
    canRender(data, metadata) {
        if (!data || !data.content) return false;
        
        const content = data.content;
        
        // Check for profile data
        if (typeof content === 'object' && content.user_id && content.username) {
            return 'profile_card';
        }
        
        // Check for credentials list
        if (Array.isArray(content) && content.length > 0 && content[0].credential_id) {
            return 'credentials_list';
        }
        
        return false;
    }

    /**
     * Render profile card
     */
    renderProfileCard(data, metadata) {
        const content = data.content || {};
        
        const card = document.createElement('div');
        card.className = 'auth-profile-card';
        
        card.innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar">
                    <i class="bi bi-person-circle"></i>
                </div>
                <div class="profile-info">
                    <h3 class="profile-name">${this.escape(content.display_name || content.username || 'Unknown')}</h3>
                    <p class="profile-username">@${this.escape(content.username || 'unknown')}</p>
                </div>
            </div>
            <div class="profile-details">
                ${content.email ? `
                    <div class="profile-field">
                        <i class="bi bi-envelope"></i>
                        <span>${this.escape(content.email)}</span>
                    </div>
                ` : ''}
                ${content.role ? `
                    <div class="profile-field">
                        <i class="bi bi-shield-check"></i>
                        <span class="role-badge">${this.escape(content.role)}</span>
                    </div>
                ` : ''}
                ${content.mobile_number ? `
                    <div class="profile-field">
                        <i class="bi bi-phone"></i>
                        <span>${this.escape(content.mobile_number)}</span>
                        ${content.mobile_verified ? '<i class="bi bi-check-circle-fill verified"></i>' : ''}
                    </div>
                ` : ''}
                ${content.created_at ? `
                    <div class="profile-field">
                        <i class="bi bi-calendar"></i>
                        <span>Member since ${this.formatDate(content.created_at)}</span>
                    </div>
                ` : ''}
                ${content.credentials && content.credentials.length > 0 ? `
                    <div class="profile-field">
                        <i class="bi bi-key"></i>
                        <span>${content.credentials.length} credential${content.credentials.length !== 1 ? 's' : ''}</span>
                    </div>
                ` : ''}
            </div>
        `;
        
        return card;
    }

    /**
     * Render credentials list
     */
    renderCredentialsList(data, metadata) {
        const credentials = data.content || [];
        
        const container = document.createElement('div');
        container.className = 'auth-credentials-list';
        
        const header = document.createElement('h4');
        header.innerHTML = '<i class="bi bi-key"></i> Security Credentials';
        container.appendChild(header);
        
        const itemsContainer = document.createElement('div');
        itemsContainer.className = 'credentials-items';
        
        credentials.forEach(cred => {
            const item = document.createElement('div');
            item.className = 'credential-item';
            item.innerHTML = `
                <div class="credential-icon">
                    <i class="bi bi-shield-lock"></i>
                </div>
                <div class="credential-info">
                    <span class="credential-id">${this.escape(cred.credential_id || 'Unknown')}</span>
                    <span class="credential-date">Added ${this.formatDate(cred.created_at)}</span>
                </div>
            `;
            itemsContainer.appendChild(item);
        });
        
        container.appendChild(itemsContainer);
        return container;
    }

    /**
     * Main render method
     */
    render(block) {
        const renderType = this.canRender(block.data, block.metadata);
        
        if (renderType === 'profile_card') {
            return this.renderProfileCard(block.data, block.metadata);
        } else if (renderType === 'credentials_list') {
            return this.renderCredentialsList(block.data, block.metadata);
        }
        
        return null;
    }

    /**
     * Helper: Format date
     */
    formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (e) {
            return dateStr;
        }
    }

    /**
     * Helper: Escape HTML
     */
    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Register with window for global access
window.AuthAppRenderer = AuthAppRenderer;

// Auto-register if RenderingSystem is available
if (window.RenderingSystem) {
    window.RenderingSystem.registerAppRenderer(new AuthAppRenderer());
    console.log('✅ Auth App Renderer registered');
}
