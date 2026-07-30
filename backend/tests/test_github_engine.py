"""Comprehensive tests for the GitHub Integration & Automation Engine."""
import json
import hashlib
import hmac
import pytest
from unittest.mock import MagicMock, patch
from app.engines.github_engine.security import (
    encrypt_token, decrypt_token, verify_webhook_signature,
)
from app.engines.github_engine.job_queue import JobQueue
from app.engines.github_engine.pipeline import (
    run_push_pipeline, _run_step, PIPELINE_STEPS,
)
from app.engines.github_engine.pr_analysis import run_pr_analysis
from app.engines.github_engine.webhook_handler import WebhookHandler, SUPPORTED_EVENTS
from app.engines.github_engine.github_service import GitHubService


# ==================================================================
# Security
# ==================================================================

class TestSecurity:

    def test_encrypt_decrypt(self):
        token = "ghp_testtoken12345"
        enc = encrypt_token(token)
        assert enc != token
        assert decrypt_token(enc) == token

    def test_encrypt_different_outputs(self):
        enc1 = encrypt_token("a")
        enc2 = encrypt_token("a")
        # Fernet produces different ciphertexts each time
        assert enc1 != enc2
        assert decrypt_token(enc1) == "a"
        assert decrypt_token(enc2) == "a"

    def test_verify_signature_valid(self):
        body = b'{"test": true}'
        secret = "mysecret"
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert verify_webhook_signature(body, sig, secret) is True

    def test_verify_signature_invalid(self):
        assert verify_webhook_signature(b"body", "sha256=wrong", "secret") is False

    def test_verify_signature_no_prefix(self):
        assert verify_webhook_signature(b"body", "nope", "secret") is False

    def test_verify_signature_empty(self):
        assert verify_webhook_signature(b"body", "", "secret") is False


# ==================================================================
# JobQueue
# ==================================================================

class TestJobQueue:

    @pytest.fixture
    def queue(self):
        db = MagicMock()
        with patch("app.engines.github_engine.job_queue.GitHubRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            q = JobQueue.__new__(JobQueue)
            q.db = db
            q.gh_repo = mock_repo
            q._handlers = {}
            return q

    def test_register_handler(self, queue):
        fn = lambda db, job: {"ok": True}
        queue.register_handler("test", fn)
        assert "test" in queue.handlers

    def test_enqueue(self, queue):
        job = MagicMock()
        job.id = 42
        queue.gh_repo.create_job.return_value = job
        jid = queue.enqueue("push_pipeline", connected_repo_id=1)
        assert jid == 42

    def test_process_job_not_found(self, queue):
        queue.gh_repo.get_job.return_value = None
        result = queue.process_job(1)
        assert result["status"] == "error"

    def test_process_job_no_handler(self, queue):
        job = MagicMock()
        job.job_type = "unknown"
        queue.gh_repo.get_job.return_value = job
        result = queue.process_job(1)
        assert result["status"] == "error"

    def test_process_job_success(self, queue):
        job = MagicMock()
        job.id = 1
        job.job_type = "test"
        job.attempt = 0
        job.max_retries = 3
        queue.gh_repo.get_job.return_value = job
        queue.register_handler("test", lambda db, j: {"done": True})
        result = queue.process_job(1)
        assert result["status"] == "completed"

    def test_process_job_retry(self, queue):
        job = MagicMock()
        job.id = 1
        job.job_type = "test"
        job.attempt = 0
        job.max_retries = 3
        queue.gh_repo.get_job.return_value = job
        queue.register_handler("test", lambda db, j: (_ for _ in ()).throw(ValueError("oops")))
        result = queue.process_job(1)
        assert result["status"] == "retry"

    def test_process_job_failed(self, queue):
        job = MagicMock()
        job.id = 1
        job.job_type = "test"
        job.attempt = 3
        job.max_retries = 3
        queue.gh_repo.get_job.return_value = job
        queue.register_handler("test", lambda db, j: (_ for _ in ()).throw(ValueError("fail")))
        result = queue.process_job(1)
        assert result["status"] == "failed"

    def test_get_job_status(self, queue):
        job = MagicMock()
        job.id = 1
        job.job_type = "test"
        job.status = "completed"
        job.attempt = 1
        job.max_retries = 3
        job.duration_seconds = 0.5
        job.error_message = None
        job.result = {}
        queue.gh_repo.get_job.return_value = job
        s = queue.get_job_status(1)
        assert s["status"] == "completed"

    def test_get_job_status_none(self, queue):
        queue.gh_repo.get_job.return_value = None
        assert queue.get_job_status(999) is None

    def test_retry_failed_jobs(self, queue):
        job = MagicMock()
        job.id = 1
        job.job_type = "test"
        job.attempt = 0
        job.max_retries = 3
        job.connected_repository_id = 1
        queue.gh_repo.get_queued_jobs.return_value = [job]
        queue.gh_repo.get_job.return_value = job
        queue.register_handler("test", lambda db, j: {"ok": True})
        count = queue.retry_failed_jobs()
        assert count >= 1


# ==================================================================
# Pipeline
# ==================================================================

class TestPipeline:

    def test_run_step_success(self):
        result = _run_step("test", lambda: {"ok": True})
        assert result["status"] == "completed"

    def test_run_step_failure(self):
        def bad():
            raise ValueError("boom")
        result = _run_step("test", bad)
        assert result["status"] == "failed"
        assert "boom" in result["error"]

    def test_pipeline_steps_constant(self):
        assert "incremental_parsing" in PIPELINE_STEPS
        assert "impact_analysis" in PIPELINE_STEPS
        assert len(PIPELINE_STEPS) == 7


# ==================================================================
# PR Analysis
# ==================================================================

class TestPRAnalysis:

    def test_run_pr_analysis(self):
        db = MagicMock()
        job = MagicMock()
        job.connected_repository_id = 1
        job.metadata_ = {
            "repository_id": 1,
            "pr_number": 42,
            "pr_title": "Add feature",
            "pr_author": "dev",
            "head_branch": "feature",
            "base_branch": "main",
            "head_sha": "abc123",
            "changed_files": ["main.py", "app/api/route.py"],
        }
        cr = MagicMock()
        cr.repository_id = 1

        with patch("app.engines.github_engine.pr_analysis.GitHubRepository") as MockGH:
            mock_gh = MockGH.return_value
            mock_gh.get_connected_repo.return_value = cr
            pra = MagicMock()
            pra.id = 10
            mock_gh.create_pr_analysis.return_value = pra

            result = run_pr_analysis(db, job)
            assert result["pr_number"] == 42
            assert result["pr_analysis_id"] == 10
            assert result["risk_level"] in ("low", "medium", "high", "critical")

    def test_pr_analysis_breaking_changes(self):
        db = MagicMock()
        job = MagicMock()
        job.connected_repository_id = 1
        job.metadata_ = {
            "repository_id": None,
            "pr_number": 1,
            "pr_title": "API change",
            "pr_author": "dev",
            "head_branch": "feat",
            "base_branch": "main",
            "head_sha": "xyz",
            "changed_files": ["app/api/users.py", "app/schema/v2.proto"],
        }

        with patch("app.engines.github_engine.pr_analysis.GitHubRepository") as MockGH:
            mock_gh = MockGH.return_value
            mock_gh.get_connected_repo.return_value = None
            pra = MagicMock()
            pra.id = 1
            mock_gh.create_pr_analysis.return_value = pra

            result = run_pr_analysis(db, job)
            call_kwargs = mock_gh.create_pr_analysis.call_args[1]
            breaking = call_kwargs.get("breaking_changes", [])
            assert len(breaking) >= 1


# ==================================================================
# WebhookHandler
# ==================================================================

class TestWebhookHandler:

    @pytest.fixture
    def handler(self):
        db = MagicMock()
        with patch("app.engines.github_engine.webhook_handler.GitHubRepository") as MockGH, \
             patch("app.engines.github_engine.webhook_handler.JobQueue") as MockJQ:
            mock_gh = MockGH.return_value
            mock_jq = MockJQ.return_value
            h = WebhookHandler.__new__(WebhookHandler)
            h.db = db
            h.gh_repo = mock_gh
            h.job_queue = mock_jq
            h._register_handlers()
            return h

    def test_supported_events(self):
        assert "push" in SUPPORTED_EVENTS
        assert "pull_request" in SUPPORTED_EVENTS
        assert "ping" in SUPPORTED_EVENTS
        assert len(SUPPORTED_EVENTS) == 9

    def test_handle_ping(self, handler):
        handler.gh_repo.get_connected_repo_by_full_name.return_value = None
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("ping", "d1", {"zen": "hi"})
        assert result["status"] == "pong"

    def test_handle_unsupported(self, handler):
        handler.gh_repo.get_connected_repo_by_full_name.return_value = None
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("fork", "d2", {"repository": {"full_name": "x/y"}})
        assert result["status"] == "ignored"

    def test_handle_push(self, handler):
        cr = MagicMock()
        cr.id = 1
        cr.repository_id = 1
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        ev.id = 1
        handler.gh_repo.create_webhook_event.return_value = ev
        handler.job_queue.enqueue.return_value = 5

        result = handler.handle_webhook("push", "d3", {
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "ref": "refs/heads/main",
            "after": "abc",
            "commits": [{"added": ["a.py"], "modified": ["b.py"], "removed": []}],
        })
        assert result["status"] == "queued"
        assert result["job_id"] == 5

    def test_handle_pr(self, handler):
        cr = MagicMock()
        cr.id = 1
        cr.repository_id = 1
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        ev.id = 1
        handler.gh_repo.create_webhook_event.return_value = ev
        handler.job_queue.enqueue.return_value = 6

        result = handler.handle_webhook("pull_request", "d4", {
            "action": "opened",
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "pull_request": {
                "number": 42,
                "title": "Feature",
                "user": {"login": "dev"},
                "head": {"ref": "feat", "sha": "abc"},
                "base": {"ref": "main"},
                "changed_files": 3,
            },
        })
        assert result["status"] == "queued"

    def test_handle_pr_closed_skip(self, handler):
        cr = MagicMock()
        cr.id = 1
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev

        result = handler.handle_webhook("pull_request", "d5", {
            "action": "closed",
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "pull_request": {"number": 1},
        })
        assert result["status"] == "processed"

    def test_handle_repo_not_connected(self, handler):
        handler.gh_repo.get_connected_repo_by_full_name.return_value = None
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("push", "d6", {
            "repository": {"full_name": "x/y"},
            "sender": {"login": "dev"},
            "commits": [],
        })
        assert result["status"] == "skipped"

    def test_handle_create_event(self, handler):
        cr = MagicMock()
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("create", "d7", {
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "ref_type": "branch",
            "ref": "feature-x",
        })
        assert result["status"] == "processed"

    def test_handle_release_event(self, handler):
        cr = MagicMock()
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("release", "d8", {
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "release": {"tag_name": "v1.0"},
        })
        assert result["status"] == "processed"

    def test_handle_installation_event(self, handler):
        cr = MagicMock()
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("installation", "d9", {
            "action": "created",
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
            "installation": {"id": 999},
        })
        assert result["status"] == "processed"

    def test_handle_repository_event(self, handler):
        cr = MagicMock()
        cr.full_name = "org/repo"
        cr.webhook_secret = None
        handler.gh_repo.get_connected_repo_by_full_name.return_value = cr
        ev = MagicMock()
        handler.gh_repo.create_webhook_event.return_value = ev
        result = handler.handle_webhook("repository", "d10", {
            "action": "created",
            "repository": {"full_name": "org/repo"},
            "sender": {"login": "dev"},
        })
        assert result["status"] == "processed"


# ==================================================================
# GitHubService
# ==================================================================

class TestGitHubService:

    @pytest.fixture
    def service(self):
        db = MagicMock()
        with patch("app.engines.github_engine.github_service.GitHubRepository") as MockGH, \
             patch("app.engines.github_engine.github_service.JobQueue") as MockJQ:
            mock_gh = MockGH.return_value
            mock_jq = MockJQ.return_value
            svc = GitHubService.__new__(GitHubService)
            svc.db = db
            svc.gh_repo = mock_gh
            svc.job_queue = mock_jq
            return svc

    def test_register_account_create(self, service):
        service.gh_repo.get_account_by_user.return_value = None
        acct = MagicMock()
        acct.id = 1
        service.gh_repo.create_account.return_value = acct
        r = service.register_account(1, 100, "dev", "token123")
        assert r["status"] == "created"

    def test_register_account_update(self, service):
        existing = MagicMock()
        existing.id = 1
        service.gh_repo.get_account_by_user.return_value = existing
        r = service.register_account(1, 100, "dev", "token123")
        assert r["status"] == "updated"

    def test_connect_repository(self, service):
        service.gh_repo.get_connected_repo_by_full_name.return_value = None
        cr = MagicMock()
        cr.id = 5
        service.gh_repo.connect_repository.return_value = cr
        r = service.connect_repository(1, 100, "org/repo")
        assert r["status"] == "connected"
        assert r["id"] == 5

    def test_connect_repository_already(self, service):
        existing = MagicMock()
        existing.id = 5
        existing.is_active = True
        service.gh_repo.get_connected_repo_by_full_name.return_value = existing
        r = service.connect_repository(1, 100, "org/repo")
        assert r["status"] == "already_connected"

    def test_disconnect_repository(self, service):
        service.gh_repo.disconnect_repository.return_value = True
        r = service.disconnect_repository(1)
        assert r["status"] == "disconnected"

    def test_disconnect_repository_not_found(self, service):
        service.gh_repo.disconnect_repository.return_value = False
        r = service.disconnect_repository(999)
        assert r["status"] == "not_found"

    def test_get_connected_repositories(self, service):
        cr = MagicMock()
        cr.id = 1
        cr.full_name = "org/repo"
        cr.default_branch = "main"
        cr.selected_branch = None
        cr.is_private = False
        cr.auto_sync = True
        cr.sync_status = "synced"
        cr.last_synced_at = None
        service.gh_repo.get_connected_repos_by_account.return_value = [cr]
        repos = service.get_connected_repositories(1)
        assert len(repos) == 1
        assert repos[0]["full_name"] == "org/repo"

    def test_sync_repository(self, service):
        cr = MagicMock()
        cr.id = 1
        cr.repository_id = 1
        cr.selected_branch = None
        cr.default_branch = "main"
        service.gh_repo.get_connected_repo.return_value = cr
        sync = MagicMock()
        sync.id = 10
        service.gh_repo.create_sync.return_value = sync
        service.job_queue.enqueue.return_value = 5
        service.job_queue.process_job.return_value = {"result": {"details": {}}}
        r = service.sync_repository(1)
        assert r["status"] == "completed"
        assert r["sync_id"] == 10

    def test_sync_repository_not_found(self, service):
        service.gh_repo.get_connected_repo.return_value = None
        r = service.sync_repository(999)
        assert r["status"] == "not_found"

    def test_sync_repository_failure(self, service):
        cr = MagicMock()
        cr.id = 1
        cr.repository_id = 1
        cr.selected_branch = None
        cr.default_branch = "main"
        cr.full_name = "org/repo"
        service.gh_repo.get_connected_repo.return_value = cr
        sync = MagicMock()
        sync.id = 10
        service.gh_repo.create_sync.return_value = sync
        service.job_queue.enqueue.return_value = 5
        service.job_queue.process_job.side_effect = Exception("boom")
        r = service.sync_repository(1)
        assert r["status"] == "failed"

    def test_select_branch(self, service):
        cr = MagicMock()
        service.gh_repo.get_connected_repo.return_value = cr
        r = service.select_branch(1, "develop")
        assert r["status"] == "updated"

    def test_select_branch_not_found(self, service):
        service.gh_repo.get_connected_repo.return_value = None
        r = service.select_branch(999, "x")
        assert r["status"] == "not_found"

    def test_detect_default_branch(self, service):
        cr = MagicMock()
        cr.default_branch = "main"
        service.gh_repo.get_connected_repo.return_value = cr
        r = service.detect_default_branch(1)
        assert r["default_branch"] == "main"

    def test_detect_default_branch_not_found(self, service):
        service.gh_repo.get_connected_repo.return_value = None
        r = service.detect_default_branch(999)
        assert r["status"] == "not_found"

    def test_get_jobs(self, service):
        j = MagicMock()
        j.id = 1
        j.job_type = "push_pipeline"
        j.status = "completed"
        j.attempt = 1
        j.duration_seconds = 1.5
        j.error_message = None
        j.created_at = "2026-01-01"
        service.gh_repo.get_jobs_by_repo.return_value = [j]
        jobs = service.get_jobs(1)
        assert len(jobs) == 1

    def test_get_job(self, service):
        service.job_queue.get_job_status.return_value = {"id": 1, "status": "completed"}
        r = service.get_job(1)
        assert r["status"] == "completed"

    def test_get_job_not_found(self, service):
        service.job_queue.get_job_status.return_value = None
        assert service.get_job(999) is None

    def test_get_pr_analysis(self, service):
        pra = MagicMock()
        pra.id = 1
        pra.pr_number = 42
        pra.pr_title = "Feature"
        pra.pr_author = "dev"
        pra.head_branch = "feat"
        pra.base_branch = "main"
        pra.status = "completed"
        pra.changed_files = 3
        pra.changed_classes = 1
        pra.changed_functions = 2
        pra.architecture_impact = "Low"
        pra.documentation_impact = "Low"
        pra.risk_score = 0.2
        pra.risk_level = "low"
        pra.breaking_changes = []
        pra.recommended_tests = {}
        pra.summary = "ok"
        service.gh_repo.get_pr_analysis.return_value = pra
        r = service.get_pr_analysis(1)
        assert r["pr_number"] == 42

    def test_get_pr_analysis_not_found(self, service):
        service.gh_repo.get_pr_analysis.return_value = None
        assert service.get_pr_analysis(999) is None
