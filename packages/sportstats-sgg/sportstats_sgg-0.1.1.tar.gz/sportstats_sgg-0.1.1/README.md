# Paquete SportStats (sportstats_sgg)

Este es un paquete de ejemplo creado para el Módulo 2 del Máster.
Provee funciones de utilidad para análisis deportivo.

## Instalación

pip install sportstats_sgg

## Ejemplos de Uso

import sportstats_sgg as ssa

### 1. Calcular Promedio de Goles
promedio = ssa.calcular_promedio_goles(goles=20, partidos=15)
print(f"El promedio de goles es: {promedio}") 
# Salida: El promedio de goles es: 1.33

### 2. Verificar Elegibilidad
elegible = ssa.verificar_elegibilidad(lesionado=False, partidos_minimos=10, partidos_jugados=12)
print(f"El jugador es elegible: {elegible}")
# Salida: El jugador es elegible: True

### 3. Filtrar Tiempos Rápidos
tiempos = [10.2, 9.8, 11.1, 9.9, 10.5]
rapidos = ssa.filtrar_tiempos_rapidos(tiempos, 10.0)
print(f"Tiempos rápidos: {rapidos}")
# Salida: Tiempos rápidos: [9.8, 9.9]