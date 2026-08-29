# CWE Common Weakness Enumeration — Security Knowledge Base

## CWE-89: SQL Injection
SQL injection occurs when user-supplied input is not properly sanitized and is included in SQL queries.

**Severity:** Critical
**OWASP:** A03:2021 - Injection

### Prevention
- Use parameterized queries (prepared statements) for all database access
- Use stored procedures that do not have dynamic SQL generation
- Use an allow-list input validation
- Escape all user-supplied input using the escaping syntax specific to the database

---

## CWE-79: Cross-Site Scripting (XSS)
XSS flaws occur when an application includes untrusted data in a web page without proper validation or escaping.

**Severity:** High  
**OWASP:** A03:2021 - Injection

### Types
- Reflected XSS: Injected script is reflected off the web server
- Stored XSS: Injected script is permanently stored on the target server
- DOM-based XSS: Client-side script writes attacker-controllable data to the DOM

### Prevention
- Never insert untrusted data except in allowed locations
- HTML encode data before putting it into HTML element content
- Attribute encode data before putting it into HTML common attributes
- Use HTTPOnly cookie flag
- Implement Content Security Policy (CSP)

---

## CWE-352: Cross-Site Request Forgery (CSRF)
CSRF is an attack that tricks the victim into submitting a malicious request.

**Prevention:**
- Use anti-CSRF tokens
- SameSite cookie attribute
- Verify Origin header

---

## CWE-327: Use of Broken or Risky Cryptographic Algorithm
Using weak cryptographic algorithms like MD5, SHA1, DES, RC4.

**Severity:** Medium-High

### Secure Alternatives
- For hashing: SHA-256, SHA-3, BLAKE2
- For passwords: bcrypt, scrypt, Argon2, PBKDF2
- For symmetric encryption: AES-256-GCM
- For asymmetric: RSA-2048+, ECDSA P-256+

---

## CWE-798: Use of Hard-coded Credentials
Authentication credentials are stored directly in code.

**Severity:** Critical

### Prevention
- Store credentials in environment variables or secrets management systems
- Use service accounts with minimal required privileges
- Rotate credentials regularly
- Never commit secrets to version control

---

## CWE-918: Server-Side Request Forgery (SSRF)
Server-side request forgery allows attackers to make the server-side application make HTTP requests to an arbitrary domain.

**OWASP:** A10:2021

### Prevention
- Validate and sanitize all client-supplied input used in server-side HTTP requests
- Use an allow-list for accessible URLs/IPs
- Block access to internal/metadata endpoints (169.254.169.254, etc.)
- Disable HTTP redirections or validate after redirection

---

## CWE-502: Deserialization of Untrusted Data
Deserialization of untrusted data can lead to remote code execution.

**Severity:** Critical

### Prevention
- Do not deserialize data from untrusted sources
- Use digital signatures to ensure deserialization only happens on trusted data
- Use language-safe serialization formats (JSON instead of pickle)
- Enforce strict type constraints during deserialization

---

## CWE-200: Exposure of Sensitive Information
Sending sensitive information to an unauthorized actor.

**Prevention:**
- Use secure error handling that does not expose stack traces
- Implement proper access controls
- Log sensitive operations without exposing data in logs

---

## CWE-287: Improper Authentication
When software does not properly authenticate users, it can allow attackers to gain access.

**Prevention:**
- Implement multi-factor authentication
- Use strong session management
- Implement brute-force protection
- Validate all authentication tokens server-side

---

## CWE-611: XML External Entity (XXE) Injection
Processing XML input that contains a reference to an external entity.

**Prevention:**
- Disable XML external entity and DTD processing in all XML parsers
- Implement positive server-side input validation
- Upgrade XML processors and libraries
- Use SAST tools to detect XXE in source code

---

## CWE-22: Path Traversal
Path traversal allows attackers to access files outside the intended directory.

**Prevention:**
- Validate user input before using it in file path operations
- Use absolute paths and canonical path resolution
- Maintain a whitelist of allowed files or directories

---

## CWE-732: Incorrect Permission Assignment for Critical Resource
Incorrect permissions can allow unauthorized access to critical files or directories.

**Prevention:**
- Apply least privilege principle
- Verify permissions of all critical resources
- Use operating system-level access controls
