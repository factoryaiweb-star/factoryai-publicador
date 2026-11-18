"""Renueva el token de Instagram (dura 60 días; se renueva cada mes) y lo deja en la salida para el workflow."""
import json, os, sys, urllib.parse, urllib.request
tok = os.environ["IG_TOKEN"]
url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": tok})
with urllib.request.urlopen(url, timeout=60) as r:
    d = json.loads(r.read())
nuevo = d["access_token"]
print(f"::add-mask::{nuevo}")
print(f"Token renovado; vence en {int(d.get('expires_in', 0))//86400} días")
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"token={nuevo}\n")
