const form = document.getElementById("puzzle-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const sourceNote = document.getElementById("source-note");
const gridEl = document.getElementById("grid");
const wordListEl = document.getElementById("word-list");
const skippedNote = document.getElementById("skipped-note");
const downloadLink = document.getElementById("download-link");
const generateBtn = document.getElementById("generate-btn");
const btnLabel = generateBtn.querySelector(".btn-label");
const btnSpinner = generateBtn.querySelector(".btn-spinner");
const themeInput = document.getElementById("theme");
const sizeSelect = document.getElementById("size");
const countSelect = document.getElementById("count");

async function runGenerate(theme, size, count, trigger) {
  generateBtn.disabled = true;
  btnLabel.textContent = "Generating…";
  btnSpinner.hidden = false;
  statusEl.textContent = "";
  resultEl.hidden = true;
  if (trigger) trigger.classList.add("loading");

  try {
    const resp = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme, size, count }),
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
  runGenerate(themeInput.value.trim(), sizeSelect.value, countSelect.value);
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
  const { theme, size, count } = card.dataset;
  themeInput.value = theme;
  sizeSelect.value = size;
  countSelect.value = count;
  runGenerate(theme, size, count, card);
});

function renderPuzzle(theme, data) {
  resultTitle.textContent = `"${theme}" word search`;

  if (data.source === "offline") {
    sourceNote.hidden = false;
    sourceNote.textContent = "Using the built-in word bank (no API key configured) — add ANTHROPIC_API_KEY to .env for AI-generated word lists on any theme.";
  } else {
    sourceNote.hidden = true;
  }

  gridEl.innerHTML = "";
  for (const row of data.grid) {
    const tr = document.createElement("tr");
    for (const letter of row) {
      const td = document.createElement("td");
      td.textContent = letter;
      tr.appendChild(td);
    }
    gridEl.appendChild(tr);
  }

  wordListEl.innerHTML = "";
  for (const word of data.words) {
    const li = document.createElement("li");
    li.textContent = word;
    li.addEventListener("click", () => li.classList.toggle("found"));
    wordListEl.appendChild(li);
  }

  if (data.skipped && data.skipped.length) {
    skippedNote.hidden = false;
    skippedNote.textContent = `Couldn't fit: ${data.skipped.join(", ")} (try a bigger grid)`;
  } else {
    skippedNote.hidden = true;
  }

  downloadLink.href = `/download/${data.puzzle_id}.pdf`;
  resultEl.hidden = false;
}
