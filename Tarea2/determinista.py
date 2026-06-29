import random
import math
import time
import matplotlib.pyplot as plt


n_adds = 0
n_removes = 0
n_swaps = 0

def leer_instancia(ruta_archivo):
    with open(ruta_archivo, 'r') as file:
        datos = file.read().split()
    datos = [int(x) for x in datos]

    m  = datos[0]   # Número de alternativas
    n  = datos[1]   # Número de recursos
    ne = datos[2]   # Número de relaciones
    B  = datos[3]   # Capacidad máxima

    idx = 4
    beneficios = datos[idx : idx + m];  idx += m
    costos     = datos[idx : idx + n];  idx += n

    recursos_requeridos = [set() for _ in range(m)]
    for _ in range(ne):
        id_alt = datos[idx]
        id_rec = datos[idx + 1]
        recursos_requeridos[id_alt].add(id_rec)
        idx += 2

    return m, n, B, beneficios, costos, recursos_requeridos


#recorre toda la lista de la solucion y agrega los subconjuntos a un conjunto grande, se usa set entonces no hay duplicados.
#ej:sol [1,2]
#    alternativa 1: usa 2 y 3
#    alternativa 2: usa 3 y 4
#   recursos_usados = {2,3,4}
def calcular_costo(solucion, recursos_requeridos, costos):
    recursos_usados = set()
    
    #uniones de conjuntos
    for i in solucion:
        recursos_usados |= recursos_requeridos[i]
    
    #calculo del costo sin duplicados
    costo_total = 0
    for j in recursos_usados:
        costo_total += costos[j]
    
    return costo_total


def calcular_beneficio(solucion, beneficios):
    beneficio = 0    

    for i in solucion:
        beneficio += beneficios[i]
    
    return beneficio


def es_factible(solucion, recursos_requeridos, costos, B):
    costo_total = calcular_costo(solucion, recursos_requeridos, costos)

    if costo_total > B:
        return False
    
    return True


def greedy_determinista(m, B, beneficios, costos, recursos_requeridos):
    evaluaciones = []
    
    #rentabilidad individual ordenada de mayor a menor
    for i in range(m):
        recursos_i = recursos_requeridos[i]
        costo_individual = 0
        for recurso in recursos_i:
            costo_individual += costos[recurso]

        rentabilidad = beneficios[i] / costo_individual if costo_individual > 0 else float('inf')
        evaluaciones.append((rentabilidad, i))
    evaluaciones.sort(reverse=True)
    
    #guardar solo el inddice
    alternativas_ordenadas = []
    for pareja in evaluaciones:
        indice = pareja[1]
        alternativas_ordenadas.append(indice)

    #agregar hasta la ultima que no se pase de la capacidad
    solucion = set()

    for i in alternativas_ordenadas:
        candidata = solucion | {i}
        if calcular_costo(candidata, recursos_requeridos, costos) <= B:
            solucion = candidata

    return solucion

import os
import statistics
ruta_instancias = 'instancias'

# Asegurarse de que exista el directorio de resultados
if not os.path.exists('resultados'):
    os.makedirs('resultados')

rutas = [
    f'{ruta_instancias}/easy.txt',
    f'{ruta_instancias}/medium1.txt',
    f'{ruta_instancias}/medium2.txt',
    f'{ruta_instancias}/hard.txt'
]

ejecuciones = 10
resumen_global = []

for ruta in rutas:
    try:
        m, n, B, beneficios, costos, recursos_requeridos = leer_instancia(ruta)
        nombre_instancia = ruta.split('/')[-1].split('.')[0]
        
        print("=" * 65)
        print(f"Procesando Instancia: {nombre_instancia} ({m} alt, {n} rec, B={B})")
        print("-" * 65)

        tiempos = []
        beneficios_obtenidos = []

        for i in range(ejecuciones):
            tiempo_inicial = time.time()
            solucion = greedy_determinista(m, B, beneficios, costos, recursos_requeridos)
            tiempo_final = time.time()
            
            tiempo_ejecucion = tiempo_final - tiempo_inicial
            beneficio = calcular_beneficio(solucion, beneficios)
            
            tiempos.append(tiempo_ejecucion)
            beneficios_obtenidos.append(beneficio)

        # Cálculos estadísticos
        t_promedio = statistics.mean(tiempos)
        b_max = max(beneficios_obtenidos)
        b_min = min(beneficios_obtenidos)
        b_promedio = statistics.mean(beneficios_obtenidos)
        b_desv_estandar = statistics.stdev(beneficios_obtenidos) if ejecuciones > 1 else 0.0

        # Imprimir resultados por consola
        print(f" Resultados tras {ejecuciones} ejecuciones:")
        print(f"   > Tiempo Promedio   : {t_promedio:.6f} segundos")
        print(f"   > Beneficio Máximo  : {b_max}")
        print(f"   > Beneficio Mínimo  : {b_min}")
        print(f"   > Beneficio Promedio: {b_promedio:.2f}")
        print(f"   > Desv. Estándar    : {b_desv_estandar:.4f}\n")

        # Guardar en la lista global para el CSV
        resumen_global.append([
            nombre_instancia, 
            t_promedio, 
            b_max, 
            b_min, 
            b_promedio, 
            b_desv_estandar
        ])
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ruta}. Saltando instancia...\n")

# Guardar el resumen en un único archivo CSV
csv_con_fecha = time.strftime("%Y%m%d-%H%M%S")
ruta_csv = f'resultados/resumen_det_{csv_con_fecha}.csv'

with open(ruta_csv, 'w') as f:
    f.write("Instancia,Tiempo_Promedio_s,Beneficio_Maximo,Beneficio_Minimo,Beneficio_Promedio,Desviacion_Estandar\n")
    for fila in resumen_global:
        f.write(f"{fila[0]},{fila[1]:.6f},{fila[2]},{fila[3]},{fila[4]:.2f},{fila[5]:.4f}\n")

print("=" * 65)
print(f"EJECUCIÓN FINALIZADA. Resumen guardado en: {ruta_csv}")
print("=" * 65)