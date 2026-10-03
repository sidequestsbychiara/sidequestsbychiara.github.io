document.addEventListener("DOMContentLoaded", () => {
  const year = document.querySelector("#year");
  if (year) year.textContent = new Date().getFullYear();

  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".main-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  document.querySelectorAll(".notes-button").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.notes;
      const notes = document.getElementById(targetId);
      if (!notes) return;

      notes.classList.toggle("open");
      button.textContent = notes.classList.contains("open")
        ? "hide notes"
        : "dev notes";
    });
  });

  // Optional rotating "now playing" flavor text.
  // Replace these with real songs, books, videos, or whatever you want.
  const media = [
    ["song that altered my brain chemistry", "artist name • 03:47"],
    ["book I will defend too aggressively", "currently reading • page ???"],
    ["playlist with unnecessary lore", "37 tracks • emotionally avoidant"],
  ];

  const title = document.querySelector("#now-playing-title");
  const subtitle = document.querySelector("#now-playing-subtitle");

  if (title && subtitle) {
    let i = 0;
    setInterval(() => {
      i = (i + 1) % media.length;
      title.textContent = media[i][0];
      subtitle.textContent = media[i][1];
    }, 4500);
  }
});
