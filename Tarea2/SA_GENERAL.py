import random
import math
import time
import statistics
import matplotlib.pyplot as plt
import os

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

def calcular_costo(solucion, recursos_requeridos, costos):
    recursos_usados = set()
    for i in solucion:
        recursos_usados |= recursos_requeridos[i]
    return sum(costos[j] for j in recursos_usados)

def calcular_beneficio(solucion, beneficios):
    return sum(beneficios[i] for i in solucion)

def es_factible(solucion, recursos_requeridos, costos, B):
    return calcular_costo(solucion, recursos_requeridos, costos) <= B

def greedy_determinista(m, B, beneficios, costos, recursos_requeridos):
    evaluaciones = []
    for i in range(m):
        recursos_i = recursos_requeridos[i]
        costo_individual = sum(costos[rec] for rec in recursos_i)
        rentabilidad = beneficios[i] / costo_individual if costo_individual > 0 else float('inf')
        evaluaciones.append((rentabilidad, i))
        
    evaluaciones.sort(reverse=True)
    alternativas_ordenadas = [pareja[1] for pareja in evaluaciones]

    solucion = set()
    for i in alternativas_ordenadas:
        candidata = solucion | {i}
        if calcular_costo(candidata, recursos_requeridos, costos) <= B:
            solucion = candidata
    return solucion

def greedy_estocastico(m, B, beneficios, costos, recursos_requeridos, semilla, k=3):
    random.seed(semilla)
    evaluaciones = []
    for i in range(m):
        recursos_i = recursos_requeridos[i]
        costo_individual = sum(costos[recurso] for recurso in recursos_i)
        rentabilidad = beneficios[i] / costo_individual if costo_individual > 0 else float('inf')
        evaluaciones.append((rentabilidad, i))

    evaluaciones.sort(reverse=True)
    candidatos = [indice for _, indice in evaluaciones]
    solucion = set()

    while candidatos:
        top_k = candidatos[:k]
        elegido = random.choice(top_k)
        if calcular_costo(solucion | {elegido}, recursos_requeridos, costos) <= B:
            solucion.add(elegido)
        candidatos.remove(elegido)
    return solucion

def generar_vecino(solucion, m):
    solucion = set(solucion)
    no_seleccionadas = list(set(range(m)) - solucion)
    seleccionadas    = list(solucion)
    r = random.random()

    if r < 0.333:
        if no_seleccionadas:  
            solucion.add(random.choice(no_seleccionadas))
    elif r < 0.666:
        if seleccionadas: 
            solucion.remove(random.choice(seleccionadas))
    else:
        if seleccionadas and no_seleccionadas: 
            solucion.remove(random.choice(seleccionadas))
            solucion.add(random.choice(no_seleccionadas))
            
    return solucion

def simulated_annealing(m, B, beneficios, costos, recursos_requeridos, solucion_inicial, semilla, T_inicial=1000.0, alpha=0.995, T_min=0.1, L=100):
    random.seed(semilla)
    solucion_actual = set(solucion_inicial)
    mejor_solucion  = set(solucion_actual)
    
    mejor_beneficio = calcular_beneficio(mejor_solucion, beneficios)
    beneficio_actual = mejor_beneficio

    T = T_inicial
    iteracion = 0
    iter_mejor = 0

    historial_mejor  = []

    while T > T_min:
        for _ in range(L):
            iteracion += 1
            vecino = generar_vecino(solucion_actual, m)

            if not es_factible(vecino, recursos_requeridos, costos, B):
                continue

            beneficio_vecino = calcular_beneficio(vecino, beneficios)
            delta = beneficio_vecino - beneficio_actual  

            if delta > 0:
                solucion_actual  = vecino
                beneficio_actual = beneficio_vecino
                if beneficio_actual > mejor_beneficio:
                    mejor_solucion  = set(solucion_actual)
                    mejor_beneficio = beneficio_actual
                    iter_mejor = iteracion
            else:
                prob = math.exp(delta / T)
                if random.random() < prob:
                    solucion_actual  = vecino
                    beneficio_actual = beneficio_vecino

            historial_mejor.append(mejor_beneficio)

        T *= alpha

    return mejor_solucion, mejor_beneficio, historial_mejor, iter_mejor


# =============================================================================
# EXPERIMENTO AUTOMATIZADO MULTI-INSTANCIA
# =============================================================================
if __name__ == "__main__":
    # Lista de instancias a evaluar
    archivos_instancias = ['easy.txt', 'medium1.txt', 'medium2.txt', 'hard.txt']
    carpeta_instancias = 'instancias'
    n_ejecuciones = 10
    
    # Crear carpeta para guardar gráficos si no existe
    if not os.path.exists('graficos_resultados'):
        os.makedirs('graficos_resultados')

    for nombre_archivo in archivos_instancias:
        ruta = os.path.join(carpeta_instancias, nombre_archivo)
        nombre_base = nombre_archivo.split('.')[0]
        
        try:
            m, n, B, beneficios, costos, recursos_requeridos = leer_instancia(ruta)
        except FileNotFoundError:
            print(f"⚠️  Error: No se encontró la instancia '{ruta}'. Saltando...")
            continue

        print("\n" + "=" * 70)
        print(f"🚀 INICIANDO ANÁLISIS: {nombre_archivo.upper()} | Alt: {m} | Rec: {n} | B: {B}")
        print("=" * 70)

        # --- 1. Preparación de Soluciones Iniciales ---
        sol_inicial_det = greedy_determinista(m, B, beneficios, costos, recursos_requeridos)
        
        soluciones_iniciales_est = []
        for i in range(n_ejecuciones):
            sol_est = greedy_estocastico(m, B, beneficios, costos, recursos_requeridos, semilla=i*10)
            soluciones_iniciales_est.append(sol_est)

        # --- 2. Experimento SA con inicio Determinista ---
        resultados_det_fo = []
        resultados_det_tiempo = []
        resultados_det_iters = []
        historiales_det = []

        for i in range(n_ejecuciones):
            t0 = time.time()
            _, best_fo, hist_mejor, iter_conv = simulated_annealing(
                m, B, beneficios, costos, recursos_requeridos, sol_inicial_det, semilla=i*100
            )
            t_ejec = time.time() - t0
            
            resultados_det_fo.append(best_fo)
            resultados_det_tiempo.append(t_ejec)
            resultados_det_iters.append(iter_conv)
            historiales_det.append(hist_mejor)

        # --- 3. Experimento SA con inicios Estocásticos ---
        resultados_est_fo = []
        resultados_est_tiempo = []
        resultados_est_iters = []
        historiales_est = []

        for i in range(n_ejecuciones):
            t0 = time.time()
            _, best_fo, hist_mejor, iter_conv = simulated_annealing(
                m, B, beneficios, costos, recursos_requeridos, soluciones_iniciales_est[i], semilla=i*100
            )
            t_ejec = time.time() - t0
            
            resultados_est_fo.append(best_fo)
            resultados_est_tiempo.append(t_ejec)
            resultados_est_iters.append(iter_conv)
            historiales_est.append(hist_mejor)

        # --- 4. Cálculo de Métricas y Salida por Consola ---
        def imprimir_metricas(nombre, fo_list, tiempo_list, iters_list):
            print(f"\n--- {nombre} ({n_ejecuciones} ejecuciones) ---")
            print(f" Mejor FO         : {max(fo_list)}")
            print(f" Peor FO          : {min(fo_list)}")
            print(f" Media de FO      : {statistics.mean(fo_list):.2f}")
            print(f" Desviación Std   : {statistics.stdev(fo_list):.2f}")
            print(f" Tiempo Medio     : {statistics.mean(tiempo_list):.4f} s")
            print(f" Iteración Media  : {statistics.mean(iters_list):.0f} (Velocidad de Convergencia)")

        imprimir_metricas("SA - Inicio Determinista", resultados_det_fo, resultados_det_tiempo, resultados_det_iters)
        imprimir_metricas("SA - Inicio Estocástico", resultados_est_fo, resultados_est_tiempo, resultados_est_iters)

        # --- 5. Generación de Gráficos ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Gráfico 1: Boxplot de FO Final
        ax1.boxplot([resultados_det_fo, resultados_est_fo], labels=['SA Determinista', 'SA Estocástico'], patch_artist=True)
        ax1.set_ylabel('Beneficio Final (FO)')
        ax1.set_title(f'Distribución de FO ({nombre_archivo})')
        ax1.grid(axis='y', alpha=0.5)

        # Gráfico 2: Convergencia Promedio
        promedio_hist_det = [sum(x)/n_ejecuciones for x in zip(*historiales_det)]
        promedio_hist_est = [sum(x)/n_ejecuciones for x in zip(*historiales_est)]

        ax2.plot(promedio_hist_det, color='crimson', label='Media SA Determinista')
        ax2.plot(promedio_hist_est, color='dodgerblue', label='Media SA Estocástico')
        ax2.set_xlabel('Iteraciones')
        ax2.set_ylabel('Mejor Beneficio Promedio (FO)')
        ax2.set_title(f'Velocidad de Convergencia Promedio ({nombre_archivo})')
        ax2.legend()
        ax2.grid(alpha=0.3)

        plt.tight_layout()
        
        ruta_grafico = f'graficos_resultados/analisis_SA_{nombre_base}.png'
        plt.savefig(ruta_grafico, dpi=150)
        plt.close(fig) # Cierra la figura para liberar memoria antes de la siguiente instancia
        
        print(f"\n✅ Análisis completado. Gráfico guardado en: '{ruta_grafico}'")