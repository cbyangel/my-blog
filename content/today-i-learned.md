---
title: 오늘 배운 것
date: 2026-07-09
tags: [개발, 일상]
description: 클로드 코드로 블로그를 만들며 배운 HTML, CSS, JavaScript의 역할을 정리했습니다.
---

오늘 클로드 코드(Claude Code)와 함께 이 블로그를 직접 만들어 봤습니다. 프레임워크 없이 순수 **HTML, CSS, JavaScript**만으로 웹사이트가 어떻게 굴러가는지 몸으로 이해하게 됐는데, 셋의 역할이 생각보다 딱 나뉘어 있어서 정리해 둡니다.

## HTML — 뼈대(구조)

HTML은 페이지에 **무엇이 있는지**를 정합니다. 제목, 문단, 목록, 링크 같은 내용의 구조를 담당하죠.

```html
<article>
  <h1>오늘 배운 것</h1>
  <p>블로그를 직접 만들어 봤다.</p>
</article>
```

`<article>`, `<header>`, `<nav>` 같은 **시맨틱 태그**를 쓰면 사람뿐 아니라 브라우저와 검색엔진도 구조를 이해할 수 있다는 걸 배웠습니다. 색이나 위치는 HTML이 신경 쓰지 않습니다. 오직 "무엇"만 다룹니다.

## CSS — 겉모습(표현)

CSS는 그 뼈대를 **어떻게 보이게 할지**를 정합니다. 색상, 글꼴, 여백, 배치, 반응형 레이아웃이 모두 CSS의 몫입니다.

이번에 가장 인상 깊었던 건 **CSS 변수(커스텀 프로퍼티)** 였습니다. 색을 변수 하나로 관리하니 다크 모드 전환이 놀랍도록 간단해졌습니다.

```css
:root {
  --color-bg: #ffffff;
  --color-text: #1f2328;
}

:root[data-theme="dark"] {
  --color-bg: #0f1115;
  --color-text: #e6e9ee;
}
```

`--color-bg` 값 하나만 바꾸면 그 변수를 쓰는 사이트 전체가 한 번에 바뀝니다. 또 `@media` 쿼리로 화면 크기에 따라 스타일을 달리 줘서 **모바일 대응**도 CSS만으로 해결했습니다.

## JavaScript — 동작(상호작용)

JavaScript는 페이지가 **사용자와 상호작용**하게 만듭니다. 클릭에 반응하고, 값을 기억하고, 내용을 바꾸는 일이죠.

다크 모드 토글 버튼이 좋은 예였습니다. 버튼을 누르면 JS가 테마를 바꾸고, 그 선택을 `localStorage`에 저장해 다음 방문 때도 유지합니다.

```javascript
toggle.addEventListener("click", function () {
  var next = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
});
```

재미있던 점은, JS가 직접 색을 칠하는 게 아니라 `data-theme` 속성만 바꾼다는 것이었습니다. **실제 색 변경은 CSS가 처리**하죠. 각자 자기 일만 합니다.

## 정리

> **HTML은 뼈대, CSS는 겉모습, JavaScript는 동작.**

셋의 경계를 흐리지 않고 각자 역할에 충실하게 두는 것이 깔끔한 코드의 핵심이라는 걸 배웠습니다. 프레임워크가 이 셋을 감싸주는 편리한 도구일 뿐, 근본은 결국 이 세 가지라는 감이 이제야 좀 잡히네요.

내일은 또 뭘 배우게 될까요?
