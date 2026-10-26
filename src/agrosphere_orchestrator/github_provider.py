"""Fixed-host GitHub CLI adapter. No merge, deployment, review, or workflow writes."""

import json
import re
import shlex
import subprocess
from typing import Protocol
from urllib.parse import quote, urlencode

from .delivery_models import (
    Check,
    DeliveryError,
    Observation,
    Policy,
    PullRequest,
    Remote,
    RequiredCheck,
    Review,
    Unit,
)
from .execution_workspace import git
from .quality_store import digest

REVIEW_QUERY = "query($owner:String!,$repo:String!,$number:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$number){reviewDecision headRefOid baseRefOid}}}"


class GitHubProvider(Protocol):
    def observe(self, unit: Unit) -> Observation: ...
    def dependency_available(self, unit: Unit, observation: Observation) -> bool: ...
    def push(self, unit: Unit, worktree): ...
    def create_pr(self, unit: Unit, title: str, body: str) -> PullRequest: ...


def remote_slug(url):
    patterns = (
        r"https://github\.com/([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?",
        r"git@github\.com:([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, url)
        if match:
            return match[1].lower()
    raise DeliveryError("REMOTE_IDENTITY", "Only canonical github.com remotes are permitted")


def check_remote(unit):
    try:
        dangerous = git(
            unit.root,
            "config",
            "--name-only",
            "--get-regexp",
            r"^(core\.sshcommand|core\.gitproxy|credential\..*helper|credential\.helper|remote\..*\.(receivepack|uploadpack|proxy|vcs))$",
        )
    except subprocess.CalledProcessError as exc:
        if exc.returncode != 1:
            raise DeliveryError(
                "GIT_CONFIGURATION", "Cannot verify safe Git transport configuration"
            ) from None
        dangerous = ""
    if dangerous:
        raise DeliveryError(
            "GIT_CONFIGURATION",
            "Repository transport commands and credential helpers are not permitted",
        )
    for args in (
        ("remote", "get-url", "--all", "origin"),
        ("remote", "get-url", "--push", "--all", "origin"),
    ):
        urls = git(unit.root, *args).splitlines()
        if not urls or any(remote_slug(u) != unit.remote.slug.lower() for u in urls):
            raise DeliveryError(
                "REMOTE_IDENTITY", "Fetch/push remotes do not match approved identity"
            )


class GitHubCliAdapter:
    def __init__(self, settings, cwd, runner=None):
        self.settings, self.cwd = settings, cwd
        self.runner = runner or subprocess.run
        exe = settings.github_executable
        if exe not in {"gh", "gh.exe"} and not (
            __import__("pathlib").Path(exe).is_absolute()
            and __import__("pathlib").Path(exe).name.lower() == "gh.exe"
        ):
            raise DeliveryError(
                "CONFIGURATION", "GitHub executable must be gh or an explicit trusted gh.exe"
            )

    def api(self, endpoint, method="GET", payload=None):
        if method not in {"GET", "POST"} or endpoint.startswith(("-", "http")):
            raise DeliveryError("INVALID_REQUEST", "Invalid provider request")
        if method == "POST":
            if endpoint == "graphql":
                if not payload or payload.get("query") != REVIEW_QUERY:
                    raise DeliveryError(
                        "INVALID_REQUEST", "Only the fixed review query is supported"
                    )
            elif (
                not self.settings.github_remote_writes
                or not re.fullmatch(r"repos/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/pulls", endpoint)
                or not payload
                or set(payload) != {"title", "body", "head", "base", "draft"}
            ):
                raise DeliveryError("WRITES_DISABLED", "Only explicit PR creation is supported")
        argv = [
            self.settings.github_executable,
            "api",
            "--hostname",
            "github.com",
            "--method",
            method,
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2026-03-10",
            endpoint,
        ]
        if payload is not None:
            argv += ["--input", "-"]
        attempts = 1 + (self.settings.github_read_retries if method == "GET" else 0)
        for attempt in range(attempts):
            try:
                result = self.runner(
                    argv,
                    cwd=self.cwd,
                    input=json.dumps(payload) if payload is not None else None,
                    capture_output=True,
                    text=True,
                    timeout=self.settings.github_timeout_seconds,
                )
            except (subprocess.TimeoutExpired, OSError):
                if attempt + 1 < attempts:
                    continue
                raise DeliveryError(
                    "PROVIDER_UNAVAILABLE",
                    "GitHub operation outcome unavailable; reconcile before mutation retry",
                ) from None
            if (
                len(result.stdout.encode()) + len(result.stderr.encode())
                > self.settings.github_max_response_bytes
            ):
                raise DeliveryError("RESPONSE_LIMIT", "GitHub response exceeded configured budget")
            if result.returncode:
                error = result.stderr.lower()
                code = (
                    "RATE_LIMIT"
                    if "rate limit" in error or "429" in error
                    else "AUTHENTICATION"
                    if any(s in error for s in ("401", "403", "authenticate", "login"))
                    else "NOT_FOUND"
                    if "404" in error
                    else "PROVIDER_UNAVAILABLE"
                )
                if code == "PROVIDER_UNAVAILABLE" and attempt + 1 < attempts:
                    continue
                raise DeliveryError(code, "GitHub request failed: " + code)
            try:
                return json.loads(result.stdout)
            except (json.JSONDecodeError, TypeError):
                raise DeliveryError("INVALID_RESPONSE", "GitHub returned invalid JSON") from None

    def pages(self, endpoint, field=None):
        output = []
        size = 0
        for page in range(1, self.settings.github_max_pages + 1):
            data = self.api(
                endpoint + ("&" if "?" in endpoint else "?") + f"per_page=100&page={page}"
            )
            values = data[field] if field else data
            if not isinstance(values, list):
                raise DeliveryError("INVALID_RESPONSE", "Expected a GitHub list")
            size += len(json.dumps(values).encode())
            if size > self.settings.github_max_response_bytes:
                raise DeliveryError(
                    "RESPONSE_LIMIT", "Paginated observation exceeds configured budget"
                )
            output.extend(values)
            if len(values) < 100:
                return output
        raise DeliveryError("PAGINATION_LIMIT", "Incomplete pagination blocks delivery")

    def policy(self, unit, branch):
        prefix = "repos/" + unit.remote.slug
        rules = self.pages(prefix + "/rules/branches/" + quote(unit.base, safe=""))
        protection = {}
        try:
            protection = self.api(prefix + "/branches/" + quote(unit.base, safe="") + "/protection")
        except DeliveryError as exc:
            if exc.code != "NOT_FOUND" or branch.get("protected") is not False:
                raise
        policy = Policy(known=True, raw_hash=digest({"rules": rules, "classic": protection}))
        requirements = protection.get("required_status_checks") or {}
        policy.strict = bool(requirements.get("strict"))
        checks = requirements.get("checks") or [
            {"context": c} for c in requirements.get("contexts", [])
        ]
        policy.checks = [RequiredCheck(name=c["context"], app_id=c.get("app_id")) for c in checks]
        reviews = protection.get("required_pull_request_reviews") or {}
        policy.approvals = reviews.get("required_approving_review_count", 0)
        policy.codeowners = bool(reviews.get("require_code_owner_reviews"))
        if protection.get("required_signatures", {}).get("enabled"):
            policy.unsupported.append("required_signatures")
        for rule in rules:
            params = rule.get("parameters", {})
            kind = rule["type"]
            if kind == "required_status_checks":
                policy.strict |= bool(params.get("strict_required_status_checks_policy"))
                policy.checks += [
                    RequiredCheck(name=c["context"], app_id=c.get("integration_id"))
                    for c in params.get("required_status_checks", [])
                ]
            elif kind == "pull_request":
                policy.approvals = max(
                    policy.approvals, params.get("required_approving_review_count", 0)
                )
                policy.codeowners |= bool(params.get("require_code_owner_review"))
                if params.get("required_review_thread_resolution"):
                    policy.unsupported.append("required_review_thread_resolution")
            elif kind not in {"deletion", "non_fast_forward"}:
                policy.unsupported.append(kind)
        if protection.get("required_conversation_resolution", {}).get("enabled"):
            policy.unsupported.append("required_conversation_resolution")
        return policy

    def pr(self, item):
        return PullRequest(
            id=item["id"],
            number=item["number"],
            url=item["html_url"],
            repository_id=item["base"]["repo"]["id"],
            head_repository_id=item["head"]["repo"]["id"],
            base=item["base"]["ref"],
            branch=item["head"]["ref"],
            base_sha=item["base"]["sha"],
            head_sha=item["head"]["sha"],
            state="merged" if item.get("merged_at") else item["state"],
            author=item["user"]["login"],
            draft=item.get("draft", False),
            mergeable=item.get("mergeable"),
            merge_sha=item.get("merge_commit_sha"),
        )

    def observe(self, unit):
        check_remote(unit)
        prefix = "repos/" + unit.remote.slug
        principal = self.api("user")["login"]
        repository = self.api(prefix)
        remote = Remote(
            id=repository["id"], owner=repository["owner"]["login"], name=repository["name"]
        )
        if remote != unit.remote:
            raise DeliveryError("REMOTE_IDENTITY", "Immutable repository identity changed")
        branch = self.api(prefix + "/branches/" + quote(unit.base, safe=""))
        branch_sha = None
        try:
            branch_sha = self.api(prefix + "/git/ref/heads/" + quote(unit.branch, safe=""))[
                "object"
            ]["sha"]
        except DeliveryError as exc:
            if exc.code != "NOT_FOUND":
                raise
        matches = self.pages(
            prefix
            + "/pulls?"
            + urlencode(
                {"state": "all", "head": unit.remote.owner + ":" + unit.branch, "base": unit.base}
            )
        )
        prs = [self.pr(p) for p in matches]
        checks, reviews = [], []
        if len(prs) == 1:
            number = prs[0].number
            detail = self.api(prefix + f"/pulls/{number}")
            prs = [self.pr(detail)]
            query = REVIEW_QUERY
            graph = self.api(
                "graphql",
                "POST",
                {
                    "query": query,
                    "variables": {
                        "owner": unit.remote.owner,
                        "repo": unit.remote.name,
                        "number": number,
                    },
                },
            )
            decision = graph.get("data", {}).get("repository", {}).get("pullRequest")
            if (
                not decision
                or decision["headRefOid"] != prs[0].head_sha
                or decision["baseRefOid"] != prs[0].base_sha
            ):
                raise DeliveryError(
                    "STALE_OBSERVATION", "GitHub head/base changed during observation"
                )
            prs[0].review_decision = decision["reviewDecision"]
            for r in self.pages(prefix + f"/pulls/{number}/reviews"):
                if r.get("submitted_at") and r.get("commit_id"):
                    reviews.append(
                        Review(
                            id=r["id"],
                            actor=r["user"]["login"],
                            actor_type=r["user"]["type"],
                            sha=r["commit_id"],
                            state=r["state"],
                            submitted_at=r["submitted_at"],
                        )
                    )
        for run in self.pages(prefix + "/commits/" + unit.head_sha + "/check-runs", "check_runs"):
            state = run.get("conclusion") if run["status"] == "completed" else run["status"]
            checks.append(
                Check(
                    name=run["name"],
                    sha=run["head_sha"],
                    state=state or "unknown",
                    raw_status=run["status"],
                    raw_conclusion=run.get("conclusion"),
                    app_id=run["app"]["id"],
                )
            )
        statuses = self.pages(prefix + "/commits/" + unit.head_sha + "/statuses")
        seen = set()
        for status in statuses:
            if status["context"] in seen:
                continue
            seen.add(status["context"])
            checks.append(
                Check(
                    name=status["context"],
                    sha=unit.head_sha,
                    state="success" if status["state"] == "success" else status["state"],
                    raw_status=status["state"],
                )
            )
        policy = self.policy(unit, branch)
        base_in_head = None
        if policy.strict and branch_sha == unit.head_sha:
            comparison = self.api(
                prefix + "/compare/" + branch["commit"]["sha"] + "..." + unit.head_sha
            )
            base_in_head = comparison.get("status") in {"ahead", "identical"}
        return Observation(
            remote=remote,
            principal=principal,
            can_push=repository.get("permissions", {}).get("push") is True,
            branch_sha=branch_sha,
            base_sha=branch["commit"]["sha"],
            prs=prs,
            policy=policy,
            base_in_head=base_in_head,
            checks=checks,
            reviews=reviews,
        )

    def dependency_available(self, unit, observation):
        if observation.remote != unit.remote or len(observation.prs) != 1:
            return False
        pr = observation.prs[0]
        if (
            pr.state != "merged"
            or not pr.merge_sha
            or pr.head_sha != unit.head_sha
            or pr.repository_id != unit.remote.id
            or pr.head_repository_id != unit.remote.id
            or pr.base != unit.base
            or pr.branch != unit.branch
        ):
            return False
        result = self.api(
            "repos/" + unit.remote.slug + "/compare/" + pr.merge_sha + "..." + observation.base_sha
        )
        return result.get("status") in {"ahead", "identical"}

    def push(self, unit, worktree):
        if not self.settings.github_remote_writes:
            raise DeliveryError("WRITES_DISABLED", "Remote writes are disabled")
        check_remote(unit)
        if (
            git(worktree, "rev-parse", "HEAD") != unit.head_sha
            or git(worktree, "branch", "--show-current") != unit.branch
        ):
            raise DeliveryError("LOCAL_IDENTITY", "Isolated branch/head mismatch")
        # Git invokes this fixed credential broker; no token enters argv, evidence or logs.
        executable = self.settings.github_executable.replace("\\", "/")
        helper = "!" + shlex.quote(executable) + " auth git-credential"
        git(
            worktree,
            "-c",
            "credential.helper=",
            "-c",
            "credential.https://github.com.helper=" + helper,
            "push",
            "--no-follow-tags",
            "--recurse-submodules=no",
            "--no-signed",
            "--porcelain",
            "origin",
            unit.head_sha + ":refs/heads/" + unit.branch,
        )

    def create_pr(self, unit, title, body):
        if not self.settings.github_remote_writes:
            raise DeliveryError("WRITES_DISABLED", "Remote writes are disabled")
        return self.pr(
            self.api(
                "repos/" + unit.remote.slug + "/pulls",
                "POST",
                {
                    "title": title[:200],
                    "body": body,
                    "head": unit.branch,
                    "base": unit.base,
                    "draft": unit.draft,
                },
            )
        )
