// Before the app starts: turns the addresses GitHub Pages can answer into the app's own address.
//  /sedne/app/?r=/profile – the site's 404 page sent an unknown /sedne/app/… address here (a reload, an older link);
//  /sedne/app/vote/?id=<id> – a poll link (vote/index.html is a real file, so it answers 200).
(function () {
  var base = "/sedne/app";
  var path = location.pathname, q = new URLSearchParams(location.search), to = null;
  var r = q.get("r");
  if (r !== null && path === base + "/") {
    to = /^\/[A-Za-z0-9._~%\/-]*(\?[A-Za-z0-9._~%=&+-]*)?$/.test(r) && !/\/\/|\.\./.test(r) ? base + r : base + "/";
  }
  var id = q.get("id");
  if (to === null && id !== null && path === base + "/vote/" && /^[A-Za-z0-9_-]{1,64}$/.test(id)) to = base + "/vote/" + id;
  if (to !== null) history.replaceState(history.state, "", to + location.hash);
})();
