(function () {
  "use strict";

  var SIZE = 4;
  var WIN_VALUE = 2048;
  var BEST_KEY = "bestScore-2048";
  var SWIPE_THRESHOLD = 24;

  // ---------- 상태 ----------
  var grid = [];        // 4x4, 빈 칸은 0
  var score = 0;
  var bestScore = 0;
  var won = false;      // 2048 도달 후 계속하기 확인 여부
  var over = false;

  // ---------- DOM ----------
  var gridContainer = document.getElementById("grid-container");
  var gridBg = document.querySelector(".grid-bg");
  var tileLayer = document.getElementById("tile-layer");
  var scoreEl = document.getElementById("score");
  var bestEl = document.getElementById("best");
  var overlay = document.getElementById("overlay");
  var overlayMsg = document.getElementById("overlay-msg");
  var overlayActions = document.getElementById("overlay-actions");
  var newGameBtn = document.getElementById("new-game");

  // 병합 애니메이션 표시용: "row,col" 집합
  var mergedCells = {};

  // ---------- 초기화 ----------
  function buildBackground() {
    var frag = document.createDocumentFragment();
    for (var i = 0; i < SIZE * SIZE; i++) {
      var cell = document.createElement("div");
      cell.className = "cell";
      frag.appendChild(cell);
    }
    gridBg.appendChild(frag);
  }

  function emptyGrid() {
    var g = [];
    for (var r = 0; r < SIZE; r++) {
      g.push([0, 0, 0, 0]);
    }
    return g;
  }

  function loadBest() {
    try {
      var v = window.localStorage.getItem(BEST_KEY);
      bestScore = v ? parseInt(v, 10) || 0 : 0;
    } catch (e) {
      bestScore = 0;
    }
  }

  function saveBest() {
    try {
      window.localStorage.setItem(BEST_KEY, String(bestScore));
    } catch (e) { /* localStorage 불가 환경 무시 */ }
  }

  function newGame() {
    grid = emptyGrid();
    score = 0;
    won = false;
    over = false;
    mergedCells = {};
    spawnTile();
    spawnTile();
    hideOverlay();
    render();
  }

  // ---------- 타일 생성 ----------
  function emptyCells() {
    var cells = [];
    for (var r = 0; r < SIZE; r++) {
      for (var c = 0; c < SIZE; c++) {
        if (grid[r][c] === 0) cells.push([r, c]);
      }
    }
    return cells;
  }

  function spawnTile() {
    var cells = emptyCells();
    if (cells.length === 0) return;
    var pick = cells[Math.floor(Math.random() * cells.length)];
    grid[pick[0]][pick[1]] = Math.random() < 0.9 ? 2 : 4;
  }

  // ---------- 이동/병합 ----------
  // 한 행을 왼쪽으로 밀고 병합. { row, gained, merges } 반환
  function slideRow(row) {
    var vals = row.filter(function (v) { return v !== 0; });
    var result = [];
    var gained = 0;
    var merges = []; // 병합이 발생한 결과 인덱스
    for (var i = 0; i < vals.length; i++) {
      if (i + 1 < vals.length && vals[i] === vals[i + 1]) {
        var merged = vals[i] * 2;
        result.push(merged);
        gained += merged;
        merges.push(result.length - 1);
        if (merged === WIN_VALUE) won = won || "reached";
        i++; // 다음 값 건너뛰기 (이중 병합 방지)
      } else {
        result.push(vals[i]);
      }
    }
    while (result.length < SIZE) result.push(0);
    return { row: result, gained: gained, merges: merges };
  }

  function transpose(g) {
    var t = emptyGrid();
    for (var r = 0; r < SIZE; r++) {
      for (var c = 0; c < SIZE; c++) {
        t[c][r] = g[r][c];
      }
    }
    return t;
  }

  function reverseRows(g) {
    return g.map(function (row) { return row.slice().reverse(); });
  }

  function cloneGrid(g) {
    return g.map(function (row) { return row.slice(); });
  }

  function gridsEqual(a, b) {
    for (var r = 0; r < SIZE; r++) {
      for (var c = 0; c < SIZE; c++) {
        if (a[r][c] !== b[r][c]) return false;
      }
    }
    return true;
  }

  // 모든 방향을 "왼쪽 밀기"로 정규화
  // dir: "left" | "right" | "up" | "down"
  function move(dir) {
    if (over) return;

    var before = cloneGrid(grid);
    var working = grid;

    // 왼쪽 기준으로 변환
    if (dir === "right") {
      working = reverseRows(working);
    } else if (dir === "up") {
      working = transpose(working);
    } else if (dir === "down") {
      working = reverseRows(transpose(working));
    }

    var gained = 0;
    var newMerged = {}; // 변환 좌표계 기준 병합 위치
    var slid = working.map(function (row, r) {
      var res = slideRow(row);
      gained += res.gained;
      res.merges.forEach(function (c) {
        newMerged[r + "," + c] = true;
      });
      return res.row;
    });

    // 역변환하여 원래 방향으로 복원
    var restored = slid;
    var restoredMerged = {};
    function mapMerged(mapFn) {
      Object.keys(newMerged).forEach(function (key) {
        var parts = key.split(",");
        var m = mapFn(parseInt(parts[0], 10), parseInt(parts[1], 10));
        restoredMerged[m[0] + "," + m[1]] = true;
      });
    }

    if (dir === "right") {
      restored = reverseRows(slid);
      mapMerged(function (r, c) { return [r, SIZE - 1 - c]; });
    } else if (dir === "up") {
      restored = transpose(slid);
      mapMerged(function (r, c) { return [c, r]; });
    } else if (dir === "down") {
      restored = transpose(reverseRows(slid));
      mapMerged(function (r, c) { return [SIZE - 1 - c, r]; });
    } else {
      // left
      Object.keys(newMerged).forEach(function (k) { restoredMerged[k] = true; });
    }

    grid = restored;

    if (gridsEqual(before, grid)) {
      return; // 실제 이동 없음 → 타일 생성 안 함
    }

    // 점수 반영
    score += gained;
    if (score > bestScore) {
      bestScore = score;
      saveBest();
    }

    mergedCells = restoredMerged;
    spawnTile();
    render();

    // 승리 판정
    if (won === "reached") {
      won = "shown";
      showWin();
      return;
    }

    // 게임오버 판정
    if (!canMove()) {
      over = true;
      showGameOver();
    }
  }

  function canMove() {
    // 빈 칸 있으면 이동 가능
    for (var r = 0; r < SIZE; r++) {
      for (var c = 0; c < SIZE; c++) {
        if (grid[r][c] === 0) return true;
      }
    }
    // 인접 동일 값 있으면 이동 가능
    for (var r2 = 0; r2 < SIZE; r2++) {
      for (var c2 = 0; c2 < SIZE; c2++) {
        var v = grid[r2][c2];
        if (c2 + 1 < SIZE && grid[r2][c2 + 1] === v) return true;
        if (r2 + 1 < SIZE && grid[r2 + 1][c2] === v) return true;
      }
    }
    return false;
  }

  // ---------- 렌더링 ----------
  function render() {
    // 타일 재구성 (그리드 배치로 위치 지정)
    tileLayer.innerHTML = "";
    var frag = document.createDocumentFragment();
    for (var r = 0; r < SIZE; r++) {
      for (var c = 0; c < SIZE; c++) {
        var v = grid[r][c];
        if (v === 0) continue;
        var tile = document.createElement("div");
        tile.className = "tile";
        tile.setAttribute("data-value", String(v));
        if (v > WIN_VALUE) tile.classList.add("super");
        if (mergedCells[r + "," + c]) tile.classList.add("merged");
        tile.style.gridRowStart = String(r + 1);
        tile.style.gridColumnStart = String(c + 1);
        tile.setAttribute("role", "gridcell");
        tile.textContent = String(v);
        frag.appendChild(tile);
      }
    }
    tileLayer.appendChild(frag);
    mergedCells = {};

    scoreEl.textContent = String(score);
    bestEl.textContent = String(bestScore);
  }

  // ---------- 오버레이 ----------
  function hideOverlay() {
    overlay.hidden = true;
    overlay.classList.remove("win");
    overlayActions.innerHTML = "";
  }

  function makeBtn(label, onClick) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.addEventListener("click", onClick);
    return b;
  }

  function showWin() {
    overlay.hidden = false;
    overlay.classList.add("win");
    overlayMsg.textContent = "You win!";
    overlayActions.innerHTML = "";
    overlayActions.appendChild(makeBtn("계속하기", function () {
      hideOverlay(); // won === "shown" 상태 유지 → 다시 안 뜸
    }));
    overlayActions.appendChild(makeBtn("New Game", newGame));
  }

  function showGameOver() {
    overlay.hidden = false;
    overlay.classList.remove("win");
    overlayMsg.textContent = "Game over!";
    overlayActions.innerHTML = "";
    overlayActions.appendChild(makeBtn("New Game", newGame));
  }

  // ---------- 입력: 키보드 ----------
  var KEY_MAP = {
    ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down",
    a: "left", d: "right", w: "up", s: "down",
    A: "left", D: "right", W: "up", S: "down"
  };

  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var dir = KEY_MAP[e.key];
    if (!dir) return;
    e.preventDefault();
    move(dir);
  });

  // ---------- 입력: 터치 스와이프 ----------
  var touchStartX = 0, touchStartY = 0, touching = false;

  gridContainer.addEventListener("touchstart", function (e) {
    if (e.touches.length !== 1) return;
    touching = true;
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  gridContainer.addEventListener("touchmove", function (e) {
    if (touching) e.preventDefault(); // 스크롤 억제
  }, { passive: false });

  gridContainer.addEventListener("touchend", function (e) {
    if (!touching) return;
    touching = false;
    var t = e.changedTouches[0];
    var dx = t.clientX - touchStartX;
    var dy = t.clientY - touchStartY;
    var absX = Math.abs(dx), absY = Math.abs(dy);
    if (Math.max(absX, absY) < SWIPE_THRESHOLD) return;
    if (absX > absY) {
      move(dx > 0 ? "right" : "left");
    } else {
      move(dy > 0 ? "down" : "up");
    }
  }, { passive: true });

  // ---------- 버튼 ----------
  newGameBtn.addEventListener("click", newGame);

  // ---------- 시작 ----------
  buildBackground();
  loadBest();
  newGame();
})();
