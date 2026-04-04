(function () {
  var AUTH_LOGIN_PATH = "/auth?mode=login";
  var AUTH_REGISTER_PATH = "/auth?mode=register";
  var CTA_SELECTOR = "a, button, [role='button']";

  function navigate(path) {
    if (window.location.pathname + window.location.search === path) {
      return;
    }
    window.location.assign(path);
  }

  function normalizeLabel(value) {
    return (value || "").replace(/\s+/g, " ").trim().toLowerCase();
  }

  function readButtonLabel(button) {
    return normalizeLabel(
      button.getAttribute("aria-label") ||
        button.getAttribute("title") ||
        button.dataset.action ||
        button.textContent
    );
  }

  function readHref(button) {
    var rawHref = button.getAttribute("href");
    return typeof rawHref === "string" ? rawHref.trim().toLowerCase() : "";
  }

  function matchesLoginTarget(label, href) {
    return (
      label.includes("sign in") ||
      label.includes("login") ||
      label.includes("log in") ||
      href === "/login" ||
      href === "/auth" ||
      href.indexOf("/auth?mode=login") === 0
    );
  }

  function matchesRegisterTarget(label, href) {
    return (
      label.includes("start free trial") ||
      label.includes("get started") ||
      label.includes("sign up") ||
      label.includes("register") ||
      label.includes("subscribe") ||
      href === "/register" ||
      href.indexOf("/auth?mode=register") === 0
    );
  }

  function navigateForElement(button) {
    var label = readButtonLabel(button);
    var href = readHref(button);

    if (matchesLoginTarget(label, href)) {
      return AUTH_LOGIN_PATH;
    }

    if (matchesRegisterTarget(label, href)) {
      return AUTH_REGISTER_PATH;
    }

    return null;
  }

  function scrollToId(id) {
    var target = document.getElementById(id);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }
    return false;
  }

  function patchElement(button) {
    if (!(button instanceof Element)) {
      return;
    }

    var targetPath = navigateForElement(button);
    if (!targetPath) {
      return;
    }

    button.setAttribute("data-route-bridge-target", targetPath);
    if (button.tagName === "A") {
      button.setAttribute("href", targetPath);
    }
  }

  function patchButtons(root) {
    var scope = root instanceof Element || root instanceof Document ? root : document;
    var nodes = scope.querySelectorAll ? scope.querySelectorAll(CTA_SELECTOR) : [];
    for (var index = 0; index < nodes.length; index += 1) {
      patchElement(nodes[index]);
    }
  }

  function normalizeCurrentPath() {
    var currentPath = window.location.pathname;
    if (currentPath === "/login") {
      navigate(AUTH_LOGIN_PATH);
      return true;
    }

    if (currentPath === "/register") {
      navigate(AUTH_REGISTER_PATH);
      return true;
    }

    return false;
  }

  function handleButtonClick(event) {
    var target = event.target;
    if (!(target instanceof Element)) {
      return;
    }

    var button = target.closest("button, a");
    if (!button) {
      return;
    }

    var authPath = navigateForElement(button);
    if (authPath) {
      event.preventDefault();
      event.stopPropagation();
      navigate(authPath);
      return;
    }

    var label = readButtonLabel(button);
    if (label.includes("see live demo") || label.includes("schedule demo") || label.includes("contact sales")) {
      event.preventDefault();
      scrollToId("pricing");
      return;
    }

    if (label.includes("explore all features") || label === "features") {
      event.preventDefault();
      scrollToId("features");
      return;
    }

    if (label.includes("start your journey today")) {
      event.preventDefault();
      navigate(AUTH_REGISTER_PATH);
      return;
    }

    if (label.includes("view documentation")) {
      event.preventDefault();
      scrollToId("journey") || scrollToId("features");
      return;
    }
  }

  if (!normalizeCurrentPath()) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        patchButtons(document);
      });
    } else {
      patchButtons(document);
    }

    var observer = new MutationObserver(function (mutations) {
      for (var index = 0; index < mutations.length; index += 1) {
        var mutation = mutations[index];
        for (var nodeIndex = 0; nodeIndex < mutation.addedNodes.length; nodeIndex += 1) {
          var node = mutation.addedNodes[nodeIndex];
          if (node instanceof Element) {
            if (node.matches && node.matches(CTA_SELECTOR)) {
              patchElement(node);
            }
            patchButtons(node);
          }
        }
      }
    });

    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  document.addEventListener("click", handleButtonClick, true);
})();
