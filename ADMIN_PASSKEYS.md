# Admin Passkey Management

This document describes the new admin-only passkey management flow added to NomNom.

## Features

### 1. Admin Dashboard Integration
- **Location**: Available from the main `/admin/` dashboard
- **Access**: Admin staff members only (requires `is_staff=True`)
- **Link**: "Account Security" section with "Passkeys" option

### 2. Passkey Management View (`/admin/passkeys/`)
- **View existing passkeys**: Lists all passkeys registered to your account
- **Passkey details**: Shows name, platform, registration date, and last used date
- **Delete passkeys**: Remove individual passkeys with confirmation
- **Add new passkeys**: Link to enrollment flow

### 3. Passkey Enrollment View (`/admin/passkeys/enroll/`)
- **Guided enrollment**: Step-by-step instructions for registering a passkey
- **Auto-naming**: Intelligent default names based on device/browser
- **Error handling**: Clear error messages and success feedback
- **WebAuthn integration**: Uses standard WebAuthn API

## Usage Flow

1. **Access**: Login to `/admin/` with username/password
2. **Navigate**: Click "Passkeys" under "Account Security" section
3. **Manage**: View existing passkeys or click "Add New Passkey"
4. **Enroll**: Enter a name and click "Register Passkey"
5. **Authenticate**: Follow browser prompts (Touch ID, Face ID, etc.)
6. **Complete**: Return to management view to see new passkey

## Technical Implementation

### Files Created/Modified:
- `src/nomnom/base/admin_views.py` - Django views for passkey management
- `src/nomnom/base/templates/admin/passkey_management.html` - Management interface
- `src/nomnom/base/templates/admin/passkey_enroll.html` - Enrollment interface  
- `src/nomnom/base/templates/admin/index.html` - Admin dashboard integration
- `src/nomnom/admin.py` - URL routing and admin site customization

### URL Patterns:
- `/admin/passkeys/` - Passkey management
- `/admin/passkeys/enroll/` - Passkey enrollment

### Security:
- Requires authentication (`@login_required`)
- Requires staff privileges (`@staff_member_required`)
- CSRF protection on all forms
- User isolation (users only see their own passkeys)

## Integration with Existing Flow

This admin flow integrates with the existing django-passkeys authentication:
- Uses same `UserPasskey` model
- Compatible with existing login flow at `/admin/login/`
- Leverages existing passkey registration endpoints
- Maintains all security features and WebAuthn standards

## Browser Compatibility

Supports all modern browsers with WebAuthn:
- Chrome/Edge 67+
- Firefox 60+
- Safari 14+
- Mobile browsers on iOS 16+ and Android 9+