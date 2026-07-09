// 다크/라이트 테마 토글. 선택은 localStorage 에 저장한다.
// FOUC 방지를 위한 초기 반영은 <head> 인라인 스크립트가 담당한다.
(function () {
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  function currentTheme() {
    // 명시적으로 설정된 값이 있으면 그것을, 없으면 시스템 설정을 따른다.
    var explicit = root.getAttribute("data-theme");
    if (explicit) return explicit;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  toggle.addEventListener("click", function () {
    var next = currentTheme() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch (e) {}
  });
})();
