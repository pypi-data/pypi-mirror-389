"""
Rendering templates for Auth App
Defines how authentication-related data should be rendered in chat interfaces
"""

# Profile Card Rendering Template
PROFILE_CARD_TEMPLATE = {
    "type": "profile_card",
    "name": "User Profile Card",
    "description": "Renders user profile information in a beautiful card format",
    "detector": {
        "required_fields": ["user_id", "username"],
        "optional_fields": ["email", "display_name", "role", "mobile_number", "created_at"]
    },
    "html_template": """
<div class="auth-profile-card">
    <div class="profile-header">
        <div class="profile-avatar">
            <i class="bi bi-person-circle"></i>
        </div>
        <div class="profile-info">
            <h3 class="profile-name">{{display_name}}</h3>
            <p class="profile-username">@{{username}}</p>
        </div>
    </div>
    <div class="profile-details">
        {{#if email}}
        <div class="profile-field">
            <i class="bi bi-envelope"></i>
            <span>{{email}}</span>
        </div>
        {{/if}}
        {{#if role}}
        <div class="profile-field">
            <i class="bi bi-shield-check"></i>
            <span class="role-badge">{{role}}</span>
        </div>
        {{/if}}
        {{#if mobile_number}}
        <div class="profile-field">
            <i class="bi bi-phone"></i>
            <span>{{mobile_number}}</span>
            {{#if mobile_verified}}
            <i class="bi bi-check-circle-fill verified"></i>
            {{/if}}
        </div>
        {{/if}}
        {{#if created_at}}
        <div class="profile-field">
            <i class="bi bi-calendar"></i>
            <span>Member since {{format_date created_at}}</span>
        </div>
        {{/if}}
        {{#if credentials}}
        <div class="profile-field">
            <i class="bi bi-key"></i>
            <span>{{credentials.length}} credential{{#if_plural credentials.length}}s{{/if_plural}}</span>
        </div>
        {{/if}}
    </div>
</div>
""",
    "css": """
/* Auth App - Profile Card Styles */
.auth-profile-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    color: white;
    margin: 8px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.auth-profile-card .profile-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
}

.auth-profile-card .profile-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
}

.auth-profile-card .profile-info {
    flex: 1;
}

.auth-profile-card .profile-name {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
}

.auth-profile-card .profile-username {
    margin: 4px 0 0 0;
    opacity: 0.9;
    font-size: 14px;
}

.auth-profile-card .profile-details {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    backdrop-filter: blur(10px);
}

.auth-profile-card .profile-field {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
}

.auth-profile-card .profile-field i {
    font-size: 18px;
    opacity: 0.9;
    width: 24px;
}

.auth-profile-card .profile-field .verified {
    color: #4ade80;
    margin-left: 8px;
    font-size: 14px;
}

.auth-profile-card .role-badge {
    background: rgba(255, 255, 255, 0.25);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
"""
}

# Credentials List Template
CREDENTIALS_LIST_TEMPLATE = {
    "type": "credentials_list",
    "name": "Credentials List",
    "description": "Renders a list of user credentials",
    "detector": {
        "is_array": True,
        "item_has_fields": ["credential_id", "created_at"]
    },
    "html_template": """
<div class="auth-credentials-list">
    <h4><i class="bi bi-key"></i> Security Credentials</h4>
    <div class="credentials-items">
        {{#each credentials}}
        <div class="credential-item">
            <div class="credential-icon">
                <i class="bi bi-shield-lock"></i>
            </div>
            <div class="credential-info">
                <span class="credential-id">{{credential_id}}</span>
                <span class="credential-date">Added {{format_date created_at}}</span>
            </div>
        </div>
        {{/each}}
    </div>
</div>
""",
    "css": """
.auth-credentials-list {
    background: var(--message-bg);
    border-radius: 8px;
    padding: 16px;
    border-left: 3px solid #10a37f;
}

.auth-credentials-list h4 {
    margin: 0 0 12px 0;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.auth-credentials-list .credentials-items {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.auth-credentials-list .credential-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 6px;
}

.auth-credentials-list .credential-icon {
    font-size: 24px;
    color: var(--primary-color);
}

.auth-credentials-list .credential-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.auth-credentials-list .credential-id {
    font-family: monospace;
    font-size: 12px;
}

.auth-credentials-list .credential-date {
    font-size: 11px;
    opacity: 0.7;
}
"""
}

# Export all templates
RENDERING_TEMPLATES = {
    "profile_card": PROFILE_CARD_TEMPLATE,
    "credentials_list": CREDENTIALS_LIST_TEMPLATE
}


def get_templates():
    """Get all rendering templates for auth app."""
    return RENDERING_TEMPLATES


def detect_data_type(data):
    """
    Detect what type of auth data this is and return the appropriate template.
    
    Args:
        data: Dictionary or list to analyze
        
    Returns:
        Template name if detected, None otherwise
    """
    if isinstance(data, dict):
        # Check for profile data
        if "user_id" in data and "username" in data:
            return "profile_card"
    
    elif isinstance(data, list) and len(data) > 0:
        # Check for credentials list
        if isinstance(data[0], dict) and "credential_id" in data[0]:
            return "credentials_list"
    
    return None
