"""GitHub CLI contracts use bounded mocked subprocess responses only."""

import json
import subprocess
from types import SimpleNamespace

import pytest
from test_delivery import ready_observation

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.delivery_models import DeliveryError
from agrosphere_orchestrator.github_provider import GitHubCliAdapter, GitHubProvider, remote_slug


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/acme/estate.git",
        "git@github.com:acme/estate.git",
        "https://github.com/acme/estate",
    ],
)
def test_canonical_remotes(url):
    assert remote_slug(url) == "acme/estate"


@pytest.mark.parametrize(
    "url",
    [
        "https://token@github.com/acme/estate",
        "https://evil.example/acme/estate",
        "-evil",
        "https://github.com/acme/../estate",
        "ssh://evil/acme/estate",
        "https://github.com/acme/estate?token=secret",
    ],
)
def test_untrusted_remotes_rejected(url):
    with pytest.raises(DeliveryError):
        remote_slug(url)


@pytest.mark.parametrize(
    "error,code",
    [
        ("HTTP 401 secret-token", "AUTHENTICATION"),
        ("403 ghp_secret", "AUTHENTICATION"),
        ("rate limit 429 secret", "RATE_LIMIT"),
        ("404 secret", "NOT_FOUND"),
        ("network secret", "PROVIDER_UNAVAILABLE"),
    ],
)
def test_provider_error_classification_never_exposes_secrets(tmp_path, error, code):
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=1, stdout="", stderr=error)

    adapter = GitHubCliAdapter(Settings(_env_file=None), tmp_path, runner)
    with pytest.raises(DeliveryError) as caught:
        adapter.api("user")
    assert caught.value.code == code
    assert "secret" not in str(caught.value)
    assert len(calls) <= 2
    assert all("--hostname" in c and "github.com" in c and "GET" in c for c in calls)


def test_write_timeout_is_not_retried(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        raise subprocess.TimeoutExpired(argv, 1)

    adapter = GitHubCliAdapter(
        Settings(_env_file=None, github_remote_writes=True), tmp_path, runner
    )
    with pytest.raises(DeliveryError):
        adapter.api(
            "repos/acme/estate/pulls",
            "POST",
            {
                "title": "title",
                "body": "literal $() backticks",
                "head": "aeo/x",
                "base": "main",
                "draft": False,
            },
        )
    assert len(calls) == 1


@pytest.mark.parametrize("body", ["not-json", "{}" * 2000])
def test_invalid_or_oversized_provider_output_blocks(tmp_path, body):
    adapter = GitHubCliAdapter(
        Settings(_env_file=None, github_max_response_bytes=1000),
        tmp_path,
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=body, stderr=""),
    )
    with pytest.raises(DeliveryError):
        adapter.api("user")


def test_pagination_is_complete_and_bounded(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=json.dumps([{}] * 100), stderr="")

    adapter = GitHubCliAdapter(Settings(_env_file=None, github_max_pages=2), tmp_path, runner)
    with pytest.raises(DeliveryError, match="pagination"):
        adapter.pages("repos/acme/estate/pulls?state=all")
    assert len(calls) == 2
    assert calls[-1][-1].endswith("page=2")


def test_rules_and_classic_protection_are_combined(tmp_path, monkeypatch):
    unit, _ = ready_observation(tmp_path)
    adapter = GitHubCliAdapter(Settings(_env_file=None), tmp_path)
    monkeypatch.setattr(
        adapter,
        "pages",
        lambda *a: [
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [{"context": "ruleset", "integration_id": 42}],
                },
            },
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 2,
                    "require_code_owner_review": True,
                },
            },
            {"type": "required_workflows", "parameters": {}},
        ],
    )
    monkeypatch.setattr(
        adapter,
        "api",
        lambda *a: {
            "required_status_checks": {"checks": [{"context": "classic", "app_id": 1}]},
            "required_pull_request_reviews": {"required_approving_review_count": 1},
        },
    )
    policy = adapter.policy(unit, {"protected": True})
    assert {c.name for c in policy.checks} == {"classic", "ruleset"}
    assert policy.approvals == 2 and policy.codeowners and policy.strict
    assert policy.unsupported == ["required_workflows"]
    assert policy.raw_hash


def test_policy_lookup_failure_does_not_mean_unprotected(tmp_path, monkeypatch):
    unit, _ = ready_observation(tmp_path)
    adapter = GitHubCliAdapter(Settings(_env_file=None), tmp_path)
    monkeypatch.setattr(adapter, "pages", lambda *a: [])

    def missing(*args):
        raise DeliveryError("NOT_FOUND", "404")

    monkeypatch.setattr(adapter, "api", missing)
    with pytest.raises(DeliveryError):
        adapter.policy(unit, {"protected": True})
    assert adapter.policy(unit, {"protected": False}).known


def test_no_merge_deployment_or_review_write_port():
    for name in ("merge", "deploy", "approve", "review", "workflow"):
        assert not hasattr(GitHubProvider, name)
        assert not hasattr(GitHubCliAdapter, name)


def test_create_pr_uses_literal_json_and_disabled_writes(tmp_path):
    unit, _ = ready_observation(tmp_path)
    seen = []

    def runner(argv, **kwargs):
        seen.append((argv, kwargs))
        return SimpleNamespace(returncode=1, stdout="", stderr="network")

    settings = Settings(_env_file=None)
    adapter = GitHubCliAdapter(settings, tmp_path, runner)
    with pytest.raises(DeliveryError, match="disabled"):
        adapter.create_pr(unit, "title", "body")
    assert not seen
    settings.github_remote_writes = True
    with pytest.raises(DeliveryError):
        adapter.create_pr(unit, "title", "$(literal) \nbody")
    assert len(seen) == 1
    argv, kwargs = seen[0]
    assert "POST" in argv and argv[-2:] == ["--input", "-"]
    assert json.loads(kwargs["input"])["body"] == "$(literal) \nbody"


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("repos/acme/estate/merges", {}),
        ("repos/acme/estate/actions/workflows/1/dispatches", {}),
        ("graphql", {"query": "mutation { dangerous }"}),
    ],
)
def test_no_generic_api_mutation_bypass(tmp_path, endpoint, payload):
    called = []
    adapter = GitHubCliAdapter(
        Settings(_env_file=None, github_remote_writes=True),
        tmp_path,
        lambda *a, **k: called.append(a),
    )
    with pytest.raises(DeliveryError):
        adapter.api(endpoint, "POST", payload)
    assert not called


def test_observe_maps_actual_head_check_review_and_permission_contracts(tmp_path, monkeypatch):
    import agrosphere_orchestrator.github_provider as module

    unit, _ = ready_observation(tmp_path)
    monkeypatch.setattr(module, "check_remote", lambda *a: None)

    def response(argv, **kwargs):
        endpoint = argv[-3] if "--input" in argv else argv[-1]
        if endpoint == "user":
            data = {"login": "publisher"}
        elif endpoint == "repos/acme/estate":
            data = {
                "id": 1,
                "owner": {"login": "acme"},
                "name": "estate",
                "permissions": {"push": True},
            }
        elif "/branches/main/protection" in endpoint:
            data = {"required_status_checks": {"checks": [{"context": "build", "app_id": 42}]}}
        elif endpoint.startswith("repos/acme/estate/branches/main"):
            data = {"protected": True, "commit": {"sha": unit.base_sha}}
        elif "/git/ref/heads/" in endpoint:
            data = {"object": {"sha": unit.head_sha}}
        elif "/rules/branches/" in endpoint:
            data = []
        elif "/check-runs" in endpoint:
            data = {
                "check_runs": [
                    {
                        "name": "build",
                        "head_sha": unit.head_sha,
                        "status": "completed",
                        "conclusion": "success",
                        "app": {"id": 42},
                    }
                ]
            }
        elif "/statuses" in endpoint:
            data = [{"context": "optional", "state": "pending"}]
        elif "/reviews" in endpoint:
            data = [
                {
                    "id": 20,
                    "user": {"login": "human", "type": "User"},
                    "commit_id": unit.head_sha,
                    "state": "APPROVED",
                    "submitted_at": "2026-01-01T00:00:00Z",
                }
            ]
        elif endpoint == "graphql":
            data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewDecision": "APPROVED",
                            "headRefOid": unit.head_sha,
                            "baseRefOid": unit.base_sha,
                        }
                    }
                }
            }
        else:
            pr = {
                "id": 10,
                "number": 1,
                "html_url": "https://github.com/acme/estate/pull/1",
                "base": {"repo": {"id": 1}, "ref": "main", "sha": unit.base_sha},
                "head": {"repo": {"id": 1}, "ref": "aeo/a", "sha": unit.head_sha},
                "state": "open",
                "user": {"login": "author"},
                "mergeable": True,
            }
            data = [pr] if "/pulls?" in endpoint else pr
        return SimpleNamespace(returncode=0, stdout=json.dumps(data), stderr="")

    adapter = GitHubCliAdapter(Settings(_env_file=None), tmp_path, response)
    observed = adapter.observe(unit)
    assert observed.can_push and observed.principal == "publisher"
    assert observed.remote.id == 1 and observed.branch_sha == unit.head_sha
    assert observed.prs[0].review_decision == "APPROVED"
    assert observed.checks[0].sha == unit.head_sha and observed.checks[0].state == "success"
    assert observed.checks[1].raw_status == "pending"
    assert observed.reviews[0].actor_type == "User"
    assert observed.policy.checks[0].app_id == 42


def test_push_uses_exact_nonforce_ref_and_existing_gh_credentials(tmp_path, monkeypatch):
    import agrosphere_orchestrator.github_provider as module

    unit, _ = ready_observation(tmp_path)
    calls = []
    monkeypatch.setattr(module, "check_remote", lambda *a: None)

    def safe_git(root, *args):
        calls.append(args)
        return (
            unit.head_sha
            if args == ("rev-parse", "HEAD")
            else unit.branch
            if args == ("branch", "--show-current")
            else ""
        )

    monkeypatch.setattr(module, "git", safe_git)
    adapter = GitHubCliAdapter(Settings(_env_file=None, github_remote_writes=True), tmp_path)
    adapter.push(unit, tmp_path)
    command = calls[-1]
    assert "--force" not in command and "--force-with-lease" not in command
    assert {"--no-follow-tags", "--recurse-submodules=no", "--no-signed"} <= set(command)
    assert command[-1] == unit.head_sha + ":refs/heads/" + unit.branch
    assert "credential.https://github.com.helper=!gh auth git-credential" in command
    assert "auth token" not in " ".join(command)
