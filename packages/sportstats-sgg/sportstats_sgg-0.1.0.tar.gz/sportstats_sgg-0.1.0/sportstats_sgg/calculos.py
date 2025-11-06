# Este es el módulo de cálculos de nuestro paquete

def calcular_promedio_goles(goles, partidos):
    """
    Calcula el promedio de goles por partido, manejando divisiones por cero.
    """
    if partidos == 0:
        return 0.0
    try:
        promedio = goles / partidos
        return round(promedio, 2)
    except TypeError:
        return "Error: Los valores deben ser numéricos."

def verificar_elegibilidad(lesionado, partidos_minimos, partidos_jugados):
    """
    Verifica si un jugador es elegible (no lesionado y cumple mínimos).
    """
    if (not lesionado) and (partidos_jugados >= partidos_minimos):
        return True
    else:
        return False