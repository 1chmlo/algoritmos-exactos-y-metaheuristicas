import random
import os
import time

contador_infactibles = 0
contador_factibles = 0
contador_soluciones = 0

# 1. PARSER: Lector del formato de Hao
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

# 2. INICIALIZACIÓN GREEDY (SEMILLA)
def generar_solucion_greedy(grupos, n, l):
    """
    Genera una solución inicial eligiendo el ítem con el mejor 
    ratio (Beneficio / Suma de Pesos) para cada grupo.
    """
    solucion_greedy = []
    for i in range(n):
        mejor_item = 0
        mejor_ratio = -float('inf')
        
        for j in range(l):
            beneficio = grupos[i][j]['beneficio']
            suma_pesos = sum(grupos[i][j]['pesos'])
            
            # Calculamos la eficiencia del ítem (evitamos división por 0)
            ratio = beneficio / suma_pesos if suma_pesos > 0 else beneficio
            
            if ratio > mejor_ratio:
                mejor_ratio = ratio
                mejor_item = j
                
        solucion_greedy.append(mejor_item)
    return solucion_greedy

# 3. ALGORITMO DE REPARACIÓN
def reparar_solucion(solucion, grupos, capacidades, n, l, m):
    """
    Intenta reparar una solución infactible intercambiando ítems por otros
    en sus respectivos grupos que consuman menos recursos.
    """
    solucion_reparada = list(solucion)
    
    while True:
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
        else:
            return solucion_reparada, False

# 4. FUNCIÓN DE EVALUACIÓN
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

# 5. ALGORITMO SIMPLIFIED SWARM OPTIMIZATION
class Particula:
    def __init__(self, n, l, solucion_inicial=None):
        if solucion_inicial is not None:
            self.solucion = list(solucion_inicial)
        else:
            self.solucion = [random.randint(0, l - 1) for _ in range(n)]
            
        self.pbest_solucion = list(self.solucion)
        self.pbest_fitness = -float('inf')
        self.fitness = -float('inf')
        self.es_factible = False

def sso_mmkp(n, l, m, capacidades, grupos, num_particulas=50, max_generaciones=1000):
    Cw = 0.10
    Cp = 0.20
    Cg = 0.20
    
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
            continue
            
        for particula in enjambre:
            nueva_solucion = []
            for d in range(n): 
                r = random.random()
                if r < Cw:
                    nueva_solucion.append(particula.solucion[d])
                elif r < Cw + Cp:
                    nueva_solucion.append(particula.pbest_solucion[d])
                elif r < Cw + Cp + Cg:
                    nueva_solucion.append(gbest_solucion[d])
                else:
                    nueva_solucion.append(random.randint(0, l - 1))
            
            particula.solucion = nueva_solucion
            
        if (gen + 1) % 100 == 0:
            estado = "Factible" if gbest_factible else "Ninguna Factible"
            print(f"Generación {gen + 1:4d} | Mejor Beneficio: {gbest_beneficio:8.2f} | Estado: {estado}")
            
    return gbest_solucion, gbest_beneficio, gbest_factible

# 6. BLOQUE DE EJECUCIÓN
if __name__ == "__main__":
    archivo_instancia = "INST20.txt" 
    
    if os.path.exists(archivo_instancia):
        print(f"Cargando instancia: {archivo_instancia}")
        n, l, m, capacidades, grupos = leer_instancia_hao(archivo_instancia)
        
        print(f"Grupos (n): {n}, Ítems por grupo (l): {l}, Recursos (m): {m}")
        print("Iniciando SSO con Reparación y Greedy")
        
        # --- INICIO DEL TEMPORIZADOR ---
        tiempo_inicio = time.time()
        
        mejor_solucion, mejor_beneficio, es_factible = sso_mmkp(
            n, l, m, capacidades, grupos, 
            num_particulas=15, 
            max_generaciones=2000
        )
        
        # --- FIN DEL TEMPORIZADOR ---
        tiempo_fin = time.time()
        tiempo_total = tiempo_fin - tiempo_inicio
        
        print("\n--- RESULTADO FINAL ---")
        print(f"Tiempo total de ejecución: {tiempo_total:.4f} segundos") # <-- Mostramos el tiempo
        print(f"Total de soluciones irreparables (infactibles): {contador_infactibles}")
        print(f"Total de soluciones evaluadas como factibles: {contador_factibles}")
        print(f"Total de evaluaciones: {contador_soluciones}")
        print(f"Beneficio Encontrado: {mejor_beneficio}")
        print(f"¿Es una solución válida?: {'Sí' if es_factible else 'No'}")
        print(f"Ítems seleccionados por grupo (índices): \n{mejor_solucion}")
    else:
        print(f"Archivo '{archivo_instancia}' no encontrado.")