const form = document.getElementById("puzzle-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const gridEl = document.getElementById("sudoku-grid");
const downloadLink = document.getElementById("download-link");
const generateBtn = document.getElementById("generate-btn");
const btnLabel = generateBtn.querySelector(".btn-label");
const btnSpinner = generateBtn.querySelector(".btn-spinner");
const difficultySelect = document.getElementById("difficulty");
const checkBtn = document.getElementById("check-btn");
const revealBtn = document.getElementById("reveal-btn");

let puzzleData = null;

async function runGenerate(difficulty, trigger) {
  generateBtn.disabled = true;
  btnLabel.textContent = "Generating…";
  btnSpinner.hidden = false;
  statusEl.textContent = "";
  resultEl.hidden = true;
  if (trigger) trigger.classList.add("loading");

  try {
    const resp = await fetch("/sudoku/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ difficulty }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.error || "Something went wrong.");
    }
    renderPuzzle(data);
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
  runGenerate(difficultySelect.value);
});

document.getElementById("sample-gallery").addEventListener("click", (e) => {
  const card = e.target.closest(".sample-card");
  if (!card) return;
  const { difficulty } = card.dataset;
  difficultySelect.value = difficulty;
  runGenerate(difficulty, card);
});

function cellInput(r, c) {
  return gridEl.querySelector(`input[data-row="${r}"][data-col="${c}"]`);
}

function focusCell(r, c) {
  if (r < 0 || r > 8 || c < 0 || c > 8) return;
  const input = cellInput(r, c);
  if (input) {
    input.focus();
  } else {
    // given cell has no input — just try the next editable cell in the same direction
  }
}

function renderPuzzle(data) {
  puzzleData = data;
  resultTitle.textContent = `Sudoku · ${data.difficulty}`;

  gridEl.innerHTML = "";
  for (let r = 0; r < 9; r++) {
    const tr = document.createElement("tr");
    for (let c = 0; c < 9; c++) {
      const td = document.createElement("td");
      td.className = "sk-cell";
      if ((c + 1) % 3 === 0 && c !== 8) td.classList.add("box-right");
      if ((r + 1) % 3 === 0 && r !== 8) td.classList.add("box-bottom");

      const given = data.puzzle[r][c];
      if (given) {
        td.classList.add("given");
        td.textContent = given;
      } else {
        const input = document.createElement("input");
        input.type = "text";
        input.inputMode = "numeric";
        input.maxLength = 1;
        input.autocomplete = "off";
        input.className = "sk-input";
        input.dataset.row = r;
        input.dataset.col = c;
        input.addEventListener("input", () => {
          input.value = input.value.replace(/[^1-9]/g, "").slice(-1);
          td.classList.remove("correct", "incorrect");
        });
        input.addEventListener("keydown", (e) => {
          switch (e.key) {
            case "ArrowRight": e.preventDefault(); focusCell(r, c + 1); break;
            case "ArrowLeft": e.preventDefault(); focusCell(r, c - 1); break;
            case "ArrowDown": e.preventDefault(); focusCell(r + 1, c); break;
            case "ArrowUp": e.preventDefault(); focusCell(r - 1, c); break;
          }
        });
        td.appendChild(input);
      }
      tr.appendChild(td);
    }
    gridEl.appendChild(tr);
  }

  downloadLink.href = `/sudoku/download/${data.puzzle_id}.pdf`;
  resultEl.hidden = false;
}

checkBtn.addEventListener("click", () => {
  if (!puzzleData) return;
  gridEl.querySelectorAll(".sk-input").forEach((input) => {
    const r = Number(input.dataset.row);
    const c = Number(input.dataset.col);
    const td = input.closest("td");
    td.classList.remove("correct", "incorrect");
    const guess = input.value.trim();
    if (!guess) return;
    td.classList.add(Number(guess) === puzzleData.solution[r][c] ? "correct" : "incorrect");
  });
});

revealBtn.addEventListener("click", () => {
  if (!puzzleData) return;
  gridEl.querySelectorAll(".sk-input").forEach((input) => {
    const r = Number(input.dataset.row);
    const c = Number(input.dataset.col);
    const td = input.closest("td");
    input.value = puzzleData.solution[r][c];
    td.classList.remove("incorrect");
    td.classList.add("correct");
  });
});
