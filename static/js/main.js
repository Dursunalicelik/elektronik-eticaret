document.querySelectorAll(".flash").forEach((item) => {
  setTimeout(() => item.classList.add("flash-hide"), 4500);
});
