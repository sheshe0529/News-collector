# Tech News → WhatsApp (Daily Digest)

Resumen diario (en español) de noticias de **sistemas operativos** (Windows, Linux), **infraestructura TI**, **hardware** y **software**, obtenido desde RSS (gratis) y enviado por **WhatsApp** mediante **Twilio** o la **Cloud API de WhatsApp**.

## 🧩 Arquitectura
1. **Recolector (RSS)**: lee fuentes definidas en `sources.yaml`.
2. **Normalizador**: limpia títulos/descripciones y elimina duplicados.
3. **Resumidor**: crea un resumen "TL;DR" en español (reglas simples). Opcional: usa un LLM si configuras `OPENAI_API_KEY`.
4. **Entrega**: envía el texto por WhatsApp (Twilio) o imprime por consola si está en modo prueba.
5. **Programación**: GitHub Actions (o cron) lo ejecuta **diariamente a las 13:00 América/Lima**.

## 🚀 Deploy rápido (GitHub Actions)
1. Sube este folder a un repositorio nuevo en GitHub.
2. En **Settings → Secrets and variables → Actions → New repository secret**, añade:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `WHATSAPP_FROM` (formato: `whatsapp:+14155238886` si usas el sandbox)
   - `WHATSAPP_TO` (tu número con prefijo país, p. ej. `whatsapp:+519XXXXXXXX`)
   - *(Opcional)* `OPENAI_API_KEY` para mejor resumen.
3. Revisa/edita `sources.yaml` si quieres agregar o quitar fuentes.
4. El flujo `daily.yml` ya está configurado para correr todos los días a las 13:00 Lima.

> **Nota sobre WhatsApp**: En desarrollo puedes usar el **Sandbox de Twilio para WhatsApp**. Para producción, necesitas registrar un número y (en la Cloud API de Meta) **plantillas aprobadas**.

## 🖥️ Ejecución local (opcional)
```bash
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env  # edita tus claves
python main.py
```

## ⚙️ Variables de entorno
Crea un `.env` con:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+519XXXXXXXX
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # opcional
TZ=America/Lima
```

## 🧪 Personalización
- Edita `sources.yaml` para añadir feeds.
- Cambia el límite de ítems y el tono de resumen en `main.py` (`MAX_ITEMS` y `make_digest`).

## 🔐 Costos y límites
- **RSS**: gratis.
- **Twilio**: tiene **Sandbox** y prueba con crédito. Para enviar a más usuarios, necesitarás un número aprobado.
- **LLM**: opcional. Si no configuras `OPENAI_API_KEY`, usa el resumidor simple por reglas.

---

Hecho con ❤️ para mantenerte al día sin esfuerzo.
