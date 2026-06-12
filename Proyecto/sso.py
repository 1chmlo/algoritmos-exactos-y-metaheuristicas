import random
import os
import time
import csv
import statistics
from datetime import datetime
import matplotlib.pyplot as plt

contador_infactibles = 0
contador_factibles = 0
contador_soluciones = 0

def reset_contadores():
    global contador_infactibles, contador_factibles, contador_soluciones
    contador_infactibles = 0
    contador_factibles = 0
    contador_soluciones = 0

# 1. Leer instancias
def leer_instancia_hao(filepath):
    with open(filepath, 'r') as f:
        data = f.read().split()
    
    iterator = iter(data)
    
    n = int(next(iterator))
    l = int(next(iterator))
    m = int(next(iterator))
    
    capacidades = [float(next(iterator)) for _ in range(m)]
    
    grupos = []
    for i in range(n):
        id_grupo = next(iterator)
        items = []
        for j in range(l):
            beneficio = float(next(iterator))
            pesos = [float(next(iterator)) for _ in range(m)]
            items.append({'beneficio': beneficio, 'pesos': pesos})
        grupos.append(items)
        
    return n, l, m, capacidades, grupos

# 2. Greedy para generar una solución inicial
def generar_solucion_greedy(grupos, n, l):
    solucion_greedy = []
    for i in range(n):
        mejor_item = 0
        mejor_ratio = -float('inf')
        
        for j in range(l):
            beneficio = grupos[i][j]['beneficio']
            suma_pesos = sum(grupos[i][j]['pesos'])
            
            ratio = beneficio / suma_pesos if suma_pesos > 0 else beneficio
            
            if ratio > mejor_ratio:
                mejor_ratio = ratio
                mejor_item = j
                
        solucion_greedy.append(mejor_item)
    return solucion_greedy

# 3. Intentar reparar soluciones infactibles 
def reparar_solucion(solucion, grupos, capacidades, n, l, m, max_intentos=5):
    solucion_reparada = list(solucion)
    intentos = 0
    
    while intentos < max_intentos:
        pesos_totales = [0.0] * m
        for i, idx_item in enumerate(solucion_reparada):
            pesos_item = grupos[i][idx_item]['pesos']
            for r in range(m):
                pesos_totales[r] += pesos_item[r]
                
        violacion_total = 0.0
        for r in range(m):
            diff = pesos_totales[r] - capacidades[r]
            if diff > 0:
                violacion_total += diff
        
        if violacion_total == 0:
            return solucion_reparada, True 
            
        mejor_intercambio = None
        mejor_reduccion_violacion = 0.0
        
        for i in range(n):
            item_actual = solucion_reparada[i]
            pesos_actuales = grupos[i][item_actual]['pesos']
            
            for j in range(l):
                if j == item_actual: 
                    continue
                
                pesos_candidatos = grupos[i][j]['pesos']
                nueva_violacion_total = 0.0
                
                for r in range(m):
                    nuevo_peso_r = pesos_totales[r] - pesos_actuales[r] + pesos_candidatos[r]
                    diff = nuevo_peso_r - capacidades[r]
                    if diff > 0:
                        nueva_violacion_total += diff
                        
                    if nueva_violacion_total >= (violacion_total - mejor_reduccion_violacion):
                        break 
                else:
                    reduccion = violacion_total - nueva_violacion_total
                    if reduccion > mejor_reduccion_violacion:
                        mejor_reduccion_violacion = reduccion
                        mejor_intercambio = (i, j)
        
        if mejor_intercambio:
            grupo_a_cambiar, nuevo_item = mejor_intercambio
            solucion_reparada[grupo_a_cambiar] = nuevo_item
            intentos += 1
        else:
            return solucion_reparada, False
            
    return solucion_reparada, False

# 4. Evaluar fitness de una solución 
def calcular_fitness(solucion, grupos, factible):
    global contador_soluciones, contador_factibles, contador_infactibles
    contador_soluciones += 1
    
    if factible:
        contador_factibles += 1
        beneficio_total = sum(grupos[i][item]['beneficio'] for i, item in enumerate(solucion))
        return beneficio_total, beneficio_total
    else:
        contador_infactibles += 1
        return -float('inf'), 0

# 5. Simplified Swarm Optimization 
class Particula:
    def __init__(self, n, l, solucion_inicial=None):
        self.es_factible = False
        if solucion_inicial is not None:
            self.solucion = list(solucion_inicial)
        else:
            self.solucion = [random.randint(0, l - 1) for _ in range(n)]
            
        self.pbest_solucion = list(self.solucion)
        self.pbest_fitness = -float('inf')
        self.fitness = -float('inf')
        

def sso_mmkp(n, l, m, capacidades, grupos, num_particulas=50, max_generaciones=1000, p_mantener=0.01, p_pbest=0.48, p_gbest=0.48):
    
    semilla_greedy = generar_solucion_greedy(grupos, n, l)
    
    enjambre = []
    for i in range(num_particulas):
        if i == 0:
            enjambre.append(Particula(n, l, solucion_inicial=semilla_greedy))
        else:
            enjambre.append(Particula(n, l))
    
    gbest_solucion = None
    gbest_fitness = -float('inf')
    gbest_beneficio = 0
    gbest_factible = False
    
    historial_convergencia = []
    
    umbral_1 = p_mantener
    umbral_2 = p_mantener + p_pbest
    umbral_3 = p_mantener + p_pbest + p_gbest

    for gen in range(max_generaciones):
        for particula in enjambre:
            particula.solucion, particula.es_factible = reparar_solucion(
                particula.solucion, grupos, capacidades, n, l, m
            )
            
            fitness, beneficio = calcular_fitness(particula.solucion, grupos, particula.es_factible)
            particula.fitness = fitness
            
            if fitness > particula.pbest_fitness and particula.es_factible:
                particula.pbest_fitness = fitness
                particula.pbest_solucion = list(particula.solucion)
                
            if fitness > gbest_fitness and particula.es_factible:
                gbest_fitness = fitness
                gbest_solucion = list(particula.solucion)
                gbest_beneficio = beneficio
                gbest_factible = True
                
        if gbest_solucion is None:
            historial_convergencia.append(0)
            continue
            
        historial_convergencia.append(gbest_beneficio)
            
        for particula in enjambre:
            nueva_solucion = [0] * n
            sol_actual = particula.solucion
            pbest_actual = particula.pbest_solucion
            
            for d in range(n): 
                r = random.random()
                if r < umbral_1:
                    nueva_solucion[d] = sol_actual[d]
                elif r < umbral_2:
                    nueva_solucion[d] = pbest_actual[d]
                elif r < umbral_3:
                    nueva_solucion[d] = gbest_solucion[d]
                else:
                    nueva_solucion[d] = random.randint(0, l - 1)
            
            particula.solucion = nueva_solucion
            
        if (gen + 1) % 100 == 0:
            estado = "Factible" if gbest_factible else "Ninguna Factible"
            print(f"Generación {gen + 1:4d} | Mejor Beneficio: {gbest_beneficio:8.2f} | Estado: {estado}")
            
    return gbest_solucion, gbest_beneficio, gbest_factible, historial_convergencia

# 6. Graficos
def generar_y_guardar_graficos(historial, factibles, infactibles, carpeta, archivo_instancia):
    """Genera las gráficas de la ejecución y las guarda en PNG."""
    
    # Gráfica 1: Curva de Convergencia
    plt.figure(figsize=(10, 6))
    plt.plot(historial, color='#2ca02c', linewidth=2, label='Mejor Beneficio Global')
    plt.title(f'Curva de Convergencia del Algoritmo SSO - {archivo_instancia}', fontsize=14)
    plt.xlabel('Generaciones', fontsize=12)
    plt.ylabel('Beneficio (Fitness)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, '01_convergencia.png'), dpi=300)
    plt.close()

    # Gráfica 2: Proporción de Factibilidad
    plt.figure(figsize=(8, 6))
    etiquetas = ['Factibles', 'Infactibles']
    valores = [factibles, infactibles]
    colores = ['#4CAF50', '#F44336']
    explode = (0.1, 0)
    
    # Solo graficar si hay datos para evitar errores
    if sum(valores) > 0:
        plt.pie(valores, explode=explode, labels=etiquetas, colors=colores, 
                autopct='%1.1f%%', shadow=True, startangle=140, textprops={'fontsize': 12})
        plt.title(f'Proporción de Soluciones Exploradas - {archivo_instancia}', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(carpeta, '02_factibilidad.png'), dpi=300)
    plt.close()

# 7. Ejecucion y prints

if __name__ == "__main__":
    carpeta_instancias = "instancias"
    if not os.path.exists(carpeta_instancias):
        print(f"La carpeta '{carpeta_instancias}' no existe.")
        exit()

    archivos_instancias = [f for f in os.listdir(carpeta_instancias) if f.endswith('.txt')]
    if not archivos_instancias:
        print(f"No se encontraron instancias en '{carpeta_instancias}'.")
        exit()
        
    n_ejecuciones = 5 # N veces que se ejecuta cada instancia
    
    fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta_salida_global = f"Resultados/Experimento_{n_ejecuciones}runs_{fecha_str}"
    os.makedirs(carpeta_salida_global, exist_ok=True)
    
    # Parámetros del SSO
    particulas = 25
    generaciones = 2000
    p_mantener = 0.10
    p_pbest = 0.40
    p_gbest = 0.40

    csv_path = os.path.join(carpeta_salida_global, "resumen_global.csv")
    with open(csv_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow([
            "Instancia", "N_Ejecuciones", "Mejor_Beneficio_Global", 
            "Media_Beneficio", "Min_Beneficio", "Desv_Est_Beneficio",
            "Media_Tiempo(s)", "Media_Factibles", "Media_Infactibles"
        ])
        
        for archivo in archivos_instancias:
            instancia_nombre = archivo.replace('.txt', '')
            archivo_instancia = os.path.join(carpeta_instancias, archivo)
            
            print(f"Procesando instancia: {instancia_nombre} ({n_ejecuciones} ejecuciones)")
            
            
            n, l, m, capacidades, grupos = leer_instancia_hao(archivo_instancia)
            
            beneficios_ejecuciones = []
            tiempos_ejecuciones = []
            factibles_ejecuciones = []
            infactibles_ejecuciones = []
            
            mejor_solucion_global = None
            mejor_beneficio_global = -float('inf')
            mejor_historial = None
            
            for ejecucion in range(n_ejecuciones):
                reset_contadores()
                tiempo_inicio = time.time()
                
                mejor_solucion, mejor_beneficio, es_factible, historial = sso_mmkp(
                    n, l, m, capacidades, grupos, 
                    num_particulas=particulas, 
                    max_generaciones=generaciones,
                    p_mantener=p_mantener,
                    p_pbest=p_pbest,
                    p_gbest=p_gbest
                )
                
                tiempo_total = time.time() - tiempo_inicio
                
                if mejor_beneficio > mejor_beneficio_global and es_factible:
                    mejor_beneficio_global = mejor_beneficio
                    mejor_solucion_global = mejor_solucion
                    mejor_historial = historial
                
                beneficios_ejecuciones.append(mejor_beneficio if es_factible else 0)
                tiempos_ejecuciones.append(tiempo_total)
                factibles_ejecuciones.append(contador_factibles)
                infactibles_ejecuciones.append(contador_infactibles)
                
                print(f"  Ejec. {ejecucion+1}/{n_ejecuciones} | Beneficio: {mejor_beneficio if es_factible else 0:.2f} | Tiempo: {tiempo_total:.2f}s")
                
            # Estadísticas
            media_beneficio = statistics.mean(beneficios_ejecuciones)
            min_beneficio = min(beneficios_ejecuciones)
            max_beneficio = max(beneficios_ejecuciones)
            desv_beneficio = statistics.stdev(beneficios_ejecuciones) if n_ejecuciones > 1 else 0.0
            
            media_tiempo = statistics.mean(tiempos_ejecuciones)
            media_factibles = statistics.mean(factibles_ejecuciones)
            media_infactibles = statistics.mean(infactibles_ejecuciones)
            
            writer.writerow([
                instancia_nombre, n_ejecuciones, max_beneficio, 
                media_beneficio, min_beneficio, desv_beneficio,
                media_tiempo, media_factibles, media_infactibles
            ])
            
            resumen_instancia = (
                f"--- RESUMEN DE LA INSTANCIA: {instancia_nombre} ---\n"
                f"Archivos analizados: 1 ({archivo})\n"
                f"Ejecuciones: {n_ejecuciones}\n\n"
                f"--- ESTADÍSTICAS DEL BENEFICIO ---\n"
                f"Mejor Beneficio Encontrado: {max_beneficio}\n"
                f"Peor Beneficio Encontrado: {min_beneficio}\n"
                f"Media del Beneficio: {media_beneficio:.2f}\n"
                f"Desviación Estándar: {desv_beneficio:.2f}\n\n"
                f"--- OTRAS MÉTRICAS PROMEDIO ---\n"
                f"Tiempo de ejecución medio: {media_tiempo:.4f} segundos\n"
                f"Soluciones Factibles exploradas (media): {media_factibles:.1f}\n"
                f"Soluciones Infactibles exploradas (media): {media_infactibles:.1f}\n\n"
            )
            if mejor_solucion_global:
                resumen_instancia += f"Mejor Solución Global Encontrada (índices):\n{mejor_solucion_global}\n"
            else:
                resumen_instancia += "No se encontró ninguna solución factible en las ejecuciones.\n"
                
            ruta_txt = os.path.join(carpeta_salida_global, f"resumen_{instancia_nombre}.txt")
            with open(ruta_txt, 'w') as f_resumen:
                f_resumen.write(resumen_instancia)
                
            # Gráficos solo para la mejor ejecución de esta instancia
            if mejor_historial:
                mejor_idx = beneficios_ejecuciones.index(max_beneficio)
                generar_y_guardar_graficos(
                    mejor_historial, 
                    factibles_ejecuciones[mejor_idx], 
                    infactibles_ejecuciones[mejor_idx], 
                    carpeta_salida_global, 
                    instancia_nombre
                )
                # Renombrar archivos generados para incluir el nombre de la instancia
                os.rename(os.path.join(carpeta_salida_global, '01_convergencia.png'), os.path.join(carpeta_salida_global, f'{instancia_nombre}_convergencia.png'))
                if os.path.exists(os.path.join(carpeta_salida_global, '02_factibilidad.png')):
                    os.rename(os.path.join(carpeta_salida_global, '02_factibilidad.png'), os.path.join(carpeta_salida_global, f'{instancia_nombre}_factibilidad.png'))

    print(f"\nEjecución finalizada. Archivo de resumen CSV generado en: {csv_path}")