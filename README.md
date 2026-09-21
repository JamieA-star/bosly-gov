BOSLY GOV v4

Overview
Bosly Gov v4 is a browser-based local copilot interface.
When you run bosly, it starts a local Python server and opens the web UI.

Launch

Two distinct things, easy to confuse:

  A) The orientation command (the normal daily driver)
     In the terminal, run:  bosly
     This prints the project orientation summary (pipeline state, top
     open plan items, recent commits, recent memory, locations). It
     does NOT launch the server. It does NOT open a browser.

  B) The browser UI (used less often)
     The Gov web UI runs on http://localhost:3102 and is bound to
     localhost only by design. To use it from another machine (e.g. a
     laptop on the same network), tunnel the port:

         ssh -L 3102:localhost:3102 bosly

     then browse http://localhost:3102 on the other machine.

     The Claude integration in routers/direct_llm.py is reachable via
     this UI. The more the UI is used, the better it gets — this is
     the teaching loop, not a side effect.

Built-in commands
The following commands are routed directly to local scripts for fast execution:
- health
- diagnose
- deploy
- housekeep
- audit
- backup
- evolve
- smoke

Natural-language matching is supported. Example:
- "how is the server" -> health
- "run a quick smoke test" -> smoke

Consent model
Bosly has two modes:
1) Built-in command mode - Runs known commands immediately.
2) LLM mode - Non-command requests are sent to the LLM router. If the response suggests file/system modifications, Bosly does not execute immediately. A consent card appears in the UI. You must choose Yes (approve and execute safe file operations), Show diff (view proposed change detail), or Cancel (deny and clear pending action).

Architecture
- Backend: Python HTTP server (server.py, routers/command_router.py, routers/llm_router.py, routers/consent_store.py)
- Frontend: single-page static UI (static/index.html, static/bosly.css, static/app.js)
- Launcher: /usr/local/bin/bosly

Config
Config file: bosly-gov-v4/config.json
Default values: host 127.0.0.1, port 3102, log_level INFO
Server is localhost-only by design.

Troubleshooting
1) "Bosly Gov is already running." - Port 3102 is already bound. Bosly opens the browser anyway.
2) Script not found errors - Verify required scripts exist and are executable at /usr/local/bin/bosly-*
3) UI opens but actions fail - Check backend logs from the terminal where bosly was started.
