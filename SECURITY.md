# Security Policy

This repository ships the official Routeplane Python SDK, published to PyPI as
**`routeplane`**. It handles **gateway credentials** and constructs every request your
application sends through the gateway, so we treat security reports here as the
highest-priority class of issue.

## Reporting a vulnerability

Email **security@routeplane.ai**.

Please include:

- The version affected (`pip show routeplane`).
- A description of the issue and the component affected (module or function if known).
- Reproduction steps or a proof of concept.
- Your assessment of impact, if you have one.

You can also use GitHub's private vulnerability reporting on this repository if you prefer not
to use email. Please do **not** open a public issue for anything you believe is a vulnerability.

**Never include a real gateway key, provider API key, or customer data in a report.** Redact
them; we can reproduce from the shape of the request.

## What to expect (coordinated disclosure)

- **Acknowledgement within 72 hours** of your report reaching us.
- An initial assessment (accepted / needs-more-info / not-a-vulnerability) within 7 days.
- We ask for a standard **90-day coordinated disclosure window** while we develop, test, and
  release a fix. We will agree a disclosure date with you and credit you in the release notes
  (or keep you anonymous — your choice).
- If we ship a fix sooner, we will coordinate earlier disclosure rather than sitting on the
  window.

## Scope

**In scope:** the `routeplane` package published from this repository and the CI workflows that
build it. We are particularly interested in:

- **Credential handling** — a gateway key leaking into logs, exception messages, tracebacks,
  `__repr__` output, or a file written with loose permissions.
- **Request construction** — header or URL injection through SDK parameters, or anything that
  causes a request to be sent to a host other than the configured gateway.
- **TLS verification** being weakened or bypassable through ordinary use of the public API.
- **Dependency and supply-chain issues** in what we publish.

**Out of scope:** the Routeplane gateway itself (report those to the same address — they are
handled outside this repo's process), third-party LLM providers, issues that require an already
compromised host, and findings that depend on a maliciously modified local config file.

## Bug bounty

We do **not** run a paid bug bounty program. We are a small team and we would rather say so
plainly than promise rewards we cannot pay consistently. We credit reporters in release notes,
and we fix confirmed reports fast.

## Supported versions

Security fixes land on the latest published version. During the 0.x series we do not backport
to older versions — upgrade to the newest release to receive fixes.
