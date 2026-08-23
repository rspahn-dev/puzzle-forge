const form = document.getElementById("puzzle-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const sourceNote = document.getElementById("source-note");
const gridEl = document.getElementById("crossword-grid");
const acrossListEl = document.getElementById("across-list");
const downListEl = document.getElementById("down-list");
const skippedNote = document.getElementById("skipped-note");
const downloadLink = document.getElementById("download-link");
const generateBtn = document.getElementById("generate-btn");
const btnLabel = generateBtn.querySelector(".btn-label");
const btnSpinner = generateBtn.querySelector(".btn-spinner");
const themeInput = document.getElementById("theme");
const difficultySelect = document.getElementById("difficulty");
const countSelect = document.getElementById("count");
const checkBtn = document.getElementById("check-btn");
const revealBtn = document.getElementById("reveal-btn");

let puzzleData = null;
let acrossMap = {};
let downMap = {};
let currentDirection = "across";

async function runGenerate(theme, minLen, maxLen, count, trigger) {
  generateBtn.disabled = true;
  btnLabel.textContent = "Generating…";
  btnSpinner.hidden = false;
  statusEl.textContent = "";
  resultEl.hidden = true;
  if (trigger) trigger.classList.add("loading");

  try {
    const resp = await fetch("/crossword/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme, min_len: minLen, max_len: maxLen, count }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.error || "Something went wrong.");
    }
    renderPuzzle(theme, data);
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    statusEl.textContent = err.message;
  } finally {
    generateBtn.disabled = false;
    btnLabel.textContent = "✨ Generate puzzle";
    btnSpinner.hidden = true;
    if (trigger) trigger.classList.remove("loading");
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const [minLen, maxLen] = difficultySelect.value.split(",");
  runGenerate(themeInput.value.trim(), minLen, maxLen, countSelect.value);
});

document.getElementById("theme-chips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  themeInput.value = chip.dataset.theme;
  themeInput.focus();
});

document.getElementById("sample-gallery").addEventListener("click", (e) => {
  const card = e.target.closest(".sample-card");
  if (!card) return;
  const { theme, min, max, count } = card.dataset;
  themeInput.value = theme;
  runGenerate(theme, min, max, count, card);
});

function buildWordMaps(data) {
  const across = {};
  const down = {};
  for (const e of data.across) {
    for (let i = 0; i < e.length; i++) across[`${e.row},${e.col + i}`] = e;
  }
  for (const e of data.down) {
    for (let i = 0; i < e.length; i++) down[`${e.row + i},${e.col}`] = e;
  }
  return { across, down };
}

function cellInput(r, c) {
  return gridEl.querySelector(`input[data-row="${r}"][data-col="${c}"]`);
}

function clearActive() {
  gridEl.querySelectorAll(".xw-cell.active").forEach((td) => td.classList.remove("active"));
  acrossListEl.querySelectorAll("li.active").forEach((li) => li.classList.remove("active"));
  downListEl.querySelectorAll("li.active").forEach((li) => li.classList.remove("active"));
}

function highlightWord(r, c, direction) {
  const entry = direction === "across" ? acrossMap[`${r},${c}`] : downMap[`${r},${c}`];
  if (!entry) return null;
  clearActive();
  for (let i = 0; i < entry.length; i++) {
    const rr = direction === "across" ? entry.row : entry.row + i;
    const cc = direction === "across" ? entry.col + i : entry.col;
    const input = cellInput(rr, cc);
    if (input) input.closest("td").classList.add("active");
  }
  const list = direction === "across" ? acrossListEl : downListEl;
  const li = list.querySelector(`li[data-number="${entry.number}"]`);
  if (li) li.classList.add("active");
  return entry;
}

function focusCell(r, c, direction) {
  const input = cellInput(r, c);
  if (!input) return;
  const key = `${r},${c}`;
  let dir = direction || currentDirection;
  if (dir === "across" && !acrossMap[key]) dir = "down";
  if (dir === "down" && !downMap[key]) dir = "across";
  currentDirection = dir;
  input.focus();
  highlightWord(r, c, dir);
}

function renderPuzzle(theme, data) {
  puzzleData = data;
  const maps = buildWordMaps(data);
  acrossMap = maps.across;
  downMap = maps.down;
  currentDirection = "across";

  resultTitle.textContent = `"${theme}" crossword`;

  if (data.source === "offline") {
    sourceNote.hidden = false;
    sourceNote.textContent = "Using the built-in word bank and generic clues (no API key configured) — add ANTHROPIC_API_KEY to .env for AI-generated word lists and clues on any theme.";
  } else {
    sourceNote.hidden = true;
  }

  gridEl.innerHTML = "";
  for (let r = 0; r < data.rows; r++) {
    const tr = document.createElement("tr");
    for (let c = 0; c < data.cols; c++) {
      const td = document.createElement("td");
      td.className = "xw-cell";
      if (!data.blocks[r][c]) {
        td.classList.add("xw-block");
        tr.appendChild(td);
        continue;
      }
      const number = data.numbers[`${r},${c}`];
      if (number) {
        const numSpan = document.createElement("span");
        numSpan.className = "xw-number";
        numSpan.textContent = number;
        td.appendChild(numSpan);
      }
      const input = document.createElement("input");
      input.type = "text";
      input.maxLength = 1;
      input.autocomplete = "off";
      input.className = "xw-input";
      input.dataset.row = r;
      input.dataset.col = c;
      input.addEventListener("focus", () => focusCell(r, c));
      input.addEventListener("click", () => {
        if (document.activeElement === input) {
          const other = currentDirection === "across" ? "down" : "across";
          const key = `${r},${c}`;
          const otherMap = other === "across" ? acrossMap : downMap;
          if (otherMap[key]) focusCell(r, c, other);
        }
      });
      input.addEventListener("input", () => {
        input.value = input.value.toUpperCase().replace(/[^A-Z]/g, "");
        input.closest("td").classList.remove("correct", "incorrect");
        if (input.value) moveCursor(r, c, currentDirection, 1);
      });
      input.addEventListener("keydown", (e) => handleKeydown(e, r, c));
      td.appendChild(input);
      tr.appendChild(td);
    }
    gridEl.appendChild(tr);
  }

  acrossListEl.innerHTML = "";
  for (const e of data.across) {
    const li = document.createElement("li");
    li.dataset.number = e.number;
    li.textContent = `${e.number}. ${e.clue}`;
    li.addEventListener("click", () => focusCell(e.row, e.col, "across"));
    acrossListEl.appendChild(li);
  }

  downListEl.innerHTML = "";
  for (const e of data.down) {
    const li = document.createElement("li");
    li.dataset.number = e.number;
    li.textContent = `${e.number}. ${e.clue}`;
    li.addEventListener("click", () => focusCell(e.row, e.col, "down"));
    downListEl.appendChild(li);
  }

  if (data.skipped && data.skipped.length) {
    skippedNote.hidden = false;
    skippedNote.textContent = `Couldn't fit: ${data.skipped.join(", ")}`;
  } else {
    skippedNote.hidden = true;
  }

  downloadLink.href = `/crossword/download/${data.puzzle_id}.pdf`;
  resultEl.hidden = false;
}

function moveCursor(r, c, direction, delta) {
  const dr = direction === "down" ? delta : 0;
  const dc = direction === "across" ? delta : 0;
  const next = cellInput(r + dr, c + dc);
  if (next) {
    next.focus();
    highlightWord(r + dr, c + dc, direction);
  }
}

function handleKeydown(e, r, c) {
  switch (e.key) {
    case "ArrowRight":
      e.preventDefault();
      focusCell(r, c + 1, "across");
      break;
    case "ArrowLeft":
      e.preventDefault();
      focusCell(r, c - 1, "across");
      break;
    case "ArrowDown":
      e.preventDefault();
      focusCell(r + 1, c, "down");
      break;
    case "ArrowUp":
      e.preventDefault();
      focusCell(r - 1, c, "down");
      break;
    case "Backspace":
      if (!e.target.value) {
        e.preventDefault();
        moveCursor(r, c, currentDirection, -1);
        const prev = document.activeElement;
        if (prev && prev.tagName === "INPUT") prev.value = "";
      }
      break;
  }
}

checkBtn.addEventListener("click", () => {
  if (!puzzleData) return;
  gridEl.querySelectorAll(".xw-input").forEach((input) => {
    const r = Number(input.dataset.row);
    const c = Number(input.dataset.col);
    const td = input.closest("td");
    td.classList.remove("correct", "incorrect");
    const guess = input.value.trim().toUpperCase();
    if (!guess) return;
    td.classList.add(guess === puzzleData.solution[r][c] ? "correct" : "incorrect");
  });
});

revealBtn.addEventListener("click", () => {
  if (!puzzleData) return;
  gridEl.querySelectorAll(".xw-input").forEach((input) => {
    const r = Number(input.dataset.row);
    const c = Number(input.dataset.col);
    const td = input.closest("td");
    input.value = puzzleData.solution[r][c];
    td.classList.remove("incorrect");
    td.classList.add("correct");
  });
});
