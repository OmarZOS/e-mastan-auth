# **Emastan** 🔐
### *The Guardian — Authentication Service*

---

## 📖 **Overview**

**Emastan** (ⴰⵎⴰⵙⵜⴰⵏ) — meaning "The Protector" in Tamazight — is a robust, secure authentication service built with **FastAPI**. It safeguards your Verdelia ecosystem with enterprise-grade user management, role-based access control, and token-based authentication.

---

## ✨ **Core Features**

| Feature | Description |
|---------|-------------|
| **User Registration** | Secure sign-up with validation and email verification |
| **Authentication** | OAuth2-compliant login with JWT token generation |
| **Password Management** | Secure password change with current password verification |
| **Token Lifecycle** | Access token generation, validation, and refresh |
| **Role-Based Access** | Granular permission control with user roles |
| **Audit Logging** | Track logins, failures, and security events |
| **Account Security** | Lockout after failed attempts, MFA ready |

---

## 🗄️ **Database Architecture**

**Emastan** uses **SQLite** for data persistence, balancing security with simplicity.

```
┌─────────────────────────────────────────┐
│            Emastan Database              │
├─────────────────────────────────────────┤
│  Users                                  │
│  ├── Credentials (hashed passwords)     │
│  ├── Profile Information                │
│  ├── Roles & Permissions                │
│  └── Security Metadata                  │
├─────────────────────────────────────────┤
│  Sessions                               │
│  └── Active token tracking              │
├─────────────────────────────────────────┤
│  Audit Logs                             │
│  └── Authentication events              │
└─────────────────────────────────────────┘
```

---

## 🔌 **API Endpoints**

### 1. 👤 **User Registration**
Create a new user account.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/` | Register a new user |

**Request Body:**
```json
{
    "username": "string",          // Required
    "email": "string",              // Required, valid email
    "phone_number": "string",       // Optional
    "password": "string",           // Required, min 8 chars
    "first_name": "string",         // Optional
    "last_name": "string",          // Optional
    "date_of_birth": "string",      // Optional (YYYY-MM-DD)
    "gender": "string",             // Optional
    "profile_picture": "binary",    // Optional
    "roles": "string",              // Optional (default: 'user')
    "last_login": "string",         // System-managed
    "login_count": "integer",       // System-managed
    "failed_login_attempts": "integer", // System-managed
    "account_locked": "boolean",    // System-managed
    "mfa_enabled": "boolean"        // System-managed
}
```

**Response (201 Created):**
```json
{
    "id_app_user": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "phone_number": "+213551234567",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "profile_picture": null,
    "roles": "user",
    "last_login": null,
    "login_count": 0,
    "failed_login_attempts": 0,
    "account_locked": false,
    "mfa_enabled": false,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
    "deleted_at": null
}
```

---

### 2. 🔑 **User Login**
Authenticate a user and obtain access token.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/token` | Login and get JWT token |

**Request Body:**
```json
{
    "username": "johndoe",
    "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

**Error Responses:**
| Status | Description |
|--------|-------------|
| `401` | Invalid credentials |
| `423` | Account locked (too many failed attempts) |

---

### 3. 🔒 **Password Change**
Update user password securely.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/change-password/` | Change user password |

**Request Body:**
```json
{
    "username": "johndoe",
    "current_password": "CurrentPass123!",
    "new_password": "NewSecurePass456!"
}
```

**Response (200 OK):**
```json
{
    "message": "Password updated successfully",
    "timestamp": "2026-01-01T00:00:00"
}
```

---

## 🛡️ **Security Architecture**

### Authentication Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Emastan   │────▶│   Token     │
│  (Mobile/   │     │   (Auth)    │     │  (JWT)      │
│   Web)      │◀────│             │◀────│             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   SQLite    │
                    │  Database   │
                    └─────────────┘
```

### Security Measures

| Layer | Protection |
|-------|------------|
| **Password Storage** | 🔐 Argon2 / bcrypt hashing |
| **Token Security** | 🔑 JWT with RSA signing |
| **Transport** | 🔒 TLS/SSL encryption (HTTPS) |
| **Brute Force** | 🛡️ Rate limiting & account lockout |
| **Audit** | 📝 Comprehensive logging |
| **MFA Ready** | 📱 Extensible for 2FA |

---

## 📡 **SSL/TLS Configuration**

Generate certificates for secure HTTPS communication:

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout certificates/key.pem \
  -out certificates/cert.pem \
  -config cert.cnf
```

---

## 🚀 **Deployment**

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/verdelia/Emastan.git
cd Emastan

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python scripts/init_db.py

# 6. Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build the image
docker build -t verdelia/Emastan:latest .

# Run the container
docker run -d \
  --name Emastan \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///app/data/users.db \
  -e SECRET_KEY=your-secret-key \
  -v ./data:/app/data \
  verdelia/Emastan:latest
```

### Production (Docker Compose)

```yaml
# docker-compose.yml
services:
  Emastan:
    image: verdelia/Emastan:latest
    container_name: Emastan
    environment:
      - DATABASE_URL=sqlite:///app/data/users.db
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=60
    volumes:
      - ./data:/app/data
      - ./certificates:/app/certificates
    ports:
      - "8443:8443"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🔧 **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./users.db` |
| `SECRET_KEY` | JWT signing key | *(required)* |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity (minutes) | `60` |
| `MAX_LOGIN_ATTEMPTS` | Failed attempts before lockout | `5` |
| `LOCKOUT_DURATION_MINUTES` | Account lockout duration | `15` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` |

---

## 📦 **Project Structure**

```
Emastan/
├── app/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   ├── models/
│   │   ├── user.py             # User model
│   │   └── token.py            # Token model
│   ├── schemas/
│   │   ├── user.py             # Pydantic schemas
│   │   └── token.py            # Token schemas
│   ├── routes/
│   │   ├── auth.py             # Authentication endpoints
│   │   └── users.py            # User management endpoints
│   ├── services/
│   │   ├── auth_service.py     # Authentication logic
│   │   └── user_service.py     # User management logic
│   ├── security/
│   │   ├── hashing.py          # Password hashing
│   │   └── jwt.py              # JWT handling
│   └── utils/
│       ├── validators.py       # Input validation
│       └── logger.py           # Logging configuration
├── certificates/
│   ├── key.pem                 # Private key
│   └── cert.pem                # Certificate
├── scripts/
│   ├── init_db.py              # Database initialization
│   └── seed_data.py            # Seed test data
├── tests/                      # Unit tests
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Multi-container setup
└── README.md                   # This file
```

---

## 📊 **API Response Codes**

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `423` | Locked |
| `500` | Internal Server Error |

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_auth.py -v
```

---

## 🔗 **Service Integration**

### As Part of Verdelia Ecosystem

```
┌─────────────────────────────────────────────────────────┐
│                    VERDELIA PLATFORM                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              🔐 A M A S T A N                   │   │
│  │              Authentication Service             │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                 │
│         ┌─────────────┼─────────────┐                  │
│         │             │             │                  │
│    ┌────▼────┐  ┌─────▼─────┐  ┌────▼────┐          │
│    │ Verde   │  │  Verde    │  │  Verde  │          │
│    │ Vault   │  │  Flow     │  │  Core   │          │
│    │(File)   │  │ (Stream)  │  │(Commerce)│          │
│    └─────────┘  └───────────┘  └─────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Integration Example:**

```python
# Client using Emastan
import requests

# Login
response = requests.post(
    "https://Emastan.verdelia.com/token",
    json={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

# Access protected service
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://verdeflow.verdelia.com/stream",
    headers=headers
)
```

---

## 📚 **Dependencies**

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.100.0 | Web framework |
| `uvicorn` | >=0.23.0 | ASGI server |
| `python-jose` | >=3.3.0 | JWT handling |
| `passlib` | >=1.7.4 | Password hashing |
| `python-multipart` | >=0.0.6 | Form data parsing |
| `sqlalchemy` | >=2.0.0 | ORM |
| `pydantic` | >=2.0.0 | Data validation |
| `email-validator` | >=2.0.0 | Email validation |
| `python-dotenv` | >=1.0.0 | Environment variables |
| `bcrypt` | >=4.0.0 | Password hashing |

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 **License**

This project is proprietary — © Verdelia. All rights reserved.

---

## 🌟 **Acknowledgments**

- Built with ❤️ for the Verdelia ecosystem
- Inspired by the Amazigh concept of **Emastan** — "The Guardian"
- Securing the future of Algerian commerce

---

**Emastan — The Guardian of Verdelia** 🔐