// Injects the animated heartbeat-line divider into any element with class "ecg-divider"
function ecgPath() {
  return `M0,14 H60 L72,14 L80,4 L92,24 L100,14 L110,14 L118,6 L126,22 L134,14 H600`;
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ecg-divider").forEach((el) => {
    el.innerHTML = `
      <svg viewBox="0 0 620 28" preserveAspectRatio="none">
        <path class="ecg-line" d="${ecgPath()}"></path>
      </svg>`;
  });
});
