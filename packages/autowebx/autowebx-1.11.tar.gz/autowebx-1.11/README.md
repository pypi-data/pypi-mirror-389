AutoWebX
========

Automate common web tasks with a lightweight Python toolkit: temp emails and inbox readers, captcha solvers, phone/SMS helpers, Playwright input humanizer, proxy utilities, and auto‑saving data structures.

Features
- Temp email helpers: temp-mail.io, mail.tm, email-fake.com, inboxes.com, Remotix Mail
- Captcha solvers: 2Captcha (Recaptcha v2/v3, Turnstile, image-to-text), CapSolver (Recaptcha v2)
- Phone verification helpers: 5sim pricing and activations
- Playwright “human” input utilities (mouse and typing)
- Proxy utilities including LunaProxy builder
- Auto-saving dict/set/queue, file append/replace helpers
- Lightweight inter-process message passing

Installation
- Python 3.9+
- Install from source:
  - `pip install -e .` (or `pip install .` to build a wheel)
- Optional: Playwright support requires `playwright` and a browser install: `pip install playwright` then `playwright install`

Quick Start
- Account generation
  - `from autowebx.account import Account; acc = Account(); print(acc.email, acc.password)`
- Temp Mail (internal temp-mail.io)
  - `from autowebx.temp_mail import Email; e = Email(); print(e.address); print(e.get_messages())`
- Mail.tm
  - `from autowebx.mail_tm import MailTmAccount; a = MailTmAccount(); print(a.email, a.password); print(a.messages())`
- Inboxes.com
  - `from autowebx.inboxes import Inboxes; ib = Inboxes('user@example.com'); msgs = ib.inbox(); html = ib.html(msgs[0])`
- Remotix Mail
  - `from autowebx.remotix_mail import messages, domains; print(domains()); print(messages('user@remotix.app'))`
- 2Captcha (Recaptcha v2/v3)
  - `from autowebx.two_captcha import TwoCaptcha, CaptchaType; token = TwoCaptcha('<api_key>', CaptchaType.recaptchaV2, 'https://site', '<site_key>').solution()`
- 2Captcha (Turnstile)
  - `from autowebx.two_captcha import Turnstile; token = Turnstile('<api_key>', 'https://site', '<site_key>').solution()`
- CapSolver (Recaptcha v2)
  - `from autowebx.capsolver import RecaptchaV2; token = RecaptchaV2('<api_key>', 'https://site', '<site_key>').solution()`
- 5sim pricing and activations
  - `from autowebx.five_sim import FiveSim, min_cost_providers; fs = FiveSim('<api_token>'); print(fs.balance()); phone = fs.buy_activation_number('netherlands','any','other')`
- Playwright humanizer
  - `from autowebx.human_wright import add_mouse_position_listener, click, fill, show_mouse`
  - Use with a `playwright.sync_api.Page` to move the mouse and type more human‑like.
- Proxy helper
  - `from autowebx.proxy import Proxy, LunaProxy; p = Proxy('user:pass@host:port'); requests_proxies = p.for_requests()`

CLI: HTTP -> Requests boilerplate
- The `functioner` console script converts a raw HTTP request file into a Python method using `requests`.
- Usage: `functioner path\to\request.txt` → writes `function.py` with a ready‑to‑paste method.

Modules Overview
- `autowebx.account` – `Account`, password/username/US phone/address generators
- `autowebx.temp_mail` – create temp-mail.io inbox; `domains()` helper with caching
- `autowebx.mail_tm` – `MailTmAccount` with JWT token management
- `autowebx.email_fake` – read/delete messages from email-fake.com
- `autowebx.inboxes` – poll inboxes.com and fetch message HTML
- `autowebx.remotix_mail` – fetch messages/domains from Remotix Mail
- `autowebx.two_captcha` – 2Captcha wrappers (Recaptcha v2/v3, Turnstile, ImageToText)
- `autowebx.capsolver` – CapSolver Recaptcha v2 wrapper
- `autowebx.five_sim` – 5sim pricing utilities and activation API
- `autowebx.human_wright` – Playwright helpers for human‑like mouse/typing
- `autowebx.proxy` – Parse proxies, build `requests`/Playwright configs, `LunaProxy`
- `autowebx.files` – thread‑safe append, replace, reactive File buffer
- `autowebx.auto_save_dict|set|queue` – persistent containers that save on mutation
- `autowebx.communications` – simple localhost message send/receive primitives
- `autowebx.panels` – SMS panel readers (Premiumy, Sniper, PSCall, Ziva) + `ReportReader`
- `autowebx.remotix` – remote usage logging/metrics (Run)

Notes & Best Practices
- Network usage: Several modules do network I/O on method calls. Avoid calling them inside tight loops without backoff.
- Optional deps: Playwright usage requires installing Playwright and browsers separately.
- Secrets: Do not hardcode API keys/tokens. Use environment variables or config files.
- Error handling: Helpers raise `TimeoutError`, `ConnectionError`, or library‑specific errors (e.g., `CaptchaError`). Catch and retry as needed.
- Thread safety: `autowebx.files.add` and `sync_print` append safely. Persistent containers save on each mutation.

Development
- Run lint/tests as appropriate for your environment.
- Update `CHANGELOG.md` when publishing.
- Packaging entry point: `functioner` maps to `autowebx.__init__:__get_function__`.

License
- See repository terms. This project includes code snippets that contact third‑party services; check their terms of service before use.

