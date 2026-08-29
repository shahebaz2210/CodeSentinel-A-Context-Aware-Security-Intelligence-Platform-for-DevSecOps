# OWASP Top 10 Security Knowledge Base

## A01:2021 - Broken Access Control
CWE: CWE-200, CWE-201, CWE-352

Broken access control is the most critical web application security risk.
Restrictions on what authenticated users are allowed to do are often not properly enforced.
Attackers can exploit these flaws to access unauthorized functionality and/or data.

### Common Vulnerabilities
- Violation of the principle of least privilege or deny by default
- Bypassing access control checks by modifying the URL
- Accessing another user's account by modifying the primary key
- Accessing API with missing access controls for POST, PUT, DELETE
- Elevation of privilege by acting as a user without being logged in
- Metadata manipulation (JWT manipulation, cookie tampering)
- CORS misconfiguration allowing access from unauthorized origins
- Force browsing to authenticated pages as unauthenticated user

### Prevention
- Deny by default, except for public resources
- Implement access control mechanisms once and reuse throughout the application
- Model access controls should enforce record ownership
- Rate limit API and controller access to minimize harm from automated attack tools
- Log access control failures, alert admins when appropriate
- Invalidate stateful session identifiers after logout
- JWT tokens should be short-lived

---

## A02:2021 - Cryptographic Failures
CWE: CWE-261, CWE-296, CWE-310, CWE-319, CWE-321, CWE-326, CWE-327, CWE-328, CWE-329

Cryptographic failures occur when sensitive data is not adequately protected.
This includes data in transit and at rest. Failures often lead to exposure of sensitive data.

### Common Vulnerabilities
- Data transmitted in cleartext (HTTP, SMTP, FTP)
- Old or weak cryptographic algorithms still in use (MD5, SHA1, DES, RC4)
- Default crypto keys in use, weak crypto keys generated
- Encryption not enforced (missing HTTP security headers)
- Server certificate not validated properly
- IV/nonce reused, or is not random enough for cryptographic mode used
- Password stored without hashing or using weak hashing algorithms
- Deprecated hash functions (MD5, SHA1) used for password storage

### Prevention
- Classify data processed, stored, or transmitted — identify which is sensitive
- Don't store sensitive data unnecessarily
- Encrypt all sensitive data at rest using strong, standard algorithms
- Ensure up-to-date and strong standard algorithms, protocols, and keys
- Encrypt all data in transit with secure protocols (TLS with PFS ciphers)
- Disable caching for responses that contain sensitive data
- Store passwords using strong adaptive and salted hashing functions (Argon2, scrypt, bcrypt, PBKDF2)
- Always use authenticated encryption instead of just encryption
- Keys should be generated cryptographically randomly and stored in memory as byte arrays

---

## A03:2021 - Injection
CWE: CWE-77, CWE-89, CWE-564

Injection flaws occur when untrusted data is sent to an interpreter as part of a command or query.

### SQL Injection (CWE-89)
SQL injection allows attackers to interfere with database queries.
This can allow viewing data that's normally not retrievable, including other users' data.

**Vulnerable example:**
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
```

**Secure fix:**
```python
# Use parameterized queries / prepared statements
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

### Command Injection (CWE-77)
Command injection allows attackers to execute arbitrary OS commands.

**Prevention:**
- Use parameterized queries for database access
- Use safe APIs that avoid using the interpreter entirely
- Validate input server-side using a whitelist
- Escape special characters using the specific escape syntax for that interpreter
- Use LIMIT and other SQL controls within queries to prevent mass disclosure

---

## A04:2021 - Insecure Design
CWE: CWE-73

Insecure design is a broad category representing different weaknesses.
"Insecure design is not the source of all other Top 10 risk categories."

Prevention includes threat modeling, secure design patterns, and reference architectures.

---

## A05:2021 - Security Misconfiguration
CWE: CWE-16

Missing appropriate security hardening, improperly configured permissions on cloud services,
unnecessary features enabled, default accounts with unchanged passwords.

### Prevention
- Repeatable hardening processes to deploy environments consistently
- Minimal platform (remove unnecessary features, components, docs, samples)
- Review and update configurations as part of patch management
- Segmented application architecture providing effective separation
- Send security directives to clients (security headers)
- Automated process to verify configurations in all environments

---

## A06:2021 - Vulnerable and Outdated Components
CWE: CWE-937, CWE-1035

Using components with known vulnerabilities enables attackers to exploit the vulnerability.

### Prevention
- Remove unused dependencies, features, components, files, documentation
- Continuously inventory versions of client-side and server-side components
- Monitor CVE databases for vulnerabilities in components
- Only obtain components from official sources over secure links
- Monitor for libraries and components unmaintained or not creating security patches

---

## A07:2021 - Identification and Authentication Failures
CWE: CWE-287, CWE-384

Confirmation of user's identity, authentication, and session management is critical.

### Prevention
- Implement multi-factor authentication where possible
- Do not ship or deploy with any default credentials
- Implement weak password checks (NIST 800-63b password requirements)
- Align password length, complexity, and rotation policies with NIST 800-63b
- Ensure registration, credential recovery, and API pathways are hardened against account enumeration
- Limit or increasingly delay failed login attempts — log all failures and alert administrators
- Use a server-side, secure, built-in session manager that generates a new random session ID after login

---

## A08:2021 - Software and Data Integrity Failures
CWE: CWE-502, CWE-829

Software and data integrity failures relate to code and infrastructure that does not protect
against integrity violations.

### Prevention
- Use digital signatures or similar mechanisms to verify the software or data is from the expected source
- Ensure libraries and dependencies are consuming trusted repositories
- Ensure there is a review process for code and configuration changes to minimize chance of malicious code
- Ensure CI/CD pipeline has proper segregation, configuration, and access control
- Ensure unsigned or unencrypted serialized data is not sent to untrusted clients

---

## A09:2021 - Security Logging and Monitoring Failures
CWE: CWE-778

Without logging and monitoring, breaches cannot be detected.

### Prevention
- Ensure all login, access control, and server-side input validation failures can be logged with sufficient context
- Ensure that logs are generated in a format that log management solutions can easily consume
- Ensure log data is encoded correctly to prevent injection
- Ensure high-value transactions have an audit trail with integrity controls
- Establish or adopt an incident response and recovery plan

---

## A10:2021 - Server-Side Request Forgery (SSRF)
CWE: CWE-918

SSRF flaws occur when a web application fetches a remote resource without validating the user-supplied URL.

### Prevention
**Network Layer:**
- Segment remote resource access functionality in separate networks
- Enforce "deny by default" firewall policies or network access control rules
- Use a firewall, VPN, or network ACL to block all but essential intranet traffic

**Application Layer:**
- Sanitize and validate all client-supplied input data
- Enforce the URL schema, port, and destination with a positive allow list
- Do not send raw responses to clients
- Disable HTTP redirections
