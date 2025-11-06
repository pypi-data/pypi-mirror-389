# Aurica Auth SDK - Quick Start Guide

## Installation

The SDK is already available in your Aurica base backend. No installation needed!

## Basic Usage

### 1. Import the SDK

```python
from src.aurica_auth import protected, public, optional, get_current_user
```

### 2. Protect Your Endpoints

#### Protected Endpoint (Requires Authentication)

```python
from fastapi import APIRouter, Request
from src.aurica_auth import protected, get_current_user

router = APIRouter()

@router.get("/dashboard")
@protected
async def get_dashboard(request: Request):
    user = get_current_user(request)
    
    return {
        "message": f"Welcome {user.username}!",
        "user_id": user.user_id,
        "email": user.email
    }
```

#### Public Endpoint (No Authentication)

```python
@router.get("/status")
@public
async def get_status():
    return {"status": "online"}
```

#### Optional Authentication

```python
@router.get("/info")
@optional
async def get_info(request: Request):
    user = get_current_user(request, required=False)
    
    if user:
        return {"message": f"Hello {user.username}"}
    else:
        return {"message": "Hello guest"}
```

## User Object Properties

The `User` object provides type-safe access to user information:

```python
user = get_current_user(request)

# Available properties:
user.username      # str - Username
user.user_id       # str - User ID
user.email         # Optional[str] - Email (may be None)
user.token_type    # str - "jwt" or "session"
user.is_authenticated  # bool - Always True for protected endpoints
user.raw_data      # Dict - Full user data dictionary
```

## Configuration

### Configure Public Routes

In your app's `app.json`:

```json
{
  "name": "your-app",
  "version": "1.0.0",
  "requires": ["authentication"],
  "public_routes": [
    "/api/your-app/public-endpoint",
    "/static/*"
  ]
}
```

## Complete Example

```python
"""
API endpoints for my-app.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from src.aurica_auth import protected, public, optional, get_current_user

router = APIRouter()

class DataModel(BaseModel):
    value: str

# Protected endpoint - authentication required
@router.post("/create")
@protected
async def create_item(request: Request, data: DataModel):
    user = get_current_user(request)
    
    return {
        "created_by": user.username,
        "user_id": user.user_id,
        "data": data.value
    }

# Public endpoint - no authentication
@router.get("/list")
@public
async def list_items():
    return {"items": ["item1", "item2"]}

# Optional authentication - personalized if logged in
@router.get("/recommended")
@optional
async def get_recommendations(request: Request):
    user = get_current_user(request, required=False)
    
    if user:
        # Return personalized recommendations
        return {
            "for_user": user.username,
            "recommendations": ["based", "on", "history"]
        }
    else:
        # Return generic recommendations
        return {
            "recommendations": ["generic", "items"]
        }
```

## Decorator Reference

| Decorator | Description | User Required |
|-----------|-------------|---------------|
| `@protected` | Requires authentication. Returns 401 if not authenticated. | Yes |
| `@public` | No authentication needed. Endpoint is publicly accessible. | No |
| `@optional` | Authentication is optional. Works for both logged-in and guest users. | No |

### Legacy Aliases (Backward Compatible)

- `@auth_required` → Use `@protected`
- `@public_route` → Use `@public`
- `@optional_auth` → Use `@optional`

## Error Handling

```python
@router.get("/data")
@protected
async def get_data(request: Request):
    user = get_current_user(request)
    
    # User is guaranteed to exist here because of @protected
    # No need for null checks!
    
    if not user.email:
        raise HTTPException(
            status_code=400, 
            detail="Email required"
        )
    
    return {"email": user.email}
```

## Type Safety Benefits

The SDK provides full type hints for IDE support:

```python
# IDE will autocomplete these properties:
user.username
user.user_id
user.email
user.token_type

# IDE will catch typos at edit time:
user.usrname  # ❌ Error: Property doesn't exist
user['username']  # ⚠️ Works but not type-safe
```

## Testing Your Endpoints

### Protected Endpoint
```bash
# Without token - should return 401
curl http://localhost:8000/api/your-app/create

# With token - should work
curl -H "Authorization: Bearer <your-token>" \
     http://localhost:8000/api/your-app/create
```

### Public Endpoint
```bash
# Should work without authentication
curl http://localhost:8000/api/your-app/list
```

### Optional Auth Endpoint
```bash
# Works without auth (guest)
curl http://localhost:8000/api/your-app/recommended

# Works with auth (personalized)
curl -H "Authorization: Bearer <your-token>" \
     http://localhost:8000/api/your-app/recommended
```

## Authentication Sources

The SDK automatically checks for tokens in:

1. **Authorization Header**: `Authorization: Bearer <token>`
2. **Cookie**: `session=<session-id>`
3. **Query Parameter**: `?token=<token>`

You don't need to handle this - the SDK does it automatically!

## Common Patterns

### Check User Permissions

```python
@router.delete("/item/{item_id}")
@protected
async def delete_item(request: Request, item_id: str):
    user = get_current_user(request)
    
    # Check if user owns the item
    item = get_item(item_id)
    if item.owner != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    delete_item(item_id)
    return {"status": "deleted"}
```

### Log User Activity

```python
@router.post("/action")
@protected
async def perform_action(request: Request):
    user = get_current_user(request)
    
    print(f"🔐 User {user.username} (ID: {user.user_id}) performed action")
    
    # Your action logic here
    return {"status": "success"}
```

### Conditional Features

```python
@router.get("/features")
@optional
async def get_features(request: Request):
    user = get_current_user(request, required=False)
    
    features = ["basic_feature"]
    
    if user:
        # Add premium features for authenticated users
        features.extend(["premium_feature", "personalization"])
    
    return {"features": features}
```

## Migration from Dict-based Auth

If you're migrating from the old `universal_auth.py`:

**Before:**
```python
user = get_current_user(request)
name = user['username']
email = user.get('email', 'N/A')
```

**After:**
```python
user = get_current_user(request)
name = user.username
email = user.email or 'N/A'
```

## Need Help?

- Check the full documentation: `AUTH_GUIDE.md` in aurica-base-be
- See migration examples: `SDK_MIGRATION.md` in aurica-base-be
- Review working examples in: `/apps/dashboard-app/be/api/stats.py`

## Quick Reference Card

```python
# Import
from src.aurica_auth import protected, public, optional, get_current_user

# Decorators
@protected  # Requires auth
@public     # No auth needed
@optional   # Auth optional

# Get user
user = get_current_user(request)           # Required (throws error if not found)
user = get_current_user(request, required=False)  # Optional (returns None if not found)

# User properties
user.username      # String
user.user_id       # String
user.email         # Optional[String]
user.token_type    # "jwt" or "session"
user.is_authenticated  # Boolean
user.raw_data      # Dict with all data
```

---

**Built with ❤️ for Aurica Apps**
