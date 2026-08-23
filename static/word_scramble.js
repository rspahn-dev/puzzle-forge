const form = document.getElementById("puzzle-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const sourceNote = document.getElementById("source-note");
const scrambleListEl = document.getElementById("scramble-list");
const downloadLink = document.getElementById("download-link");
const generateBtn = document.getElementById("generate-btn");
const btnLabel = generateBtn.querySelector(".btn-label");
const btnSpinner = generateBtn.querySelector(".btn-spinner");
const themeInput = document.getElementById("theme");
const difficultySelect = document.getElementById("difficulty");
const countSelect = document.getElementById("count");
const checkBtn = document.getElementById("check-btn");
const revealBtn = document.getElementById("reveal-btn");

async function runGenerate(theme, minLen, maxLen, count, trigger) {
  generateBtn.disabled = true;
  btnLabel.textContent = "Generating…";
  btnSpinner.hidden = false;
  statusEl.textContent = "";
  resultEl.hidden = true;
  if (trigger) trigger.classList.add("loading");

  try {
    const resp = await fetch("/word-scramble/generate", {
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

function renderPuzzle(theme, data) {
  resultTitle.textContent = `"${theme}" word scramble`;

  if (data.source === "offline") {
    sourceNote.hidden = false;
    sourceNote.textContent = "Using the built-in word bank (no API key configured) — add ANTHROPIC_API_KEY to .env for AI-generated word lists on any theme.";
  } else {
    sourceNote.hidden = true;
  }

  scrambleListEl.innerHTML = "";
  for (const item of data.items) {
    const li = document.createElement("li");
    li.className = "scramble-item";
    li.dataset.answer = item.answer;

    const word = document.createElement("span");
    word.className = "scramble-word";
    word.textContent = item.scrambled;

    const input = document.createElement("input");
    input.type = "text";
    input.maxLength = item.length;
    input.autocomplete = "off";
    input.className = "scramble-input";
    input.addEventListener("input", () => li.classList.remove("correct", "incorrect"));

    li.appendChild(word);
    li.appendChild(input);
    scrambleListEl.appendChild(li);
  }

  downloadLink.href = `/word-scramble/download/${data.puzzle_id}.pdf`;
  resultEl.hidden = false;
}

checkBtn.addEventListener("click", () => {
  for (const li of scrambleListEl.children) {
    const input = li.querySelector(".scramble-input");
    const guess = input.value.trim().toUpperCase();
    li.classList.remove("correct", "incorrect");
    if (!guess) continue;
    li.classList.add(guess === li.dataset.answer ? "correct" : "incorrect");
  }
});

revealBtn.addEventListener("click", () => {
  for (const li of scrambleListEl.children) {
    const input = li.querySelector(".scramble-input");
    input.value = li.dataset.answer;
    li.classList.remove("incorrect");
    li.classList.add("correct");
  }
});
