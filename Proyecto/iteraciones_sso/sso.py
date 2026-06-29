import random
import os
import time

contador_infactibles = 0
contador_factibles = 0
contador_soluciones = 0

# 1. PARSER: Lector del formato de Hao
def leer_instancia_hao(filepath):
    with open(filepath, 'r') as f:
        # Leemos todo y lo separamos por espacios (ignora saltos de línea y múltiples espacios)
        data = f.read().split()
    
    iterator = iter(data)
    
    n = int(next(iterator)) # Número de grupos
    l = int(next(iterator)) # Número de ítems por grupo
    m = int(next(iterator)) # Número de recursos (dimensiones)
    
    # Capacidades de las mochilas
    capacidades = [float(next(iterator)) for _ in range(m)]
    
    grupos = []
    for i in range(n):
        id_grupo = next(iterator) # Ignoramos el índice del grupo ('1', '2', etc.)
        items = []
        for j in range(l):
            beneficio = float(next(iterator))
            pesos = [float(next(iterator)) for _ in range(m)]
            items.append({'beneficio': beneficio, 'pesos': pesos})
        grupos.append(items)
        
    return n, l, m, capacidades, grupos

# 2. FUNCIÓN DE EVALUACIÓN (CON PENALIZACIÓN)
def calcular_fitness(posicion, grupos, capacidades, m, factor_penalizacion=1000):
    beneficio_total = 0
    pesos_totales = [0] * m
    
    # Sumar beneficios y recursos consumidos
    for idx_grupo, idx_item in enumerate(posicion):
        item = grupos[idx_grupo][idx_item]
        beneficio_total += item['beneficio']
        for r in range(m):
            pesos_totales[r] += item['pesos'][r]
            
    # Calcular si nos pasamos del límite de las mochilas
    violacion_total = 0
    es_factible = True
    for r in range(m):
        if pesos_totales[r] > capacidades[r]:
            violacion_total += (pesos_totales[r] - capacidades[r])
            es_factible = False

    global contador_soluciones, contador_factibles, contador_infactibles
    contador_soluciones += 1
    
    if es_factible:
        contador_factibles += 1
    else:
        contador_infactibles += 1

    # Si no reparamos, debemos castigar severamente las soluciones inválidas
    fitness = beneficio_total - (factor_penalizacion * violacion_total)
    
    return fitness, es_factible, beneficio_total

# 3. ALGORITMO SIMPLIFIED SWARM OPTIMIZATION
class Particula: 
    def __init__(self, n, l):
        # La posición es un arreglo de tamaño 'n' (grupos). 
        # Cada valor es un entero entre 0 y l-1 (el ítem elegido).
        # Cada particula es una solucion
        # Se puede aplicar un greedy para la solucion inicial
        self.posicion = [random.randint(0, l - 1) for _ in range(n)]
        self.pbest_posicion = list(self.posicion)
        self.pbest_fitness = -float('inf')
        self.fitness = -float('inf')
        self.es_factible = False

def sso_mmkp(n, l, m, capacidades, grupos, num_particulas, max_generaciones):
    # Probabilidades de SSO
    Cw = 0.10 # Mantener estado actual
    Cp = 0.40 # Copiar mejor personal (pBest)
    Cg = 0.40 # Copiar mejor global (gBest)
    # Cr = 0.10 # Aleatorio (Implícito al final)
    
    # Generacion de la poblacion inicial
    enjambre = []
    for i in range(num_particulas):
        enjambre.append(Particula(n, l))

    gbest_posicion = None
    gbest_fitness = -float('inf')
    gbest_beneficio = 0
    gbest_factible = False
    
    # Bucle de Generaciones
    for gen in range(max_generaciones):
        for particula in enjambre:
            # 1. Evaluar la partícula actual
            fitness, factible, beneficio = calcular_fitness(particula.posicion, grupos, capacidades, m)
            particula.fitness = fitness
            particula.es_factible = factible
            
            # 2. Actualizar pBest (Mejor personal)
            if fitness > particula.pbest_fitness:
                particula.pbest_fitness = fitness
                particula.pbest_posicion = list(particula.posicion)
                
            # 3. Actualizar gBest (Mejor global)
            if fitness > gbest_fitness:
                gbest_fitness = fitness
                gbest_posicion = list(particula.posicion)
                gbest_beneficio = beneficio
                gbest_factible = factible
                
        # 4. Actualizar posiciones (movimiento del enjambre según reglas de SSO)
        for particula in enjambre:
            nueva_posicion = []
            for d in range(n): # iteramos sobre cada grupo
                r = random.random()
                if r < Cw:
                    nueva_posicion.append(particula.posicion[d])
                elif r < Cw + Cp:
                    nueva_posicion.append(particula.pbest_posicion[d])
                elif r < Cw + Cp + Cg:
                    nueva_posicion.append(gbest_posicion[d])
                else:
                    nueva_posicion.append(random.randint(0, l - 1))
            
            particula.posicion = nueva_posicion
            
        if (gen + 1) % 100 == 0:
            estado = "Factible" if gbest_factible else "Infactible"
            print(f"Generación {gen + 1:4d} | Fitness: {gbest_fitness:10.2f} | Beneficio Real: {gbest_beneficio:8.2f} | Estado: {estado}")
            
    return gbest_posicion, gbest_beneficio, gbest_factible

# 4. BLOQUE DE EJECUCIÓN
if __name__ == "__main__":
    archivo_instancia = "./material/ClassicINST/I07.txt" 
    
    if os.path.exists(archivo_instancia):
        print(f"Cargando instancia: {archivo_instancia}...")
        n, l, m, capacidades, grupos = leer_instancia_hao(archivo_instancia)
        
        print(f"Grupos (n): {n}, Ítems por grupo (l): {l}, Recursos (m): {m}")
        print("Iniciando SSO...")
        
        # Ejecutamos el algoritmo
        t_inicio = time.perf_counter()
        mejor_solucion, mejor_beneficio, es_factible = sso_mmkp(
            n, l, m, capacidades, grupos, 
            num_particulas=25, 
            max_generaciones=2000
        )
        t_fin = time.perf_counter()
        t_ejecucion = t_fin - t_inicio

        #Calculando % de factibilidad
        porcentaje_factibilidad = 0
        if contador_soluciones > 0:
            porcentaje_factibilidad = (contador_factibles / contador_soluciones) * 100 
        

        print("\n--- RESULTADO FINAL ---")
        print(f"Tiempo de ejecución: {t_ejecucion:.2f} segundos")
        print(f"Total de soluciones infactibles encontradas: {contador_infactibles}")
        print(f"Total de soluciones factibles encontradas: {contador_factibles}")
        print(f"Total de soluciones evaluadas: {contador_soluciones}")
        print(f"Porcentaje de soluciones factibles: {porcentaje_factibilidad:.2f}%")
        print("---------------------------------")
        print(f"Beneficio Encontrado: {mejor_beneficio}")
        print(f"¿Es una solución válida?: {'Sí' if es_factible else 'No (Modifica la penalización o agrega reparación)'}")
        print(f"Ítems seleccionados por grupo (índices): \n{mejor_solucion}")
    else:
        print(f"Por favor, descarga una instancia como '{archivo_instancia}' en la misma carpeta que este script para probarlo.")