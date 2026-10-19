const menu = document.getElementById("menu");
const links = document.getElementById("links");
if (menu && links) {
  menu.addEventListener("click", () => links.classList.toggle("open"));
  links.querySelectorAll("a").forEach(a => a.addEventListener("click", () => links.classList.remove("open")));
}
