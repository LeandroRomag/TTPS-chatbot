import re
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

AR_COUNTRY_CODE = 54


def to_e164(number: str, default_region: str = "AR"):
    """
    Devuelve número en formato E.164 ('+549221...')
    o None si no es válido.
    """
    if not number:
        return None
    
    s = number.strip().replace("whatsapp:", "")
    s = re.sub(r"[ \-\(\)]", "", s)

    try:
        parsed = phonenumbers.parse(s, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        
        return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        return None


def normalize_for_whatsapp(number: str):
    """
    Convierte E.164 al formato que usa WhatsApp (sin +, sin '9').
    Ej:
      '+5492216705941' -> '542216705941'
      '+542216705941' -> '542216705941'
    """
    if not number:
        return None
    
    s = number.strip()

    # Caso típico Argentina móvil con 9
    if s.startswith("+549"):
        return "54" + s[4:]

    # Caso general: remover +
    if s.startswith("+"):
        return s[1:]

    # Intentar parsear si no viene con +
    maybe_e164 = to_e164(s)
    if maybe_e164:
        return normalize_for_whatsapp(maybe_e164)

    # Último recurso
    digits = re.sub(r"\D", "", s)
    if digits.startswith("549"):
        return "54" + digits[3:]
    return digits


def normalize_phone(raw: str, default_region="AR"):
    """
    Retorna:
      (e164, wa_id, is_valid)
    """
    if not raw:
        return (None, None, False)
    
    raw = raw.replace("whatsapp:", "")

    e164 = to_e164(raw, default_region)
    wa_id = None
    valid = False

    if e164:
        wa_id = normalize_for_whatsapp(e164)
        valid = True
    else:
        wa_id = normalize_for_whatsapp(raw)
        maybe_e164 = to_e164(wa_id, default_region)
        if maybe_e164:
            e164 = maybe_e164
            valid = True

    return (e164, wa_id, valid)
