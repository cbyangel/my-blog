// 네온 액센트 색상 토글 (시안 ↔ 마젠타). 선택은 localStorage 에 저장한다.
// FOUC 방지를 위한 초기 반영은 <head> 인라인 스크립트가 담당한다.
(function () {
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  function currentAccent() {
    return root.getAttribute("data-accent") === "magenta" ? "magenta" : "cyan";
  }

  toggle.addEventListener("click", function () {
    var next = currentAccent() === "magenta" ? "cyan" : "magenta";
    root.setAttribute("data-accent", next);
    try {
      localStorage.setItem("accent", next);
    } catch (e) {}
  });
})();
