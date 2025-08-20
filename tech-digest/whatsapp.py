import os
from typing import Tuple

def send_whatsapp(message: str) -> Tuple[bool, str]:
    """
    Envía un WhatsApp usando Twilio.
    Requiere variables de entorno:
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - WHATSAPP_FROM (ej. whatsapp:+14155238886)
      - WHATSAPP_TO   (ej. whatsapp:+519XXXXXXXX)
    """
    from twilio.rest import Client

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("WHATSAPP_FROM")
    to_num = os.getenv("WHATSAPP_TO")

    if not all([sid, token, from_num, to_num]):
        return False, "Faltan variables de entorno de Twilio."

    try:
        client = Client(sid, token)
        msg = client.messages.create(
            body=message,
            from_=from_num,
            to=to_num
        )
        return True, ""
    except Exception as e:
        return False, str(e)
