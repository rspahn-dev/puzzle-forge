const form = document.getElementById("batch-form");
const gameTypeSelect = document.getElementById("game-type");
const statusEl = document.getElementById("status");
const skippedNote = document.getElementById("skipped-note");
const generateBtn = document.getElementById("generate-btn");
const btnLabel = generateBtn.querySelector(".btn-label");
const btnSpinner = generateBtn.querySelector(".btn-spinner");

function syncFieldVisibility() {
  const gameType = gameTypeSelect.value;
  document.querySelectorAll("[data-game-fields]").forEach((el) => {
    const types = el.dataset.gameFields.split(",");
    el.classList.toggle("active", types.includes(gameType));
  });
}

gameTypeSelect.addEventListener("change", syncFieldVisibility);
syncFieldVisibility();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const gameType = gameTypeSelect.value;

  const payload = { game_type: gameType };
  if (gameType === "sudoku") {
    payload.difficulty = document.getElementById("difficulty").value;
    payload.count = document.getElementById("sudoku-count").value;
  } else {
    payload.themes = document.getElementById("themes").value.split("\n");
    payload.size = document.getElementById("size").value;
    payload.count = document.getElementById("count").value;
    payload.per_theme = document.getElementById("per-theme").value;
  }

  generateBtn.disabled = true;
  btnLabel.textContent = "Generating…";
  btnSpinner.hidden = false;
  statusEl.textContent = "This can take a little while for several puzzles…";
  skippedNote.hidden = true;

  try {
    const resp = await fetch("/batch/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.error || "Something went wrong.");
    }

    const skipped = resp.headers.get("X-Batch-Skipped");
    if (skipped) {
      skippedNote.hidden = false;
      skippedNote.textContent = `Couldn't build a puzzle for: ${skipped} (skipped)`;
    }

    const blob = await resp.blob();
    const disposition = resp.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `${gameType}_batch.pdf`;

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    statusEl.textContent = "Done — your PDF download should start automatically.";
  } catch (err) {
    statusEl.textContent = err.message;
  } finally {
    generateBtn.disabled = false;
    btnLabel.textContent = "📚 Generate book PDF";
    btnSpinner.hidden = true;
  }
});
