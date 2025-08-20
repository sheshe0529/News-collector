import os
import re
import time
import textwrap
import hashlib
import feedparser
import yaml
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- Opcional LLM ---
USE_LLM = False
try:
    import requests
    if os.getenv("OPENAI_API_KEY"):
        USE_LLM = True
except Exception:
    USE_LLM = False

from whatsapp import send_whatsapp

load_dotenv()

MAX_ITEMS = 10  # máximo de notas en el resumen
SUMMARY_LEN = 4  # nº de bullets en TL;DR aproximado

def slug(s: str) -> str:
    return re.sub(r"\W+", "-", s.lower()).strip("-")

def clean_html(s: str) -> str:
    # Eliminamos HTML básico y normalizamos espacios
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

def simple_score(item):
    # Priorizamos fuentes técnicas y títulos con palabras clave
    title = (item.get("title") or "").lower()
    score = 0
    for kw in ["linux", "windows", "kernel", "kubernetes", "cloud", "infra", "driver", "security", "vulnerability", "patch", "update", "nvidia", "amd", "intel"]:
        if kw in title:
            score += 1
    # Antigüedad
    published_parsed = item.get("published_parsed") or item.get("updated_parsed")
    if published_parsed:
        age = time.time() - time.mktime(published_parsed)
        # Menos edad => mayor score
        score += max(0, 3 - age / (60*60*12))  # 3 puntos si <12h
    return score

def load_sources(path="sources.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("feeds", [])

def fetch_all(feeds):
    items = []
    for f in feeds:
        d = feedparser.parse(f["url"])
        for e in d.entries:
            items.append({
                "source": f["name"],
                "title": clean_html(getattr(e, "title", "")),
                "summary": clean_html(getattr(e, "summary", getattr(e, "description", ""))),
                "link": getattr(e, "link", ""),
                "published_parsed": getattr(e, "published_parsed", getattr(e, "updated_parsed", None)),
            })
    # deduplicar por link o título
    seen = set()
    unique = []
    for it in items:
        key = it["link"] or it["title"]
        h = hashlib.md5(key.encode("utf-8")).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(it)
    # ordenar por score descendente
    unique.sort(key=simple_score, reverse=True)
    return unique[: MAX_ITEMS]

def llm_summarize(items):
    # Usa la API de OpenAI (o similar) si OPENAI_API_KEY está presente.
    # Prompt en español, estilo conciso.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    # Armamos contexto
    bullets = []
    for it in items:
        bullets.append(f"- {it['title']} ({it['source']})")

    prompt = f"""Eres un asistente experto que crea un resumen diario conciso (máx. {SUMMARY_LEN} puntos) en español sobre novedades técnicas en sistemas operativos, Linux, Windows, infraestructura TI, cloud y hardware. 
Condensa las noticias en bullets claros con verbo al inicio (p. ej., "Lanzan...", "Corrigen...", "Anuncian...") y menciona producto/proyecto/empresa.
Evita opinión y adornos. Mantén una línea por bullet. 

Noticias:
{chr(10).join(bullets)}
"""

    # Llamada rápida a la API de Chat Completions
    try:
        import json, requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Eres un asistente que resume noticias técnicas de forma muy concisa."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        out = resp.json()
        return out["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return None

def rules_summary(items):
    # Resumen simple por reglas: toma los N títulos más relevantes
    top = items[:SUMMARY_LEN]
    lines = []
    for it in top:
        lines.append(f"- {it['title']} ({it['source']})")
    return "\n".join(lines)

def make_digest(items):
    date_lima = datetime.now().strftime("%Y-%m-%d")
    header = f"📰 Resumen Tech • {date_lima}"
    tldr = llm_summarize(items) if USE_LLM else None
    if not tldr:
        tldr = rules_summary(items)

    body_lines = [header, "", "TL;DR", tldr, "", "Lecturas:"]
    for it in items:
        body_lines.append(f"• {it['title']} — {it['link']}")
    body = "\n".join(body_lines)
    # WhatsApp limita largo; si excede 4096, recortamos lecturas
    if len(body) > 3900:
        body_lines = body_lines[: body_lines.index("Lecturas:")+1] + body_lines[body_lines.index("Lecturas:")+1 : body_lines.index("Lecturas:")+1 + 5]
        body = "\n".join(body_lines)
        body += "\n… (+ más en tus feeds)"
    return body

def main():
    feeds = load_sources()
    items = fetch_all(feeds)
    if not items:
        print("Sin items disponibles.")
        return
    message = make_digest(items)
    # Enviar por WhatsApp
    ok, err = send_whatsapp(message)
    if ok:
        print("Mensaje enviado correctamente.")
    else:
        print("Error al enviar WhatsApp:", err)
        # Fallback: imprime por consola
        print("\n--- DIGEST ---\n")
        print(message)

if __name__ == "__main__":
    main()
