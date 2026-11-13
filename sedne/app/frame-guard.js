// Refuses to run inside another site's frame (GitHub Pages can't send frame-ancestors / X-Frame-Options).
if (window.top !== window.self) {
  document.documentElement.style.display = "none";
  try { window.top.location.replace(window.self.location.href); } catch (e) { /* the frame keeps an empty page */ }
}
