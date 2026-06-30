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


def generar_vecino(solucion, m):
    global n_adds, n_removes, n_swaps
    solucion = set(solucion)
    todas_alternativas = set(range(m))

    no_seleccionadas = list(todas_alternativas - solucion)
    seleccionadas    = list(solucion)
    r = random.random()

    #agrega uno si hay disponibles.
    if r < 0.333:
        if no_seleccionadas:  
            solucion.add(random.choice(no_seleccionadas))
            n_adds += 1

    #elimina uno si aun quedan.
    elif r < 0.666:
        if seleccionadas: solucion.remove(random.choice(seleccionadas))
        n_removes += 1

    #elimina uno y agrega otro, si hay para agregar y quitar.
    else:
        if seleccionadas and no_seleccionadas: 
            solucion.remove(random.choice(seleccionadas))
            solucion.add(random.choice(no_seleccionadas))
            n_swaps += 1
    return solucion


def simulated_annealing(m, B, beneficios, costos, recursos_requeridos, T_inicial=1000.0, alpha=0.995, T_min=0.1, L=100, max_iter=None):
    
    solucion_actual = greedy_determinista(m, B, beneficios, costos, recursos_requeridos)

    mejor_solucion  = set(solucion_actual)
    mejor_beneficio = calcular_beneficio(mejor_solucion, beneficios)
    beneficio_actual = mejor_beneficio

    T = T_inicial
    iteracion = 0

    #listar para graficos
    historial_mejor    = []
    historial_actual   = []

    while T > T_min:
        if max_iter is not None and iteracion >= max_iter:
            break

        for _ in range(L):
            iteracion += 1

            #generar vecino
            vecino = generar_vecino(solucion_actual, m)
            print(f"Iteración {iteracion}: vecino generado = {vecino}")

            #si es infactible se vuelve a generar
            if not es_factible(vecino, recursos_requeridos, costos, B):
                continue

            beneficio_vecino = calcular_beneficio(vecino, beneficios)
            delta = beneficio_vecino - beneficio_actual  # positivo = mejora

            if delta > 0:
                #se acepta inmediatamente si mejora
                solucion_actual  = vecino
                beneficio_actual = beneficio_vecino

                if beneficio_actual > mejor_beneficio:
                    mejor_solucion  = set(solucion_actual)
                    mejor_beneficio = beneficio_actual

            else:
                #se acepta con probabilidad e^(delta/T)
                prob = math.exp(delta / T)
                print(f"Iteración {iteracion}: delta = {delta}, T = {T:.4f}, probabilidad de aceptación = {prob:.4f}")
                if random.random() < prob:
                    solucion_actual  = vecino
                    beneficio_actual = beneficio_vecino

            historial_actual.append(beneficio_actual)
            historial_mejor.append(mejor_beneficio)

        #enfriamiento
        T *= alpha

    return mejor_solucion, mejor_beneficio, historial_actual, historial_mejor



ruta = 'instancias/hard.txt'
m, n, B, beneficios, costos, recursos_requeridos = leer_instancia(ruta)

print("=" * 55)
print(f"  Instancia cargada: {m} alternativas, {n} recursos, B={B}")
print("=" * 55)


t_inicial = time.time()
mejor_sol, mejor_ben, hist_actual, hist_mejor = simulated_annealing(m, 
                                                                    B, 
                                                                    beneficios, 
                                                                    costos, 
                                                                    recursos_requeridos, 
                                                                    T_inicial = 1000.0, 
                                                                    alpha= 0.995,
                                                                    T_min     = 0.1,
                                                                    L= 100)
t_final = time.time()

costo_final = calcular_costo(mejor_sol, recursos_requeridos, costos)
print(f"\n[Simulated Annealing]")
print(f"  Beneficio final  : {mejor_ben}")
print(f"  Costo total usado: {costo_final} / {B}")
print(f"  Alternativas sel.: {sorted(mejor_sol)}")
print(f"  Tiempo ejecución : {t_final - t_inicial:.3f} s")
print(f"  Iteraciones total: {len(hist_actual)}")
print(f"  Movimientos: Adds={n_adds}, Removes={n_removes}, Swaps={n_swaps}")

    # -- Gráfico FO vs Iteraciones --
plt.figure(figsize=(10, 5))
plt.plot(hist_actual, color='steelblue', alpha=0.5, linewidth=0.8, label='Solución actual')
plt.plot(hist_mejor,  color='crimson',   linewidth=1.5, label='Mejor solución')
plt.xlabel('Iteraciones')
plt.ylabel('Beneficio (FO)')
plt.title(f'Simulated Annealing — Convergencia ({ruta.split("/")[-1]})')
plt.legend()
plt.tight_layout()
plt.savefig('convergencia_SA.png', dpi=150)
plt.show()
print("\n  Gráfico guardado en convergencia_SA.png")