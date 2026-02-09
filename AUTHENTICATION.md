# Multi-User Authentication Setup

This file is automatically created when you first run the application.

## Default Account

When you first run the app, a default admin account is created:
- **Username:** admin
- **Password:** admin

⚠️ **IMPORTANT:** Change this password immediately after first login!

## User Registration

New users can register through the web interface:
1. Go to the login page
2. Click "New User Registration"
3. Fill in username, name, email, and password
4. **Optional:** Set up account recovery:
   - Security Question: Choose and answer a personal question
5. Click "Register"
6. **IMPORTANT:** Save your recovery code displayed on screen
7. Login with new credentials

## Password Recovery

If you forget your password, you have two recovery options:

### Option 1: Recovery Code
- Use the 16-character code shown during registration
- Click "Forgot Password? Recover Account"
- Select "Recovery Code" method
- Enter your username and recovery code
- Set your new password

### Option 2: Security Question
- Use the security question you set during registration
- Click "Forgot Password? Recover Account"
- Select "Security Question" method
- Enter your username
- Answer your security question
- Set your new password

⚠️ **Save Your Recovery Code:** The recovery code is shown only once during registration. Store it in a password manager or secure location.

## Changing Passwords

### For Logged-In Users
Users can change their password after logging in (planned feature).

### For Administrators
Admins can reset any user's password programmatically:

```python
from auth_config import change_password
change_password('username', 'new_password')
```

## Security Notes

- All passwords are hashed using bcrypt
- Recovery codes are hashed using SHA-256
- Security question answers are hashed (case-insensitive)
- User data is stored in a local SQLite database (`user_data.db`)
- Each user has completely separate data
- Credentials are stored in `credentials.yaml` (excluded from git)

## File Security

**Never commit these files to version control:**
- `credentials.yaml` - Contains hashed passwords
- `user_data.db` - Contains all user data

Both files are already in `.gitignore`.

## Multi-User Hosting

To host this for multiple users:

1. **Local Network:**
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```
   Access from other devices: `http://YOUR_IP:8501`

2. **Cloud Deployment:**
   - Streamlit Cloud (free tier for private apps)
   - AWS, Google Cloud, Azure
   - Heroku, Railway, Render
   
⚠️ For production deployment, additionally implement:
- HTTPS/SSL encryption
- Regular database backups
- Session timeout policies
- Password complexity requirements

## Changing Passwords

Users can reset passwords by contacting the admin, who can run:

```python
from auth_config import change_password
change_password('username', 'new_password')
```

## Adding Users Programmatically

```python
from auth_config import register_new_user

register_new_user(
    username='john_doe',
    name='John Doe',
    password='secure_password',
    email='john@example.com'
)
```
