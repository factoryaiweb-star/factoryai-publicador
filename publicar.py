"""Publicador propio de Factory AI Web (reemplazo gratuito de Metricool para Instagram).

Lee `calendario.csv`, y cada publicación con estado `programado` cuya hora ya llegó
la publica en Instagram con la API oficial (Instagram API with Instagram Login).

Variables de entorno (GitHub Actions → Settings → Secrets and variables → Actions):
  IG_USER_ID       ID de la cuenta profesional de Instagram (secreto)
  IG_TOKEN         token de acceso de larga duración (secreto; nunca en el chat ni en el repo)
  PUBLIC_BASE_URL  URL pública donde se sirven los archivos, p. ej.
                   https://<usuario>.github.io/<repo>/   (variable, no secreta)
  API_VERSION      opcional, por defecto v24.0

Uso:
  python publicar.py            publica lo que ya toca
  python publicar.py --dry      solo muestra qué publicaría (no llama a Instagram)
  python publicar.py --check    revisa token, cuenta y cupo diario
"""
import csv, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Santiago")
CAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendario.csv")
TEXTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textos")
API = f"https://graph.instagram.com/{os.environ.get('API_VERSION', 'v24.0')}"
COLS = ["id", "fecha_hora", "tipo", "archivos", "portada", "texto", "estado", "ig_media_id", "publicado_en", "nota"]
MAX_ATRASO = timedelta(hours=12)  # si se pasó más de esto, no publica y lo marca «atrasado»


def env(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"Falta la variable {name}")
    return v


def call(method, path, params=None):
    params = dict(params or {})
    params["access_token"] = env("IG_TOKEN")
    url = f"{API}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:300]
        raise RuntimeError(f"HTTP {e.code}: {msg}") from None


def url_de(nombre):
    base = env("PUBLIC_BASE_URL").rstrip("/") + "/"
    return base + "media/" + urllib.parse.quote(nombre.strip())


def es_video(nombre):
    return nombre.lower().endswith((".mp4", ".mov"))


def esperar_listo(container_id, max_seg=600):
    t0 = time.time()
    while time.time() - t0 < max_seg:
        st = call("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram rechazó el archivo: {st.get('status')}")
        time.sleep(8)
    raise RuntimeError("Instagram tardó demasiado en procesar el video")


def crear_contenedor(fila, texto):
    ig = env("IG_USER_ID")
    tipo = fila["tipo"].strip().upper()
    archivos = [a for a in fila["archivos"].split("|") if a.strip()]
    if not archivos:
        raise RuntimeError("La fila no tiene archivos")

    if tipo == "REEL":
        p = {"media_type": "REELS", "video_url": url_de(archivos[0]), "caption": texto, "share_to_feed": "true"}
        if fila.get("portada", "").strip():
            p["cover_url"] = url_de(fila["portada"])
        c = call("POST", f"{ig}/media", p)["id"]
        esperar_listo(c)
        return c

    if tipo == "HISTORIA":
        a = archivos[0]
        p = {"media_type": "STORIES", ("video_url" if es_video(a) else "image_url"): url_de(a)}
        c = call("POST", f"{ig}/media", p)["id"]
        if es_video(a):
            esperar_listo(c)
        return c

    if tipo == "POST":
        c = call("POST", f"{ig}/media", {"image_url": url_de(archivos[0]), "caption": texto})["id"]
        return c

    if tipo == "CARRUSEL":
        if not 2 <= len(archivos) <= 10:
            raise RuntimeError("Un carrusel necesita entre 2 y 10 archivos")
        hijos = []
        for a in archivos:
            p = {"is_carousel_item": "true"}
            if es_video(a):
                p.update({"media_type": "VIDEO", "video_url": url_de(a)})
            else:
                p["image_url"] = url_de(a)
            h = call("POST", f"{ig}/media", p)["id"]
            if es_video(a):
                esperar_listo(h)
            hijos.append(h)
        c = call("POST", f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(hijos), "caption": texto})["id"]
        esperar_listo(c)
        return c

    raise RuntimeError(f"Tipo desconocido: {tipo} (usa REEL, HISTORIA, POST o CARRUSEL)")


def leer_texto(fila):
    t = fila.get("texto", "").strip()
    if t.endswith(".txt"):
        with open(os.path.join(TEXTOS, t), encoding="utf-8") as f:
            return f.read().strip()
    return t


def cargar():
    with open(CAL, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for fl in filas:
        for c in COLS:
            fl.setdefault(c, "")
    return filas


def guardar(filas):
    tmp = CAL + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    os.replace(tmp, CAL)


def check():
    ig = env("IG_USER_ID")
    me = call("GET", "me", {"fields": "user_id,username,account_type"})
    print("Cuenta:", me)
    lim = call("GET", f"{ig}/content_publishing_limit", {"fields": "quota_usage,config"})
    print("Cupo diario:", lim)


def main():
    dry = "--dry" in sys.argv
    if "--check" in sys.argv:
        return check()
    ahora = datetime.now(TZ)
    filas = cargar()
    cambios = False
    for fl in filas:
        if fl["estado"].strip().lower() != "programado":
            continue
        cuando = datetime.strptime(fl["fecha_hora"].strip(), "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if cuando > ahora:
            continue
        if ahora - cuando > MAX_ATRASO:
            fl["estado"], fl["nota"] = "atrasado", f"no se publicó a tiempo (revisar) · {ahora:%Y-%m-%d %H:%M}"
            cambios = True
            continue
        print(f"→ {fl['id']} {fl['tipo']} {fl['fecha_hora']}")
        if dry:
            print("   archivos:", [url_de(a) for a in fl["archivos"].split("|") if a.strip()] if os.environ.get("PUBLIC_BASE_URL") else fl["archivos"])
            continue
        try:
            texto = leer_texto(fl)
            c = crear_contenedor(fl, texto)
            pub = call("POST", f"{env('IG_USER_ID')}/media_publish", {"creation_id": c})
            fl["estado"], fl["ig_media_id"], fl["publicado_en"], fl["nota"] = "publicado", pub.get("id", ""), f"{datetime.now(TZ):%Y-%m-%d %H:%M}", ""
            print("   publicado", pub)
        except Exception as e:
            fl["estado"], fl["nota"] = "error", str(e)[:300]
            print("   ERROR", e)
        cambios = True
    if cambios and not dry:
        guardar(filas)


if __name__ == "__main__":
    main()
