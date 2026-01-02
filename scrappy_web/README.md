# ScrapPY Web Interface & REST API

This module provides an optional, decoupled REST API and web-based interface for ScrapPY. It is designed with strict adherence to OWASP principles, ensuring security, auditability, and explicit user consent for all operations.

## System Architecture

```ascii
+----------------+       +----------------+       +----------------+
|  Web Browser   | <---> |   REST API     | <---> |   Task Queue   |
| (Read-only UI) | HTTPS | (FastAPI/Auth) |       | (Background)   |
+----------------+       +----------------+       +-------+--------+
                                 |                        |
                                 v                        v
                         +----------------+       +----------------+
                         |  Auth & Audit  |       |   ScrapPY CLI  |
                         |    Database    |       |  (Subprocess)  |
                         +----------------+       +----------------+
```

### Components

1.  **REST API (FastAPI):** The core entry point. Handles authentication, input validation, job scheduling, and result retrieval.
2.  **Web UI (Static HTML/JS):** A lightweight client that consumes the REST API. It does not contain business logic.
3.  **Task Queue:** Manages background execution of ScrapPY scans to prevent blocking the API.
4.  **ScrapPY CLI:** The unmodified core logic, invoked via secure subprocess calls.

## REST API Design

### Endpoints

| Method | Endpoint                       | Description                                                          | Auth Required      |
| :----- | :----------------------------- | :------------------------------------------------------------------- | :----------------- |
| `POST` | `/api/v1/auth/token`           | Obtain access token (OAuth2 Password Flow)                           | No                 |
| `POST` | `/api/v1/jobs`                 | Submit a new scraping job. Requires file upload and explicit config. | Yes (Scope: write) |
| `GET`  | `/api/v1/jobs/{job_id}`        | Get job status and metadata.                                         | Yes (Scope: read)  |
| `GET`  | `/api/v1/jobs/{job_id}/result` | Get job output (wordlist/metadata).                                  | Yes (Scope: read)  |
| `GET`  | `/api/v1/audit/logs`           | Retrieve audit logs for admin review.                                | Yes (Scope: admin) |

### Request/Response Schemas

**Job Submission (POST /api/v1/jobs)**

```json
// Request (Multipart/Form-Data)
{
  "file": (Binary PDF),
  "mode": "word-frequency" | "full" | "metadata" | "entropy",
  "consent_acknowledged": true
}

// Response
{
  "job_id": "uuid-string",
  "status": "queued",
  "created_at": "timestamp"
}
```

## Threat Model

### Assets

- **User Uploaded PDFs:** May contain sensitive data.
- **Generated Wordlists:** Potential attack vectors if leaked.
- **Server Resources:** CPU/RAM used for scraping.

### Risks & Mitigations

| Threat                        | Description                                                            | Mitigation                                                                                                        |
| :---------------------------- | :--------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| **Unauthenticated Access**    | Attacker submits jobs or views results without permission.             | **Strict Auth:** OAuth2 with JWT. No anonymous access.                                                            |
| **DoS via Large Files**       | Attacker uploads massive PDFs to exhaust server memory/disk.           | **Limits:** Max file size (10MB), Max request rate (Rate Limiting).                                               |
| **Command Injection**         | Attacker crafts filenames to execute shell commands.                   | **Sanitization:** Filenames are hashed/randomized on disk. Subprocess calls use list arguments, never shell=True. |
| **Path Traversal**            | Attacker tries to read arbitrary files via job ID manipulation.        | **Validation:** Job IDs are UUIDs. File paths are strictly scoped to a temp directory.                            |
| **SSRF / RCE**                | Exploiting vulnerabilities in PDF parsing libraries.                   | **Isolation:** Parsing happens in a separate process. Input validation on file magic numbers.                     |
| **Misuse / Unintended Scans** | User accidentally scans sensitive docs or scans without authorization. | **Explicit Consent:** API requires `consent_acknowledged` flag. Audit logs track who scanned what and when.       |

## Technology Stack

### Backend

- **Language:** Python 3.9+
- **Framework:** FastAPI (High performance, auto-validation, secure defaults).
- **Security:** `python-jose` (JWT), `passlib` (Hashing), `slowapi` (Rate Limiting).
- **Task Management:** `concurrent.futures` (Simple, no external deps) or `Redis` (Production).

### Frontend

- **Technology:** Vanilla HTML/JS (Fetch API).
- **Design:** Minimalist, functional. No external CDNs (privacy).

## Project Structure

```
scrappy_web/
├── api/
│   ├── __init__.py
│   ├── main.py          # App entry point
│   ├── auth.py          # Authentication logic
│   ├── config.py        # Environment configuration
│   ├── models.py        # Pydantic schemas
│   └── worker.py        # Job execution logic
├── tests/
│   ├── __init__.py
│   └── test_api.py      # API test suite
├── ui/
│   └── index.html       # Single page app
├── .env.example         # Environment template
├── requirements.txt     # Web-specific dependencies
└── README.md            # This file
```

## Usage

### Development

1.  **Install Dependencies:**

    ```bash
    pip install -r scrappy_web/requirements.txt
    ```

2.  **Set Environment Variables:**

    ```bash
    # Generate a secret key
    python -c "import secrets; print(secrets.token_hex(32))"

    # Export it (or create .env file)
    export SCRAPPY_SECRET_KEY="your-generated-key-here"
    ```

3.  **Start Server:**

    ```bash
    uvicorn scrappy_web.api.main:app --reload
    ```

4.  **Access:**
    - **UI:** http://127.0.0.1:8000/ui/
    - **API Docs:** http://127.0.0.1:8000/docs
    - **Credentials:** `admin` / `password123`

### Docker

```bash
# Build
docker build -t scrappy-web .

# Run (set your secret key)
docker run -p 8000:8000 -e SCRAPPY_SECRET_KEY="your-secret-key" scrappy-web

# Or use docker-compose
cp scrappy_web/.env.example .env
# Edit .env and set SCRAPPY_SECRET_KEY
docker-compose up
```

### Running Tests

```bash
SCRAPPY_SECRET_KEY="test-key-minimum-32-chars" pytest scrappy_web/tests/ -v
```

## Configuration

| Environment Variable           | Required | Default   | Description                    |
| ------------------------------ | -------- | --------- | ------------------------------ |
| `SCRAPPY_SECRET_KEY`           | **Yes**  | -         | JWT signing key (min 32 chars) |
| `SCRAPPY_TOKEN_EXPIRE_MINUTES` | No       | 30        | Token expiration time          |
| `SCRAPPY_MAX_FILE_SIZE_MB`     | No       | 10        | Max upload file size           |
| `SCRAPPY_LOGIN_RATE_LIMIT`     | No       | 5/minute  | Login rate limit               |
| `SCRAPPY_JOB_RATE_LIMIT`       | No       | 10/minute | Job submission rate limit      |
