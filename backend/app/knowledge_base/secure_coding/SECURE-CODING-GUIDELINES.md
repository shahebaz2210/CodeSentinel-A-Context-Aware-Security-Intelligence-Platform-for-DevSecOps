# Secure Coding Guidelines

## Input Validation

### Principle
All input from external sources must be validated before use. This includes:
- HTTP request parameters, headers, and body
- Data from files, databases, or external APIs
- Environment variables used at runtime

### Implementation Guidelines

**Whitelist validation (preferred)**
```python
# Allow only expected values
ALLOWED_SCAN_TYPES = {"repo", "pr"}
if scan_type not in ALLOWED_SCAN_TYPES:
    raise ValueError(f"Invalid scan type: {scan_type}")
```

**Type enforcement**
```python
# Use Pydantic for automatic validation
from pydantic import BaseModel, validator

class ScanRequest(BaseModel):
    repo_id: str
    scan_type: Literal["repo", "pr"]
    pr_number: Optional[int] = None
```

**Size limits**
- Limit request body size at the web server level
- Apply field-level length constraints in schemas
- Reject files or payloads exceeding size thresholds

---

## Authentication & Authorization

### Session Management
- Use short-lived tokens (max 1 hour) with refresh token rotation
- Invalidate tokens server-side on logout
- Use httpOnly, Secure, SameSite=Strict cookies for web sessions
- Never store secrets in localStorage for sensitive production apps

### OAuth Security
- Validate state parameter in OAuth callbacks to prevent CSRF
- Exchange authorization codes server-side only
- Store tokens encrypted at rest using a secrets manager

### API Authorization
- Check permissions on every API handler, not just at routing layer
- Return 403 (Forbidden) vs 404 (Not Found) carefully — use 404 for resource not found to avoid enumeration
- Log failed authorization attempts

---

## Secrets Management


```python
# BAD — never do this
OPENAI_API_KEY = "sk-proj-abc123..."
DATABASE_URL = "postgresql://user:password@host/db"

# GOOD — always from environment
import os
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
```

### Environment Variables
- Use `.env` files locally only — never commit them
- In production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager)
- Rotate secrets regularly and on personnel changes

---

## Cryptography

### Hashing
```python
# For passwords — use bcrypt, scrypt, or argon2
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(plaintext_password)

# Never use MD5 or SHA1 for passwords
# import hashlib; hashlib.md5(password).hexdigest()  # BAD
```

### Random Values
```python
# For security-sensitive tokens
import secrets
token = secrets.token_urlsafe(32)  # Good

# Never use random.random() for security
import random; random.random()  # BAD for security
```

---

## SQL Security

### Parameterized Queries
```python
# Always use parameterized queries — never f-strings in SQL
# BAD:
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD (SQLAlchemy ORM):
user = db.query(User).filter(User.id == user_id).first()

# GOOD (raw SQL with parameters):
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

---

## HTTP Security Headers

All API responses should include:
```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=63072000; includeSubDomains
```

---

## Logging Security

```python
# GOOD — log the event, not the sensitive data
logger.info("Authentication failed", username_length=len(username))

# BAD — never log credentials, tokens, or PII
logger.info("Login attempt", password=password)  # NEVER DO THIS
logger.info("Token issued", token=access_token)  # NEVER DO THIS
```

### Structured Logging
- Use structured logging (JSON format) for machine-parseable audit trails
- Include: timestamp, user_id (not username), IP, action, result
- Ensure logs are forwarded to a SIEM for security monitoring

---

## Dependency Management

- Maintain a dependency lock file (`requirements.lock` or `poetry.lock`)
- Run `pip audit` or `safety check` in CI to detect known CVEs
- Keep all dependencies updated, especially security-critical ones
- Use minimal dependencies — prefer stdlib over third-party when feasible
- Review transitive dependencies — a vulnerable sub-dependency is still a vulnerability

---

## Error Handling

```python
# Good — generic error for external callers
@app.exception_handler(Exception)
async def generic_handler(request, exc):
    # Log the full error internally
    logger.error("Unhandled exception", exc_info=exc)
    # Return a generic message externally — never stack traces
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

Never expose:
- Stack traces to end users
- Database query details
- Internal file paths
- Library versions in error messages

---

## Container Security

- Run containers as non-root users
- Use read-only root filesystems where possible
- Apply resource limits (CPU, memory)
- Scan container images for CVEs using Trivy or Grype
- Never include secrets in Docker images — use runtime injection
