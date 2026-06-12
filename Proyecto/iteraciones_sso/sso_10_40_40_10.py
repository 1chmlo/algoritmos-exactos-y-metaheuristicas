import random
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt

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
        pesos_totales = [0] * m
        for idx_grupo, idx_item in enumerate(solucion_reparada):
            item = grupos[idx_grupo][idx_item]
            for r in range(m):
                pesos_totales[r] += item['pesos'][r]
                
        violacion_total = sum(max(0, pesos_totales[r] - capacidades[r]) for r in range(m))
        
        if violacion_total == 0:
            return solucion_reparada, True 
            
        mejor_intercambio = None
        mejor_reduccion_violacion = 0
        
        for i in range(n):
            item_actual = solucion_reparada[i]
            pesos_actuales = grupos[i][item_actual]['pesos']
            
            for j in range(l):
                if j == item_actual: 
                    continue
                
                pesos_candidatos = grupos[i][j]['pesos']
                nueva_violacion_total = 0
                for r in range(m):
                    nuevo_peso_r = pesos_totales[r] - pesos_actuales[r] + pesos_candidatos[r]
                    nueva_violacion_total += max(0, nuevo_peso_r - capacidades[r])
                    
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
        beneficio_total = sum(grupos[i][solucion[i]]['beneficio'] for i in range(len(solucion)))
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
            nueva_solucion = []
            for d in range(n): 
                r = random.random()
                if r < p_mantener:
                    nueva_solucion.append(particula.solucion[d])
                elif r < p_mantener + p_pbest:
                    nueva_solucion.append(particula.pbest_solucion[d])
                elif r < p_mantener + p_pbest + p_gbest:
                    nueva_solucion.append(gbest_solucion[d])
                else:
                    nueva_solucion.append(random.randint(0, l - 1))
            
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
    instancia = "I07"
    archivo_instancia = f"instancias/{instancia}.txt" 
    
    if os.path.exists(archivo_instancia):
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta_salida = f"Resultados/{instancia}_{fecha_str}_10_40_40_10"
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"Directorio de resultados creado: {carpeta_salida}/\n")
        
        print(f"Cargando instancia: {archivo_instancia}")
        n, l, m, capacidades, grupos = leer_instancia_hao(archivo_instancia)
        
        print(f"Grupos (n): {n}, Ítems por grupo (l): {l}, Recursos (m): {m}")
        print("Iniciando SSO con Reparación y Greedy...")
        
        tiempo_inicio = time.time()
        
        particulas = 25
        generaciones = 2000
        p_mantener = 0.10
        p_pbest = 0.40
        p_gbest = 0.40


        mejor_solucion, mejor_beneficio, es_factible, historial = sso_mmkp(
            n, l, m, capacidades, grupos, 
            num_particulas=particulas, 
            max_generaciones=generaciones,
            p_mantener=p_mantener,
            p_pbest=p_pbest,
            p_gbest=p_gbest
        )
        
        tiempo_fin = time.time()
        tiempo_total = tiempo_fin - tiempo_inicio
        
        print("\nGenerando gráficas PNG...")
        generar_y_guardar_graficos(historial, contador_factibles, contador_infactibles, carpeta_salida, archivo_instancia)
        
        resumen = (
            f"\n--- RESULTADO FINAL ---\n"
            f"Instancia: {instancia}\n"
            f"Generaciones: {generaciones} | Partículas: {particulas}\n"
            f"Probabilidades - Mantener: {p_mantener:.2f}, PBest: {p_pbest:.2f}, GBest: {p_gbest:.2f}, Aleatorio: {1 - p_mantener - p_pbest - p_gbest:.2f}\n"

            f"Tiempo total de ejecución: {tiempo_total:.4f} segundos\n"
            f"Total de soluciones irreparables (infactibles): {contador_infactibles}\n"
            f"Total de soluciones evaluadas como factibles: {contador_factibles}\n"
            f"Total de evaluaciones: {contador_soluciones}\n"
            f"Beneficio Encontrado: {mejor_beneficio}\n"
            f"¿Es una solución válida?: {'Sí' if es_factible else 'No'}\n"
            f"Ítems seleccionados por grupo (índices): \n{mejor_solucion}\n"
        )
        
        print(resumen)
        
        ruta_txt = os.path.join(carpeta_salida, "resumen.txt")
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(resumen)
            
        print(f"¡Listo! Puedes revisar las gráficas y el resumen (.txt) en la carpeta: {carpeta_salida}")
    else:
        print(f"Archivo '{archivo_instancia}' no encontrado.")