// Bosly Gov — Project Workspaces
(function () {
  "use strict";

  let currentProject = null;
  let currentReportYear = null;
  let reportContent = "";

  const projectTabsEl = document.getElementById("projectTabs");
  const reportPanel = document.getElementById("reportPanel");
  const reportTitle = document.getElementById("reportTitle");
  const reportView = document.getElementById("reportView");
  const reportEdit = document.getElementById("reportEdit");
  const reportEditor = document.getElementById("reportEditor");
  const reportEditBtn = document.getElementById("reportEditBtn");
  const reportNewBtn = document.getElementById("reportNewBtn");
  const reportSaveBtn = document.getElementById("reportSaveBtn");
  const reportCancelBtn = document.getElementById("reportCancelBtn");
  const reportToggleBtn = document.getElementById("reportToggleBtn");
  const reportCloseBtn = document.getElementById("reportCloseBtn");
  const memoryToggleBtn = document.getElementById("memoryToggleBtn");
  const memoryView = document.getElementById("memoryView");

  function api(method, path, body) {
    return fetch("/gov" + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    }).then((r) => r.json());
  }

  function loadProjects() {
    return api("GET", "/api/projects").then((data) => {
      if (data.ok && Array.isArray(data.projects)) {
        return data.projects;
      }
      return [];
    });
  }

  function renderTabs(projects) {
    if (!projectTabsEl) return;
    projectTabsEl.innerHTML = "";
    projects.forEach((slug) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn project-tab" + (slug === currentProject ? " active" : "");
      btn.textContent = slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
      btn.addEventListener("click", () => switchProject(slug));
      projectTabsEl.appendChild(btn);
    });
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "btn project-add";
    addBtn.textContent = "+";
    addBtn.title = "New project";
    addBtn.addEventListener("click", newProject);
    projectTabsEl.appendChild(addBtn);
  }

  function loadReports(slug) {
    return api("GET", `/api/project/${slug}/reports`).then((data) => {
      if (data.ok && Array.isArray(data.reports)) {
        return data.reports;
      }
      return [];
    });
  }

  function loadReport(slug, year) {
    return api("GET", `/api/project/${slug}/report/${year}`).then((data) => {
      if (data.ok && typeof data.content === "string") {
        return data.content;
      }
      return "";
    });
  }

  function toggleReportPanel() {
    if (reportPanel.classList.contains("collapsed")) {
      reportPanel.classList.remove("collapsed");
      reportToggleBtn.textContent = "Hide Report";
    } else {
      reportPanel.classList.add("collapsed");
      reportToggleBtn.textContent = "Show Report";
    }
  }

  function closeReport() {
    reportPanel.classList.add("hidden");
  }

  function showReportView(slug, year, content) {
    currentReportYear = year;
    reportContent = content;
    reportTitle.textContent = `${slug} — ${year} Report`;
    reportView.textContent = content || "(empty report)";
    reportPanel.classList.remove("hidden");
    reportView.classList.remove("hidden");
    reportEdit.classList.add("hidden");
  }

  function showReportEdit() {
    reportEditor.value = reportContent || "";
    reportView.classList.add("hidden");
    reportEdit.classList.remove("hidden");
    reportPanel.classList.add("fullscreen");
    reportEditor.focus();
  }

  function hideReportEdit() {
    reportView.classList.remove("hidden");
    reportEdit.classList.add("hidden");
    reportPanel.classList.remove("fullscreen");
  }

  async function saveReport() {
    if (!currentProject || !currentReportYear) return;
    const content = reportEditor.value;
    const result = await api("PUT", `/api/project/${currentProject}/report/${currentReportYear}`, { content });
    if (result.ok) {
      reportContent = content;
      reportView.textContent = content || "(empty report)";
      hideReportEdit();
    } else {
      alert("Save failed: " + (result.error || "unknown error"));
    }
  }

  async function newReportYear() {
    if (!currentProject) return;
    const result = await api("POST", `/api/project/${currentProject}/report/new`);
    if (result.ok && result.year) {
      const content = await loadReport(currentProject, result.year);
      showReportView(currentProject, result.year, content);
    } else {
      alert("Failed to create new report: " + (result.error || "unknown error"));
    }
  }

  function newProject() {
    const name = prompt("Enter project name (lowercase, hyphens):");
    if (!name) return;
    const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!slug) {
      alert("Invalid project name.");
      return;
    }
    api("POST", "/api/projects", { name: slug }).then((result) => {
      if (result.ok) {
        currentProject = slug;
        return loadProjects().then((projects) => {
          renderTabs(projects);
          return switchProject(slug);
        });
      } else {
        alert("Failed to create project: " + (result.error || "unknown error"));
      }
    });
  }

  function switchProject(slug) {
    currentProject = slug;
    return loadProjects().then((projects) => {
      renderTabs(projects);
      return loadReports(slug).then((reports) => {
        if (reports.length > 0) {
          const latest = reports[0]; // sorted desc
          return loadReport(slug, latest).then((content) => {
            showReportView(slug, latest, content);
          });
        } else {
          reportPanel.classList.add("hidden");
        }
        // Also switch chat storage key
        if (window.switchChatProject) {
          window.switchChatProject(slug);
        }
      });
    });
  }

  // Initialise
  function init() {
    loadProjects().then((projects) => {
      if (projects.length > 0) {
        currentProject = projects[0];
        renderTabs(projects);
        switchProject(currentProject);
      } else {
        renderTabs([]);
      }
    });
  }

  function loadMemory(slug) {
    return api("GET", `/api/project/${slug}/memory`).then((data) => {
      if (data.ok) {
        return data;
      }
      return null;
    }).catch(() => null);
  }

  function toggleMemory() {
    if (!currentProject) return;
    if (memoryView.classList.contains("hidden")) {
      loadMemory(currentProject).then((data) => {
        if (data && data.memory) {
          memoryView.textContent = JSON.stringify(data.memory, null, 2);
        } else {
          memoryView.textContent = "(no consolidated memory yet)";
        }
        memoryView.classList.remove("hidden");
        memoryToggleBtn.textContent = "Hide";
      });
    } else {
      memoryView.classList.add("hidden");
      memoryToggleBtn.textContent = "Show";
    }
  }

  // Bind report buttons
  if (reportEditBtn) reportEditBtn.addEventListener("click", showReportEdit);
  if (reportNewBtn) reportNewBtn.addEventListener("click", newReportYear);
  if (reportSaveBtn) reportSaveBtn.addEventListener("click", saveReport);
  if (reportCancelBtn) reportCancelBtn.addEventListener("click", hideReportEdit);
  if (reportToggleBtn) reportToggleBtn.addEventListener("click", toggleReportPanel);
  if (reportCloseBtn) reportCloseBtn.addEventListener("click", closeReport);
  if (memoryToggleBtn) memoryToggleBtn.addEventListener("click", toggleMemory);

  init();
})();
