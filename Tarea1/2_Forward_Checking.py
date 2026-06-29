import os
import time
import csv
import matplotlib.pyplot as plt
from datetime import datetime

# CONFIGURACION PARA GUARDAR FOTOS DE LOS GRAFICOS
NOMBRE_ARCHIVO = 'case1.txt'
cantidad_pistas  = 3 
nombre_base = os.path.splitext(NOMBRE_ARCHIVO)[0]
fecha_ejecucion = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

CARPETA_RESULTADOS = os.path.join(os.path.dirname(__file__), 'resultados_FC', f"{nombre_base}_{fecha_ejecucion}")
os.makedirs(CARPETA_RESULTADOS, exist_ok=True)


# ── Lectura de instancia ───────────────────────────────────────────────────────
with open(os.path.join(os.path.dirname(__file__), NOMBRE_ARCHIVO)) as caso:
    valores = caso.read().split()
    D = int(valores[0])
    idx = 1
    aviones = []
    Tij_global = []

    for i in range(D):
        Ek        = int(valores[idx])
        Pk        = int(valores[idx + 1])
        Lk        = int(valores[idx + 2])
        pen_early = float(valores[idx + 3])
        pen_tardy = float(valores[idx + 4])
        idx += 5

        Tij = []
        for j in range(D):
            Tij.append(int(valores[idx]))
            idx += 1
        Tij_global.append(Tij)

        aviones.append({
            'id':              i + 1,
            'primer_tiempo':   Ek,
            'tiempo_esperado': Pk,
            'ultimo_tiempo':   Lk,
            'dominio':         Lk - Ek + 1,
            'costo_temprano':  pen_early,
            'costo_tarde':     pen_tardy,
            'Tij':             Tij,
        })


# ── Variables globales ─────────────────────────────────────────────────────────
mejor_costo    = float('inf')
mejor_secuencia = None
mejoramiento   = []

sol_factibles    = 0
sol_infactibles  = 0   # podas FC (avión futuro sin pista válida)

contador_nodos   = 0
NODOS_MAXIMOS    = 100000
TIEMPO_MAX       = int(120)
TIEMPO_INICIAL   = time.time()

nodos_tiempo          = []
costos_tiempo         = []
factibles_infactibles = []
costos_nodos          = []
tiempo_usado          = False
proximo_muestreo      = 0.1
nodos_entre_muestras  = 5000


# ── Funciones de costo ─────────────────────────────────────────────────────────
def calcular_costo_arr(secuencia):
    costo_total = 0
    for entrada in secuencia:
        tiempo_llegada  = entrada[1]
        tiempo_esperado = entrada[2]
        desfase         = abs(tiempo_esperado - tiempo_llegada)
        costo_tarde     = entrada[3]
        costo_temprano  = entrada[4]

        if tiempo_llegada == tiempo_esperado:
            continue
        elif tiempo_llegada > tiempo_esperado:
            costo_total += desfase * costo_tarde
        else:
            costo_total += desfase * costo_temprano
    return int(costo_total)


def es_menor_costo(costo_actual, secuencia):
    global mejor_costo, mejor_secuencia, mejoramiento
    global costos_nodos, costos_tiempo, contador_nodos
    if costo_actual < mejor_costo:
        mejor_costo     = int(costo_actual)
        mejor_secuencia = secuencia.copy()
        mejoramiento.append(mejor_costo)
        return True
    return False


# ── es_valido: separación contra aviones YA asignados en la misma pista ────────
def es_valido(avion_nuevo, tiempo_nuevo, pista_nueva, instanciados):
    global sol_infactibles, Tij_global
    for avion_previo in instanciados:
        pista_previa  = avion_previo[5]
        tiempo_previo = avion_previo[1]
        if pista_nueva == pista_previa:
            id_nuevo  = avion_nuevo['id'] - 1
            id_previo = avion_previo[0] - 1
            if tiempo_nuevo >= tiempo_previo:
                separacion_req = Tij_global[id_previo][id_nuevo]
                if (tiempo_nuevo - tiempo_previo) < separacion_req: 
                    sol_infactibles += 1
                    return False
            else:
                separacion_req = Tij_global[id_nuevo][id_previo]
                if (tiempo_previo - tiempo_nuevo) < separacion_req: 
                    sol_infactibles += 1
                    return False
    return True


# ── Gráficos ───────────────────────────────────────────────────────────────────
def graficar_nodos_tiempo(nodos_tiempo):
    if not nodos_tiempo:
        print("No hay datos para graficar Nodos vs Tiempo.")
        return
    nodos   = [item[0] for item in nodos_tiempo]
    tiempos = [item[1] for item in nodos_tiempo]
    plt.figure(figsize=(10, 5))
    plt.plot(tiempos, nodos, color='blue', linewidth=2)
    plt.title('Nodos Explorados vs Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Cantidad de Nodos')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(CARPETA_RESULTADOS, '1_nodos_vs_tiempo.png'), bbox_inches='tight')

    ruta_csv = os.path.join(CARPETA_RESULTADOS, '1_nodos_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Nodos'])
        for t, n in zip(tiempos, nodos):
            writer.writerow([t, n])
    print("Gráfico y CSV guardados: 1_nodos_vs_tiempo")


def graficar_costos_tiempo(costos_tiempo):
    if not costos_tiempo:
        print("No hay datos para graficar Costos vs Tiempo.")
        return
    costos_tiempo.sort(key=lambda x: x[1])
    costos  = [item[0] for item in costos_tiempo]
    tiempos = [item[1] for item in costos_tiempo]
    plt.figure(figsize=(10, 5))
    plt.step(tiempos, costos, where='post', color='green', marker='o')
    plt.title('Evolución del Mejor Costo en el Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Mejor Costo Encontrado')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(CARPETA_RESULTADOS, '2_costos_vs_tiempo.png'), bbox_inches='tight')

    ruta_csv = os.path.join(CARPETA_RESULTADOS, '2_costos_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Mejor Costo'])
        for t, c in zip(tiempos, costos):
            writer.writerow([t, c])
    print("Gráfico y CSV guardados: 2_costos_vs_tiempo")


def graficar_factibles_infactibles(factibles_infactibles):
    if not factibles_infactibles:
        print("No hay datos para graficar Soluciones vs Tiempo.")
        return
    factibles   = [item[0] for item in factibles_infactibles]
    infactibles = [item[1] for item in factibles_infactibles]
    tiempos     = [item[2] for item in factibles_infactibles]
    plt.figure(figsize=(10, 5))
    plt.plot(tiempos, factibles,   label='Factibles',             color='green', linewidth=2)
    plt.plot(tiempos, infactibles, label='Podas FC (sin ventana)', color='red',   linewidth=2)
    plt.yscale('log')
    plt.title('Soluciones Factibles y Podas FC vs Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Cantidad')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(CARPETA_RESULTADOS, '3_soluciones_vs_tiempo.png'), bbox_inches='tight')
    
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '3_soluciones_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Factibles', 'Infactibles (Podas FC)'])
        for t, f, inf in zip(tiempos, factibles, infactibles):
            writer.writerow([t, f, inf])
            
    print("Gráfico y CSV guardados: 3_soluciones_vs_tiempo")


def graficar_costos_nodos(costos_nodos):
    if not costos_nodos:
        print("No hay datos para graficar Costos vs Nodos.")
        return
    costos = [item[0] for item in costos_nodos]
    nodos  = [item[1] for item in costos_nodos]
    plt.figure(figsize=(10, 5))
    plt.step(nodos, costos, where='post', color='purple', marker='o')
    plt.title('Evolución del Mejor Costo vs Nodos Explorados')
    plt.xlabel('Nodos Explorados')
    plt.ylabel('Mejor Costo Encontrado')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(CARPETA_RESULTADOS, '4_costos_vs_nodos.png'), bbox_inches='tight')
    
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '4_costos_vs_nodos.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Nodos Explorados', 'Mejor Costo'])
        for n, c in zip(nodos, costos):
            writer.writerow([n, c])
            
    print("Gráfico y CSV guardados: 4_costos_vs_nodos")


# ── Función recursiva con Forward Checking Verdadero (Sets) ───────────────────
def funcion_recursiva(nivel, aviones_instanciados, dominios_actuales):
    global cantidad_pistas, aviones, mejor_costo, mejor_secuencia
    global sol_factibles, sol_infactibles, contador_nodos
    global NODOS_MAXIMOS, TIEMPO_MAX, TIEMPO_INICIAL
    global nodos_tiempo, costos_tiempo, factibles_infactibles, costos_nodos
    global tiempo_usado, proximo_muestreo, nodos_entre_muestras

    contador_nodos += 1
    tiempo_actual = int(time.time() - TIEMPO_INICIAL)

    # ── Muestreo por tiempo y nodos ───────────────────────────────────────────
    if tiempo_actual >= proximo_muestreo:
        proximo_muestreo += 1
        nodos_tiempo.append((contador_nodos, tiempo_actual))
        factibles_infactibles.append((sol_factibles, sol_infactibles, tiempo_actual))
        costo_a_guardar = mejor_costo if mejor_costo != float('inf') else 0
        costos_tiempo.append((costo_a_guardar, tiempo_actual))

    if contador_nodos % (NODOS_MAXIMOS // 20) == 0:
        print(f'[!] Nodos explorados: {contador_nodos}')

    if contador_nodos % nodos_entre_muestras == 0:
        costo_a_guardar = mejor_costo if mejor_costo != float('inf') else 0
        costos_nodos.append((costo_a_guardar, contador_nodos))

    if contador_nodos == NODOS_MAXIMOS:
        graficar_costos_nodos(costos_nodos)

    if tiempo_actual == TIEMPO_MAX and not tiempo_usado:
        graficar_costos_tiempo(costos_tiempo)
        graficar_factibles_infactibles(factibles_infactibles)
        graficar_nodos_tiempo(nodos_tiempo)
        tiempo_usado = True

    # ── Caso base ─────────────────────────────────────────────────────────────
    if nivel == len(aviones):
        sol_factibles += 1
        costo_secuencia = calcular_costo_arr(aviones_instanciados)
        if es_menor_costo(costo_secuencia, aviones_instanciados):
            costos_tiempo.append((costo_secuencia, tiempo_actual))
            print(f'[!!!!!!] nueva mejor secuencia encontrada: {mejor_costo}')
        return

    avion_actual   = aviones[nivel]
    id_actual_orig = avion_actual['id'] - 1

    for pista in range(1, cantidad_pistas + 1):

        # Si el dominio del avión para esta pista quedó vacío, saltamos
        if not dominios_actuales[id_actual_orig][pista]:
            continue

        # Iteramos ordenadamente por los tiempos que sobrevivieron en el dominio
        for tiempo in sorted(dominios_actuales[id_actual_orig][pista]):

            # Verificación clásica por si hay restricciones cruzadas
            if not es_valido(avion_actual, tiempo, pista, aviones_instanciados):
                continue

            # ── Forward Checking (Restando Ventanas de Tiempo) ─────────────────
            # Copiamos la estructura de diccionarios y conjuntos
            nuevo_dominio = {k: {p: set(v[p]) for p in v} for k, v in dominios_actuales.items()}
            valido = True

            for nivel_futuro in range(nivel + 1, len(aviones)):
                avion_futuro   = aviones[nivel_futuro]
                id_futuro_orig = avion_futuro['id'] - 1

                separacion_actual_a_futuro = avion_actual['Tij'][id_futuro_orig]
                separacion_futuro_a_actual = Tij_global[id_futuro_orig][id_actual_orig]

                # Calculamos el rango de tiempo prohibido para el avión futuro en esta misma pista
                inicio_bloqueo = tiempo - separacion_futuro_a_actual + 1
                fin_bloqueo = tiempo + separacion_actual_a_futuro - 1
                ventana_prohibida = set(range(inicio_bloqueo, fin_bloqueo + 1))

                # Le quitamos esa ventana prohibida al dominio del avión futuro
                nuevo_dominio[id_futuro_orig][pista] -= ventana_prohibida

                # Verificamos si al avión futuro le queda alguna opción viable en cualquier pista
                tiene_pista_valida = any(len(nuevo_dominio[id_futuro_orig][p]) > 0 for p in range(1, cantidad_pistas + 1))

                if not tiene_pista_valida:
                    sol_infactibles += 1
                    valido = False
                    break

            if not valido:
                continue  # Si podamos por FC, probamos el siguiente minuto

            # ── Asignar ───────────────────────────────────────────────────────
            aviones_instanciados.append([
                avion_actual['id'],              
                tiempo,                          
                avion_actual['tiempo_esperado'], 
                avion_actual['costo_tarde'],     
                avion_actual['costo_temprano'],  
                pista                            
            ])

            # Recursión con los dominios filtrados por FC
            funcion_recursiva(nivel + 1, aviones_instanciados, nuevo_dominio)

            # ── Backtracking ──────────────────────────────────────────────────
            aviones_instanciados.pop()


# ── Inicialización y ejecución ─────────────────────────────────────────────────

# Ordenar aviones por tiempo esperado (menor a mayor)
aviones.sort(key=lambda avion: avion['tiempo_esperado'])

# dominios_iniciales: Conjuntos (sets) con todos los minutos posibles desde Ek hasta Lk
dominios_iniciales = {}
for avion in aviones:
    id_orig = avion['id'] - 1
    dominios_iniciales[id_orig] = {
        p: set(range(avion['primer_tiempo'], avion['ultimo_tiempo'] + 1))
        for p in range(1, cantidad_pistas + 1)
    }

print(f"Iniciando Forward Checking: {len(aviones)} aviones, {cantidad_pistas} pista(s)...")
print("-" * 50)

funcion_recursiva(0, [], dominios_iniciales)

# Guardar gráficos finales si no se guardaron por tiempo
graficar_costos_tiempo(costos_tiempo)
graficar_factibles_infactibles(factibles_infactibles)
graficar_nodos_tiempo(nodos_tiempo)
graficar_costos_nodos(costos_nodos)

print("\n" + "=" * 50)
print("RESULTADO FINAL - FORWARD CHECKING")
if mejor_costo == float('inf'):
    print("No existe solución factible.")
else:
    print(f"Costo mínimo : {mejor_costo}")
    print(f"Aviones      : {[e[0] for e in mejor_secuencia]}")
    print(f"Tiempos      : {[e[1] for e in mejor_secuencia]}")
    print(f"Pistas       : {[e[5] for e in mejor_secuencia]}")
    print(f"Nodos totales: {contador_nodos}")
    print(f"Podas FC     : {sol_infactibles}")
print("=" * 50)