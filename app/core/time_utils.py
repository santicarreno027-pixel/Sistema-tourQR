from datetime import datetime, date
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("America/Cancun")

def combinar_fecha_y_hora(fecha: date, hora_str: str) -> datetime:
    """
    Toma una fecha (date) y un texto de hora, limpia mezclas raras como '13:30 PM'
    y devuelve un objeto datetime COMPLETO con zona horaria de Quintana Roo.
    """
    if not hora_str or hora_str.strip().upper() == "OPEN":
        dt_naive = datetime.combine(fecha, datetime.min.time())
        return dt_naive.replace(tzinfo=TZ_LOCAL)
        
    # 🧼 LIMPIEZA EXTRA: Si metieron algo como "13:30 PM", removemos el PM/AM para no romper %H:%M
    hora_clean = hora_str.strip().upper()
    if any(x in hora_clean for x in ["AM", "PM"]) and any(int(s) > 12 for s in hora_clean.split(':') if s.isdigit()):
        hora_clean = hora_clean.replace("AM", "").replace("PM", "").strip()
    
    # 🌟 Intento 1: Formato 24 horas estándar (Ej: '13:30')
    try:
        time_obj = datetime.strptime(hora_clean, "%H:%M").time()
        dt_naive = datetime.combine(fecha, time_obj)
        return dt_naive.replace(tzinfo=TZ_LOCAL)
    except Exception:
        pass

    # 🌟 Intento 2: Formato 12 horas clásico (Ej: '01:30 PM')
    try:
        time_obj = datetime.strptime(hora_clean, "%I:%M %p").time()
        dt_naive = datetime.combine(fecha, time_obj)
        return dt_naive.replace(tzinfo=TZ_LOCAL)
    except Exception:
        pass

    # 🚨 Plan de Rescate Total
    dt_naive = datetime.combine(fecha, datetime.strptime("08:00 AM", "%I:%M %p").time())
    return dt_naive.replace(tzinfo=TZ_LOCAL)