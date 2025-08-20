import os, re, time, hashlib, feedparser, yaml
from datetime import datetime
from dotenv import load_dotenv
from whatsapp import send_whatsapp

load_dotenv()

# ====== Ajusta aquí tus preferencias ======
MAX_ITEMS = 4                    # 4 bullets para no pasar el límite del Sandbox
KEYWORDS = {
    # SO / Linux / Windows
    "linux","kernel","ubuntu","debian","fedora","arch","red hat","windows","microsoft",
    # Infra / Cloud / DevOps
    "kubernetes","docker","container","cloud","aws","azure","gcp","security","vulnerability","patch",
    # Hardware
    "cpu","gpu","intel","amd","nvidia","epyc","ryzen","xeon",
    # IA / Software
    "ai","machine learning","llm","model","open source","driver","release","update"
}
# ==========================================

def clean_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

def load_sources(path="sources.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("feeds", [])

def fetch_items(feeds):
    items = []
    for f in feeds:
        d = feedparser.parse(f["url"])
        for e in d.entries:
            title = clean_html(getattr(e, "title", ""))
            summary = clean_html(getattr(e, "summary", getattr(e, "description", "")))
            link = getattr(e, "link", "") or getattr(e, "id", "")
            published = getattr(e, "published_parsed", getattr(e, "updated_parsed", None))
            items.append({
                "source": f["name"],
                "title": title,
                "summary": summary,
                "link": link,
                "published_parsed": published,
            })
    # dedupe por link/título
    seen, uniq = set(), []
    for it in items:
        h = hashlib.md5((it["link"] or it["title"]).encode("utf-8")).hexdigest()
        if h not in seen:
            seen.add(h); uniq.append(it)
    # ordenar recientes primero
    uniq.sort(key=lambda x: x["published_parsed"] or time.gmtime(0), reverse=True)
    return uniq

def matches_keywords(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in KEYWORDS)

def generic_headline(it):
    """Devuelve un titular corto y genérico por categoría detectada."""
    t = it["title"].lower()
    src = it["source"]
    if any(k in t for k in ["linux","kernel","ubuntu","fedora","debian","arch","red hat"]):
        return f"Novedades en Linux y ecosistema ({src})"
    if "windows" in t or "microsoft" in t:
        return f"Actualización y cambios en Windows ({src})"
    if any(k in t for k in ["kubernetes","container","docker"]):
        return f"Movimientos en contenedores/Kubernetes ({src})"
    if any(k in t for k in ["aws","azure","gcp","cloud"]):
        return f"Anuncios y lanzamientos en Cloud ({src})"
    if any(k in t for k in ["cpu","gpu","intel","amd","nvidia","epyc","ryzen","xeon"]):
        return f"Avances de hardware y drivers ({src})"
    if any(k in t for k in ["security","vulnerability","patch"]):
        return f"Parcheo y seguridad en plataformas ({src})"
    if any(k in t for k in ["ai","machine learning","llm","model"]):
        return f"Novedades en IA y modelos ({src})"
    return f"Actualización relevante en tecnología ({src})"

def make_digest(items):
    # filtrar por keywords y tomar top N
    filtered = [it for it in items if matches_keywords((it["title"] + " " + it["summary"]))]

    # si no hubo match, toma lo más reciente igualmente
    if not filtered:
        filtered = items[:MAX_ITEMS]
    else:
        filtered = filtered[:MAX_ITEMS]

    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"📰 Resumen Tech • {date_str}", ""]

    for it in filtered:
        headline = generic_headline(it)
        # enlace “Ver más” por ítem
        lines.append(f"- {headline} — [Ver más]({it['link']})")

    body = "\n".join(lines)

    # Límite Sandbox ~1600 chars → reforzamos margen
    if len(body) > 1500:
        lines = lines[:2 + MAX_ITEMS]  # header + MAX_ITEMS
        body = "\n".join(lines)

    return body

def main():
    feeds = load_sources()
    items = fetch_items(feeds)
    if not items:
        print("Sin items disponibles.")
        return
    message = make_digest(items)
    ok, err = send_whatsapp(message)
    if ok:
        print("Mensaje enviado correctamente.")
    else:
        print("Error al enviar WhatsApp:", err)
        print("\n--- DEBUG ---\n", message)

if __name__ == "__main__":
    main()
