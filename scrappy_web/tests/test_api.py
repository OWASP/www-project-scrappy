import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import sys

# Set test environment variables before importing app
os.environ["SCRAPPY_SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"

from scrappy_web.api.main import app, limiter
from scrappy_web.api.models import JobStatus

# Disable rate limiting for tests
limiter.enabled = False

client = TestClient(app)


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Valid credentials return access token"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_password(self):
        """Invalid password returns 401"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_username(self):
        """Invalid username returns 401"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "notauser", "password": "password123"}
        )
        assert response.status_code == 401


class TestJobCreation:
    """Job submission endpoint tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get valid auth headers"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "password123"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a minimal valid PDF for testing"""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF'
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(pdf_content)
        return pdf_file
    
    def test_job_requires_auth(self):
        """Job creation without auth returns 401"""
        response = client.post(
            "/api/v1/jobs",
            data={"mode": "full", "consent_acknowledged": "true"},
            files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
        )
        assert response.status_code == 401
    
    def test_job_requires_consent(self, auth_headers, sample_pdf):
        """Job creation without consent returns 400"""
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/api/v1/jobs",
                headers=auth_headers,
                data={"mode": "full", "consent_acknowledged": "false"},
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        assert response.status_code == 400
        assert "consent" in response.json()["detail"].lower()
    
    def test_job_rejects_non_pdf(self, auth_headers):
        """Non-PDF files are rejected"""
        response = client.post(
            "/api/v1/jobs",
            headers=auth_headers,
            data={"mode": "full", "consent_acknowledged": "true"},
            files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]
    
    def test_job_validates_pdf_magic_bytes(self, auth_headers):
        """Files with PDF content-type but wrong magic bytes are rejected"""
        response = client.post(
            "/api/v1/jobs",
            headers=auth_headers,
            data={"mode": "full", "consent_acknowledged": "true"},
            files={"file": ("fake.pdf", b"not a real pdf", "application/pdf")}
        )
        assert response.status_code == 400
        assert "Invalid PDF" in response.json()["detail"]


class TestJobRetrieval:
    """Job status and result retrieval tests"""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "password123"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_nonexistent_job(self, auth_headers):
        """Requesting non-existent job returns 404"""
        response = client.get(
            "/api/v1/jobs/nonexistent-job-id",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_get_result_nonexistent_job(self, auth_headers):
        """Requesting result for non-existent job returns 404"""
        response = client.get(
            "/api/v1/jobs/nonexistent-job-id/result",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestRootEndpoint:
    """Root endpoint tests"""
    
    def test_root_redirects_to_ui(self):
        """Root endpoint redirects to UI"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/"


class TestConfig:
    """Configuration validation tests"""
    
    def test_config_loads(self):
        """Config module loads without error"""
        from scrappy_web.api.config import settings
        assert settings.MAX_FILE_SIZE_MB > 0
        assert settings.ALGORITHM == "HS256"
    
    def test_allowed_content_types(self):
        """Only PDF content type is allowed"""
        from scrappy_web.api.config import settings
        assert "application/pdf" in settings.ALLOWED_CONTENT_TYPES
        assert len(settings.ALLOWED_CONTENT_TYPES) == 1
