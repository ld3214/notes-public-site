(function () {
  "use strict";

  /* ── Helpers ── */
  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  }

  function normalize(value) {
    return value.trim().toLowerCase();
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.cssText = "position:fixed;left:-9999px";
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand("copy") ? resolve() : reject(new Error("copy failed"));
      } catch (e) { reject(e); } finally { area.remove(); }
    });
  }

  /* ── Dark mode ── */
  function initTheme() {
    const toggle = document.getElementById("theme-toggle");
    const html = document.documentElement;
    const saved = localStorage.getItem("notebook-theme");
    if (saved) {
      html.dataset.theme = saved;
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      html.dataset.theme = "dark";
    }
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      const next = html.dataset.theme === "dark" ? "light" : "dark";
      html.dataset.theme = next;
      try { localStorage.setItem("notebook-theme", next); } catch (e) {}
    });
  }

  /* ── Progress bar ── */
  function initProgressBar() {
    const bar = document.getElementById("progress-bar");
    if (!bar) return;
    function update() {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const pct = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0;
      bar.style.width = pct + "%";
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* ── Back to top ── */
  function initBackToTop() {
    const btn = document.getElementById("back-to-top");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.hidden = (window.scrollY || document.documentElement.scrollTop) < 400;
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ── Mobile sidebar toggle ── */
  function initSidebarToggle() {
    const menuBtn = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (!menuBtn || !sidebar || !overlay) return;

    function openSidebar() {
      sidebar.classList.add("open");
      overlay.classList.add("active");
      document.body.style.overflow = "hidden";
    }
    function closeSidebar() {
      sidebar.classList.remove("open");
      overlay.classList.remove("active");
      document.body.style.overflow = "";
    }
    menuBtn.addEventListener("click", openSidebar);
    overlay.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("open")) closeSidebar();
    });
  }

  /* ── TOC (right panel) ── */
  function initToc() {
    const article = document.getElementById("markdown-body");
    const tocPanel = document.getElementById("toc-panel");
    const tocLinks = document.getElementById("toc-links");
    if (!article || !tocPanel || !tocLinks) return;

    const headings = Array.from(article.querySelectorAll("h2, h3"));
    if (headings.length < 2) return;

    tocPanel.hidden = false;

    const frag = document.createDocumentFragment();
    headings.forEach(function (h) {
      const a = document.createElement("a");
      a.href = h.id ? "#" + h.id : "#";
      a.className = "toc-link toc-" + h.tagName.toLowerCase();
      a.textContent = (h.textContent || "").replace(/\s*¶\s*$/, "").trim();
      frag.appendChild(a);
    });
    tocLinks.appendChild(frag);

    /* Scrollspy */
    if ("IntersectionObserver" in window) {
      const allLinks = Array.from(tocLinks.querySelectorAll(".toc-link"));
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            allLinks.forEach(function (link) {
              link.classList.toggle("active", id && link.getAttribute("href") === "#" + id);
            });
          }
        });
      }, { rootMargin: "0px 0px -55% 0px", threshold: 0 });
      headings.forEach(function (h) { if (h.id) observer.observe(h); });
    }
  }

  /* ── Code copy buttons ── */
  function addCodeTools() {
    const targets = Array.from(document.querySelectorAll(".markdown-body .codehilite, .markdown-body pre"));
    const handled = new Set();
    targets.forEach(function (target) {
      const pre = target.matches("pre") ? target : target.querySelector("pre");
      if (!pre || handled.has(pre)) return;
      handled.add(pre);

      let container = target;
      if (target.matches("pre") && !target.closest(".codehilite")) {
        container = document.createElement("div");
        container.className = "codehilite plain-code";
        container.dataset.lang = target.dataset.lang || "Code";
        target.parentNode.insertBefore(container, target);
        container.appendChild(target);
      } else if (target.matches("pre")) {
        container = target.closest(".codehilite") || target;
      }
      if (container.querySelector(".code-toolbar")) return;

      const toolbar = document.createElement("div");
      toolbar.className = "code-toolbar";
      const label = document.createElement("span");
      label.className = "code-lang";
      label.textContent = container.dataset.lang || pre.dataset.lang || "Code";
      const btn = document.createElement("button");
      btn.className = "code-copy-button";
      btn.type = "button";
      btn.textContent = "Copy";
      btn.addEventListener("click", function () {
        copyText(pre.textContent || "").then(function () {
          btn.textContent = "Copied";
          btn.classList.add("copied");
          window.setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 1400);
        }).catch(function () {
          btn.textContent = "Failed";
          window.setTimeout(function () { btn.textContent = "Copy"; }, 1400);
        });
      });
      toolbar.appendChild(label);
      toolbar.appendChild(btn);
      container.insertBefore(toolbar, pre);
    });
  }

  /* ── Search ── */
  function initSearch() {
    const input = document.getElementById("site-search");
    const results = document.getElementById("search-results");
    const navLinks = Array.from(document.querySelectorAll(".nav-link"));
    if (!input || !results) return;

    const searchIndex = window.NOTEBOOK_SEARCH_INDEX || [];

    /* "/" to focus search */
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const tag = (document.activeElement || {}).tagName;
        if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
          e.preventDefault();
          input.focus();
          input.select();
        }
      }
      if (e.key === "Escape" && document.activeElement === input) {
        input.blur();
        input.value = "";
        update();
      }
    });

    function update() {
      const query = normalize(input.value);
      navLinks.forEach(function (link) {
        const haystack = link.dataset.search || "";
        link.style.display = !query || haystack.includes(query) ? "" : "none";
      });

      if (query.length < 2 || searchIndex.length === 0) {
        results.hidden = true;
        results.innerHTML = "";
        return;
      }

      const words = query.split(/\s+/).filter(Boolean);
      const matches = searchIndex
        .map(function (item) {
          const haystack = (item.title + " " + item.path + " " + item.text).toLowerCase();
          const score = words.reduce(function (tot, w) { return tot + (haystack.includes(w) ? 1 : 0); }, 0);
          return { item, score };
        })
        .filter(function (m) { return m.score > 0; })
        .sort(function (a, b) { return b.score - a.score || a.item.path.localeCompare(b.item.path); })
        .slice(0, 8);

      if (matches.length === 0) {
        results.hidden = true;
        results.innerHTML = "";
        return;
      }

      const root = window.NOTEBOOK_ROOT || "";
      results.innerHTML = matches.map(function (m) {
        const url = root + m.item.path;
        return "<a href=\"" + escapeHtml(url) + "\"><strong>" + escapeHtml(m.item.title) + "</strong><small>" + escapeHtml(m.item.path) + "</small></a>";
      }).join("");
      results.hidden = false;
    }

    input.addEventListener("input", update);
  }

  /* ── Boot ── */
  initTheme();
  initProgressBar();
  initBackToTop();
  initSidebarToggle();
  addCodeTools();
  initToc();
  initSearch();

})();
