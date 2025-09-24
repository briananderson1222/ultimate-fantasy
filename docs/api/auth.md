# Authentication API

## Overview

The Authentication API provides secure user registration, login, password management, and account operations for the Ultimate Fantasy Platform.

## Base URL

```
/api/v1/auth
```

## Endpoints

### Register User

Create a new user account.

**POST** `/register`

#### Request Body

```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "2024-01-01T00:00:00Z",
  "timezone": "UTC"
}
```

#### Validation Rules

- `username`: 3-30 characters, alphanumeric and underscores only
- `email`: Valid email address
- `password`: Minimum 8 characters
- `first_name`, `last_name`: 1-50 characters
- `timezone`: Valid timezone identifier

#### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600
  }
}
```

#### Error Codes

- `EMAIL_ALREADY_EXISTS` - Email address is already registered
- `USERNAME_ALREADY_EXISTS` - Username is already taken
- `WEAK_PASSWORD` - Password doesn't meet security requirements
- `VALIDATION_ERROR` - Invalid input data

---

### Login

Authenticate a user and receive access tokens.

**POST** `/login`

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "string",
  "remember_me": false
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "last_login": "2024-01-01T00:00:00Z"
    },
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600
  }
}
```

#### Error Codes

- `AUTHENTICATION_ERROR` - Invalid credentials
- `ACCOUNT_DISABLED` - User account is disabled
- `TOO_MANY_ATTEMPTS` - Account temporarily locked due to failed attempts
- `USER_NOT_FOUND` - Email address not found

---

### Refresh Token

Get a new access token using a refresh token.

**POST** `/refresh`

#### Request Body

```json
{
  "refresh_token": "refresh-token"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "new-jwt-token",
    "expires_in": 3600
  }
}
```

#### Error Codes

- `INVALID_TOKEN` - Refresh token is invalid or malformed
- `TOKEN_EXPIRED` - Refresh token has expired

---

### Logout

Invalidate user tokens and end session.

**POST** `/logout`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Successfully logged out"
  }
}
```

---

### Get Current User

Get current authenticated user information.

**GET** `/me`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "date_of_birth": "2024-01-01T00:00:00Z",
      "timezone": "UTC",
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-01T00:00:00Z",
      "is_verified": true,
      "is_active": true
    }
  }
}
```

---

### Update Profile

Update user profile information.

**PUT** `/profile`

**Authentication Required**

#### Request Body

```json
{
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "2024-01-01T00:00:00Z",
  "timezone": "UTC"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "date_of_birth": "2024-01-01T00:00:00Z",
      "timezone": "UTC",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### Change Password

Change user password.

**PUT** `/password`

**Authentication Required**

#### Request Body

```json
{
  "current_password": "string",
  "new_password": "string"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Password updated successfully"
  }
}
```

#### Error Codes

- `AUTHENTICATION_ERROR` - Current password is incorrect
- `WEAK_PASSWORD` - New password doesn't meet requirements

---

### Request Password Reset

Request a password reset email.

**POST** `/password/reset-request`

#### Request Body

```json
{
  "email": "user@example.com"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Password reset email sent if account exists"
  }
}
```

---

### Reset Password

Reset password using reset token.

**POST** `/password/reset`

#### Request Body

```json
{
  "token": "reset-token",
  "new_password": "string"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Password reset successfully"
  }
}
```

#### Error Codes

- `INVALID_TOKEN` - Reset token is invalid or expired
- `WEAK_PASSWORD` - New password doesn't meet requirements

---

### Verify Email

Verify email address using verification token.

**POST** `/verify-email`

#### Request Body

```json
{
  "token": "verification-token"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Email verified successfully"
  }
}
```

#### Error Codes

- `INVALID_TOKEN` - Verification token is invalid or expired

---

### Resend Verification Email

Resend email verification.

**POST** `/verify-email/resend`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Verification email sent"
  }
}
```

## Security Features

### Rate Limiting

- Login attempts: 5 per minute per IP
- Password reset requests: 3 per hour per email
- Registration: 10 per hour per IP

### Token Security

- Access tokens expire in 1 hour (3600 seconds)
- Refresh tokens expire in 30 days
- All tokens are JWTs with strong encryption
- Tokens are invalidated on logout

### Password Requirements

- Minimum 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one number
- Cannot contain username or email

### Account Protection

- Account lockout after 5 failed login attempts
- Lockout duration: 15 minutes
- Password history: Cannot reuse last 5 passwords
- Email verification required for new accounts