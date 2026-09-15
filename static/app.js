(() => {
  "use strict";

  const STORAGE_CHAT = "boslyGovChatHistoryV4";
  const STORAGE_SAVED = "boslyGovSavedResponsesV4";

  const chatArea = document.getElementById("chatArea");
  const savedArea = document.getElementById("savedArea");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const chatTabBtn = document.getElementById("chatTabBtn");
  const savedTabBtn = document.getElementById("savedTabBtn");
  const govConsentCard = document.getElementById("govConsentCard");
  const govConsentSummary = document.getElementById("govConsentSummary");
  const govConsentDiff = document.getElementById("govConsentDiff");
  const govApproveBtn = document.getElementById("govApproveBtn");
  const govDenyBtn = document.getElementById("govDenyBtn");

  let waiting = false;
  let messageHistory = [];
  let currentChatProject = "bosly-accord";
  let savedItems = [];
  let thinkingNode = null;
  let currentTab = "chat";
  let activeAbort = null;
  let pendingSessionId = null;
  let pendingToken = null;

  function safeText(v) { return v == null ? "" : String(v); }
  function nowIso() { return new Date().toISOString(); }
  function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  function formatDateTime(iso) {
    const d = new Date(iso);
    return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  async function loadState() {
    // Load saved items from localStorage
    try { savedItems = JSON.parse(localStorage.getItem(STORAGE_SAVED) || "[]"); } catch { savedItems = []; }
    // Load chat from server for current project
    try {
      const resp = await fetch(`/gov/api/project/${currentChatProject}/chat`);
      const data = await resp.json().catch(() => ({}));
      if (data.ok && Array.isArray(data.messages)) {
        messageHistory = data.messages;
      } else {
        messageHistory = [];
      }
    } catch {
      messageHistory = [];
    }
  }
  function persistChat() {
    const chatKey = `${STORAGE_CHAT}_${currentChatProject}`;
    localStorage.setItem(chatKey, JSON.stringify(messageHistory));
  }

  window.switchChatProject = function (slug) {
    if (!slug || slug === currentChatProject) return;
    currentChatProject = slug;
    loadState();
    renderChat();
  };
  function persistSaved() { localStorage.setItem(STORAGE_SAVED, JSON.stringify(savedItems)); }

  function setOnlineStatus(online, text) {
    statusDot.classList.toggle("online", !!online);
    statusText.textContent = text || (online ? "Online" : "Offline");
  }

  function setWaiting(v) {
    waiting = !!v;
    sendBtn.disabled = waiting;
    sendBtn.textContent = waiting ? "Sending…" : "Send";
    chatInput.disabled = waiting;
  }

  function scrollToBottom() {
    if (currentTab === "chat") chatArea.scrollTop = chatArea.scrollHeight;
  }

  function parseCodeBlocks(text) {
    const blocks = [];
    const regex = /```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g;
    let match;
    let lastIndex = 0;
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) blocks.push({ type: "text", value: text.slice(lastIndex, match.index) });
      blocks.push({ type: "code", lang: (match[1] || "code").toLowerCase(), value: match[2] });
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) blocks.push({ type: "text", value: text.slice(lastIndex) });
    return blocks;
  }

  function maybeExtractFilePath(text) {
    const m = text.match(/(?:^|\s)([\w./-]+\.[a-zA-Z0-9]+)(?=\s|$|:)/);
    return m ? m[1] : "";
  }

  function buildCodeBlock(code, lang, filePath) {
    const wrap = document.createElement("div");
    wrap.className = "code-wrap";

    const head = document.createElement("div");
    head.className = "code-head";
    head.innerHTML = `<span>${lang}</span>`;

    const actions = document.createElement("div");
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "copy-btn";
    copyBtn.textContent = "Copy";
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code);
        copyBtn.textContent = "Copied";
        setTimeout(() => (copyBtn.textContent = "Copy"), 1200);
      } catch {}
    });
    actions.appendChild(copyBtn);

    if (filePath) {
      const applyBtn = document.createElement("button");
      applyBtn.type = "button";
      applyBtn.className = "apply-btn";
      applyBtn.textContent = "Apply fix";
      applyBtn.addEventListener("click", () => {
        chatInput.value = `Apply this fix to ${filePath}`;
        chatInput.focus();
      });
      actions.appendChild(applyBtn);
    }

    head.appendChild(actions);

    const pre = document.createElement("pre");
    const codeEl = document.createElement("code");
    codeEl.textContent = code;
    pre.appendChild(codeEl);

    wrap.appendChild(head);
    wrap.appendChild(pre);
    return wrap;
  }

  function createMessageEl(msg, idx) {
    const row = document.createElement("div");
    row.className = `message-row ${msg.role}`;

    const card = document.createElement("div");
    card.className = "message";

    const meta = document.createElement("div");
    meta.className = "meta";

    const left = document.createElement("span");
    left.textContent = `${msg.role === "user" ? "You" : msg.role === "bosly" ? "Bosly" : "System"} • ${formatTime(msg.timestamp)}`;
    meta.appendChild(left);

    if (msg.role === "bosly") {
      const starBtn = document.createElement("button");
      starBtn.type = "button";
      starBtn.className = "star-btn";
      starBtn.textContent = "☆";
      const savedMatch = savedItems.find((s) => s.messageId === msg.id);
      if (savedMatch) {
        starBtn.classList.add("saved");
        starBtn.textContent = "★";
      }
      starBtn.addEventListener("click", () => toggleSave(msg.id, idx, starBtn));
      meta.appendChild(starBtn);
    }

    card.appendChild(meta);

    const content = document.createElement("div");
    content.className = "content";

    const chunks = parseCodeBlocks(safeText(msg.text));
    const filePath = maybeExtractFilePath(msg.text || "");
    chunks.forEach((chunk) => {
      if (chunk.type === "text") {
        if (!chunk.value) return;
        const p = document.createElement("div");
        p.textContent = chunk.value.trim();
        if (p.textContent) content.appendChild(p);
      } else {
        content.appendChild(buildCodeBlock(chunk.value, chunk.lang, filePath));
      }
    });

    if (msg.context && msg.context.summary) {
      const details = document.createElement("details");
      details.className = "context-box";
      const summary = document.createElement("summary");
      summary.textContent = `Context: ${msg.context.summary}`;
      const detail = document.createElement("div");
      detail.className = "context-detail";
      detail.textContent = msg.context.detail || msg.context.summary;
      details.appendChild(summary);
      details.appendChild(detail);
      content.prepend(details);
    }

    card.appendChild(content);
    row.appendChild(card);
    return row;
  }

  function renderChat() {
    chatArea.innerHTML = "";
    messageHistory.forEach((msg, idx) => chatArea.appendChild(createMessageEl(msg, idx)));
    scrollToBottom();
  }

  function renderSaved() {
    savedArea.innerHTML = "";
    if (!savedItems.length) {
      const empty = document.createElement("div");
      empty.className = "saved-empty";
      empty.textContent = "No saved responses yet.";
      savedArea.appendChild(empty);
      return;
    }

    savedItems.slice().reverse().forEach((item) => {
      const row = document.createElement("div");
      row.className = "message-row bosly";
      const card = document.createElement("div");
      card.className = "message";

      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = `Saved • ${formatDateTime(item.savedAt)}`;
      card.appendChild(meta);

      const q = document.createElement("div");
      q.className = "content";
      q.textContent = `Q: ${item.question || "(unknown question)"}`;
      const a = document.createElement("div");
      a.className = "content";
      a.style.marginTop = "10px";
      a.textContent = `A: ${item.answer || ""}`;

      card.appendChild(q);
      card.appendChild(a);
      row.appendChild(card);
      savedArea.appendChild(row);
    });
  }

  function addMessage(role, text, extra = {}) {
    const msg = {
      id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
      role,
      text: safeText(text),
      timestamp: nowIso(),
      ...extra
    };
    messageHistory.push(msg);
    persistChat();
    chatArea.appendChild(createMessageEl(msg, messageHistory.length - 1));
    scrollToBottom();
    return msg;
  }

  function updateMessageText(messageId, newText, extraPatch = null) {
    const idx = messageHistory.findIndex((m) => m.id === messageId);
    if (idx === -1) return;
    messageHistory[idx].text = safeText(newText);
    if (extraPatch && typeof extraPatch === "object") {
      Object.assign(messageHistory[idx], extraPatch);
    }
    persistChat();
    renderChat();
  }

  function toggleSave(messageId, index, starBtnEl) {
    const msg = messageHistory[index];
    if (!msg || msg.role !== "bosly") return;

    const existingIndex = savedItems.findIndex((s) => s.messageId === messageId);
    if (existingIndex >= 0) {
      savedItems.splice(existingIndex, 1);
      if (starBtnEl) {
        starBtnEl.classList.remove("saved");
        starBtnEl.textContent = "☆";
      }
    } else {
      const question = [...messageHistory].reverse().find((m, i) => {
        const originalIndex = messageHistory.length - 1 - i;
        return originalIndex < index && m.role === "user";
      });
      savedItems.push({
        messageId,
        question: question?.text || "",
        answer: msg.text,
        savedAt: nowIso()
      });
      if (starBtnEl) {
        starBtnEl.classList.add("saved");
        starBtnEl.textContent = "★";
      }
    }
    persistSaved();
    if (currentTab === "saved") renderSaved();
  }

  async function checkHealth() {
    try {
      const r = await fetch("/gov/api/health");
      if (!r.ok) throw new Error();
      const data = await r.json();
      setOnlineStatus(true, data?.status === "healthy" ? "Online" : "Degraded");
    } catch {
      setOnlineStatus(false, "Offline");
      addMessage("system", "Server health check failed.");
    }
  }

  function showThinking(contextFiles = []) {
    const box = document.createElement("div");
    box.className = "thinking-card";
    box.id = "thinkingCard";
    box.innerHTML = `
      <div class="thinking-title">Bosly is working</div>
      <div class="thinking-line">Reading your files... <span class="dots"><span></span><span></span><span></span></span></div>
      <div class="thinking-line">Checking the Accord... <span class="dots"><span></span><span></span><span></span></span></div>
      <div class="thinking-line">Thinking... <span class="dots"><span></span><span></span><span></span></span></div>
      <details class="context-box">
        <summary>Reading ${contextFiles[0] || "current context"}, ${Math.max(contextFiles.length - 1, 0)} related files, Accord summary...</summary>
        <div class="context-detail">${contextFiles.length ? contextFiles.join(", ") : "No explicit files provided by backend context."}</div>
      </details>
    `;
    thinkingNode = box;
    chatArea.appendChild(box);
    scrollToBottom();
  }

  function hideThinking() {
    if (thinkingNode && thinkingNode.parentNode) thinkingNode.parentNode.removeChild(thinkingNode);
    thinkingNode = null;
  }

  async function sendChatMessage(message) {
    const resp = await fetch(`/gov/api/project/${currentChatProject}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || data.ok === false) {
      throw new Error(safeText(data.error || `Request failed (${resp.status})`));
    }
    return data;
  }

  function parseContextFromResponse(res) {
    const files = [];
    if (Array.isArray(res.context_files)) files.push(...res.context_files.map(safeText).filter(Boolean));
    if (res.current_file) files.unshift(safeText(res.current_file));
    const tier = safeText(res.context_tier || "light");
    return {
      summary: files.length
        ? `[${tier}] Reading ${files[0]}${files.length > 1 ? `, ${files.length - 1} related files` : ""}, Accord summary...`
        : `[${tier}] Reading your files and Accord summary...`,
      detail: files.length ? files.join(", ") : "Context inferred from current session.",
      files
    };
  }

  async function streamChatMessage(message, onContext, onToken, onDone) {
    const controller = new AbortController();
    activeAbort = controller;

    const resp = await fetch("/gov/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify({ message }),
      signal: controller.signal
    });

    const contentType = safeText(resp.headers.get("content-type"));
    if (!resp.ok || !contentType.includes("text/event-stream")) {
      const fallback = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(safeText(fallback.error || `Request failed (${resp.status})`));
      return { mode: "json", payload: fallback };
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const lines = chunk.split("\n").map((l) => l.trim()).filter(Boolean);
        let eventName = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        let payload = {};
        try { payload = JSON.parse(data); } catch { continue; }

        if (eventName === "context") onContext(payload);
        else if (eventName === "token") onToken(safeText(payload.text || ""));
        else if (eventName === "done") {
          onDone(payload);
          activeAbort = null;
          return { mode: "sse", payload };
        } else if (eventName === "error") {
          throw new Error(safeText(payload.error || "Streaming error"));
        }
      }
    }

    activeAbort = null;
    return { mode: "sse", payload: {} };
  }

  async function apiFix(payload) {
    const resp = await fetch("/api/fix", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || data.ok === false) {
      throw new Error(safeText(data.error || "Request failed"));
    }
    return data;
  }

  function parseFixCommand(text) {
    const t = safeText(text).trim();
    let m = t.match(/^\/fix\s+(.+)$/i);
    if (m) return { file: safeText(m[1]).trim() };
    m = t.match(/^fix\s+(.+)$/i);
    if (m) return { file: safeText(m[1]).trim() };
    m = t.match(/apply\s+this\s+fix\s+to\s+([^\s]+)$/i);
    if (m) return { file: safeText(m[1]).trim() };
    return null;
  }

  function showConsentCard(sessionId, token, diff, summary) {
    pendingSessionId = sessionId;
    pendingToken = token;
    if (govConsentSummary) govConsentSummary.textContent = summary || "Fix proposal ready";
    if (govConsentDiff) govConsentDiff.textContent = diff || "";
    if (govConsentCard) govConsentCard.style.display = "block";
  }

  function hideConsentCard() {
    pendingSessionId = null;
    pendingToken = null;
    if (govConsentCard) govConsentCard.style.display = "none";
  }

  async function approvePendingFix() {
    if (!pendingSessionId) return;
    const sessionId = pendingSessionId;
    hideConsentCard();
    const liveMessage = addMessage("bosly", "Approving fix...");
    try {
      const data = await apiFix({ mode: "resume", session_id: sessionId, action: "approve" });
      updateMessageText(liveMessage.id, "Fix approved and applied.", { role: "system" });
    } catch (err) {
      updateMessageText(liveMessage.id, "Approval error: " + safeText(err.message || err), { role: "system" });
    }
  }

  async function denyPendingFix() {
    if (!pendingSessionId) return;
    const sessionId = pendingSessionId;
    hideConsentCard();
    const liveMessage = addMessage("bosly", "Denying fix...");
    try {
      const data = await apiFix({ mode: "resume", session_id: sessionId, action: "deny" });
      updateMessageText(liveMessage.id, "Fix denied.", { role: "system" });
    } catch (err) {
      updateMessageText(liveMessage.id, "Denial error: " + safeText(err.message || err), { role: "system" });
    }
  }

  async function startFixSessionFromUI(file, originalUserMessage) {
    setWaiting(true);
    const liveMessage = addMessage("bosly", "Starting fix session for " + file + "...");
    
    try {
      const data = await apiFix({
        file: file,
        message: originalUserMessage || ("Fix " + file),
        run_project_checks: false,
        max_retries: 3
      });
      
      const session = data.session;
      if (!session) {
        updateMessageText(liveMessage.id, "No session returned from fix API.", { role: "system" });
        return;
      }
      
      const state = safeText(session.state || "");
      const status = safeText(session.status || "");
      
      if (status === "done") {
        updateMessageText(liveMessage.id, "Fix session completed for " + file + " — no errors found or patch applied.", { role: "system" });
      } else if (status === "failed") {
        updateMessageText(liveMessage.id, "Fix session failed for " + file + " — " + safeText(session.error || "unknown error"), { role: "system" });
      } else if (state === "awaiting_consent") {
        const token = safeText(session.result?.consent?.token || session.artifacts?.pending_token || "");
        const diff = safeText(session.result?.proposed_diff || "");
        const sessionId = safeText(session.session_id || "");
        updateMessageText(
          liveMessage.id,
          "Fix proposal ready for " + file + ".\n\nToken: " + token + "\n\nDiff preview:\n" + diff.substring(0, 1500),
          { role: "system" }
        );
        showConsentCard(sessionId, token, diff, "Fix proposal for " + file);
      } else {
        updateMessageText(liveMessage.id, "Fix session running for " + file + " — state: " + state, { role: "system" });
      }
    } catch (err) {
      updateMessageText(liveMessage.id, "Fix session error: " + safeText(err.message || err), { role: "system" });
    } finally {
      setWaiting(false);
      chatInput.focus();
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (waiting) return;
    const text = safeText(chatInput.value).trim();
    if (!text) return;

    addMessage("user", text);
    chatInput.value = "";
    setWaiting(true);

    // Check for /fix command
    const fixCmd = parseFixCommand(text);
    if (fixCmd && fixCmd.file) {
      await startFixSessionFromUI(fixCmd.file, text);
      return;
    }

    const liveMessage = addMessage("bosly", "");
    const defaultFiles = ["Current file", "Accord.md", "related files"];
    showThinking(defaultFiles);

    let liveContext = { summary: "Reading your files...", detail: "", files: [] };
    let buffer = "";

    try {
      const res = await sendChatMessage(text);
      const context = parseContextFromResponse(res);
      const answer = safeText(res.reply || res.text || res.answer || "Done.");
      hideThinking();
      updateMessageText(liveMessage.id, answer, { context });
    } catch (err) {
      hideThinking();
      updateMessageText(liveMessage.id, `Request error: ${safeText(err.message || err)}`, { role: "system", context: null });
    } finally {
      hideThinking();
      setWaiting(false);
      chatInput.focus();
    }
  }

  function switchTab(tab) {
    currentTab = tab;
    const isChat = tab === "chat";
    chatArea.classList.toggle("hidden", !isChat);
    savedArea.classList.toggle("hidden", isChat);
    chatTabBtn.classList.toggle("active", isChat);
    savedTabBtn.classList.toggle("active", !isChat);
    if (!isChat) renderSaved();
    if (isChat) scrollToBottom();
  }

  function onInputKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.requestSubmit();
      return;
    }
    if (e.key === "Escape") {
      if (waiting) {
        if (activeAbort) {
          try { activeAbort.abort(); } catch {}
          activeAbort = null;
        }
        hideThinking();
        setWaiting(false);
        addMessage("system", "Request cancelled.");
      } else {
        chatInput.value = "";
      }
    }
  }

  function bind() {
    chatForm.addEventListener("submit", onSubmit);
    chatInput.addEventListener("keydown", onInputKeydown);
    chatTabBtn.addEventListener("click", () => switchTab("chat"));
    savedTabBtn.addEventListener("click", () => switchTab("saved"));
    if (govApproveBtn) govApproveBtn.addEventListener("click", approvePendingFix);
    if (govDenyBtn) govDenyBtn.addEventListener("click", denyPendingFix);
  }

  async function init() {
    await loadState();
    renderChat();
    renderSaved();
    bind();
    await checkHealth();
    chatInput.focus();
    if (!messageHistory.length) {
      addMessage("system", "Bosly Gov is ready. Calm mode enabled.");
    }
  }

  init();
})();
