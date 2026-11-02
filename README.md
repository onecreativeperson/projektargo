# linkedin-media (Projekt Argo)

Branch for LinkedIn post images of Štefan Toporcer / Projekt Argo. Not part of the website build – do not merge into `main`, do not delete.

- `li/render.py` – renders a 1080x1350 PNG in the projektargo.com design system (`python3 li/render.py spec.json`, spec format in the file header).
- `posts/` – published images, served via `https://raw.githubusercontent.com/onecreativeperson/projektargo/linkedin-media/posts/<file>.png`.

Used by the scheduled task "Argo LinkedIn agent".
