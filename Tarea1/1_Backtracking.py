import os
import time
import csv
import matplotlib.pyplot as plt
from datetime import datetime

# CONFIGURACION PARA GUARDAR FOTOS DE LOS GRAFICOS
NOMBRE_ARCHIVO = 'case1.txt'
cantidad_pistas = 3
nombre_base = os.path.splitext(NOMBRE_ARCHIVO)[0] 
fecha_ejecucion = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CARPETA_RESULTADOS = os.path.join(os.path.dirname(__file__), 'resultados_BT', f"{nombre_base}_{fecha_ejecucion}")
os.makedirs(CARPETA_RESULTADOS, exist_ok=True)


# Leyendo archivos e instanciando aviones
with open(os.path.join(os.path.dirname(__file__), NOMBRE_ARCHIVO)) as caso:
    valores = caso.read().split()
    D = int(valores[0])
    idx = 1
    aviones = []
    Tij_global = []

    for i in range(D):
        Ek = int(valores[idx])
        Pk = int(valores[idx+1])
        Lk = int(valores[idx+2])
        pen_early = float(valores[idx+3]) 
        pen_tardy = float(valores[idx+4]) 
        idx += 5
        Tij = []
        for j in range(D):
            Tij.append(int(valores[idx]))
            idx += 1
        Tij_global.append(Tij)    
        aviones.append({
            'id': i+1,
            'primer_tiempo': Ek,
            'tiempo_esperado': Pk,
            'ultimo_tiempo': Lk,
            'dominio': Lk-Ek+1,
            'costo_temprano': pen_early,
            'costo_tarde': pen_tardy,
            'Tij': Tij, #arreglo
        })
        
    #print(f"Total de aviones leídos (D): {D}")
    #print("\nInformación del primer avión cargado:")
    #print(aviones)


#Aqui los aviones ya estan definidos y se puede acceder a cualquier avion con aviones[i]['atributo']

mejor_costo = float('inf') 
mejor_secuencia = None    
mejoramiento = [] # guardar como mejoran las secuencias en orden

#Arreglo
def calcular_costo_arr(secuencia):
    global mejor_costo
    costo_total = 0
    
    for i in range(len(secuencia)):
        tiempo_esperado = secuencia[i][2]
        tiempo_llegada = secuencia[i][1]
        desfase = abs(tiempo_esperado-tiempo_llegada)
        costo_tarde = secuencia[i][3]
        costo_temprano = secuencia[i][4]

        #A tiempo
        if tiempo_llegada == tiempo_esperado : continue
        #Tarde
        if tiempo_llegada > tiempo_esperado : costo_total += desfase * costo_tarde
        #Temprano
        else: costo_total += desfase * costo_temprano



    return int(costo_total)


def es_menor_costo(costo_actual, secuencia):
    global mejor_costo
    global mejor_secuencia
    global mejoramiento
    global costos_nodos, costos_tiempo, contador_nodos
    if costo_actual < mejor_costo: 
        mejor_costo = int(costo_actual)
        mejor_secuencia = secuencia.copy()
        mejoramiento.append(mejor_costo)
        return True
    else: return False

def es_valido(avion_nuevo, tiempo_nuevo, pista_nueva, instanciados):
    global sol_infactibles
    global Tij_global
    for avion_previo in instanciados:
        pista_previa = avion_previo[5] 
        tiempo_previo = avion_previo[1]

        if pista_nueva == pista_previa:
            id_nuevo = avion_nuevo['id'] - 1
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

sol_factibles = 0
sol_infactibles = 0

contador_nodos = 0
NODOS_MAXIMOS = 100000
TIEMPO_MAX = int(120)
TIEMPO_INICIAL = time.time()


#arreglos para graficos
nodos_tiempo = [] # [numero de nodos, tiempo]
costos_tiempo = [] # [menor_costo, tiempo]
factibles_infactibles = [] # [sol_factibles, sol_infactibles, tiempo]
costos_nodos = [] # [menor_costo, numero de nodos]
tiempo_usado = False
proximo_muestreo = 0.1 #segundo
nodos_entre_muestras = 5000 #cada 5000 nodos



# GRAFICOS
def graficar_nodos_tiempo(nodos_tiempo):
    global CARPETA_RESULTADOS
    if not nodos_tiempo:
        print("No hay datos para graficar Nodos vs Tiempo.")
        return
        
    nodos = [item[0] for item in nodos_tiempo]
    tiempos = [item[1] for item in nodos_tiempo]

    plt.figure(figsize=(10, 5))
    plt.plot(tiempos, nodos, color='blue', linewidth=2)
    plt.title('Nodos Explorados vs Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Cantidad de Nodos')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    ruta_guardado = os.path.join(CARPETA_RESULTADOS, '1_nodos_vs_tiempo.png')
    plt.savefig(ruta_guardado, bbox_inches='tight')
    
    # GUARDAR COMO CSV
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '1_nodos_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Nodos'])
        for t, n in zip(tiempos, nodos):
            writer.writerow([t, n])
    print("Gráfico y CSV guardados: 1_nodos_vs_tiempo")

def graficar_costos_tiempo(costos_tiempo):
    global CARPETA_RESULTADOS
    if not costos_tiempo:
        print("No hay datos para graficar Costos vs Tiempo.")
        return
    
    costos_tiempo.sort(key=lambda x: x[1])
    costos = [item[0] for item in costos_tiempo]
    tiempos = [item[1] for item in costos_tiempo]

    plt.figure(figsize=(10, 5))
    plt.step(tiempos, costos, where='post', color='green', marker='o') 
    plt.title('Evolución del Mejor Costo en el Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Mejor Costo Encontrado')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # GUARDAR COMO PNG
    ruta_guardado = os.path.join(CARPETA_RESULTADOS, '2_costos_vs_tiempo.png')
    plt.savefig(ruta_guardado, bbox_inches='tight')

    # GUARDAR COMO CSV
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '2_costos_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Mejor Costo'])
        for t, c in zip(tiempos, costos):
            writer.writerow([t, c])
    print("Gráfico y CSV guardados: 2_costos_vs_tiempo")

def graficar_factibles_infactibles(factibles_infactibles):
    global CARPETA_RESULTADOS
    if not factibles_infactibles:
        print("No hay datos para graficar Soluciones vs Tiempo.")
        return
        
    factibles = [item[0] for item in factibles_infactibles]
    infactibles = [item[1] for item in factibles_infactibles]
    tiempos = [item[2] for item in factibles_infactibles]

    plt.figure(figsize=(10, 5))
    plt.plot(tiempos, factibles, label='Factibles', color='green', linewidth=2)
    plt.plot(tiempos, infactibles, label='Infactibles (Choques)', color='red', linewidth=2)
    plt.yscale('log')
    plt.title('Soluciones Factibles e Infactibles vs Tiempo')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Cantidad de Soluciones')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # GUARDAR COMO PNG
    ruta_guardado = os.path.join(CARPETA_RESULTADOS, '3_soluciones_vs_tiempo.png')
    plt.savefig(ruta_guardado, bbox_inches='tight')
    
    # GUARDAR COMO CSV
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '3_soluciones_vs_tiempo.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tiempo (s)', 'Factibles', 'Infactibles (Choques)'])
        for t, f, inf in zip(tiempos, factibles, infactibles):
            writer.writerow([t, f, inf])
            
    print("Gráfico y CSV guardados: 3_soluciones_vs_tiempo")

def graficar_costos_nodos(costos_nodos):
    global CARPETA_RESULTADOS
    if not costos_nodos:
        print("No hay datos para graficar Costos vs Nodos.")
        return
        
    costos = [item[0] for item in costos_nodos]
    nodos = [item[1] for item in costos_nodos]

    plt.figure(figsize=(10, 5))
    plt.step(nodos, costos, where='post', color='purple', marker='o')
    plt.title('Evolución del Mejor Costo vs Nodos Explorados')
    plt.xlabel('Nodos Explorados')
    plt.ylabel('Mejor Costo Encontrado')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # GUARDAR COMO PNG
    ruta_guardado = os.path.join(CARPETA_RESULTADOS, '4_costos_vs_nodos.png')
    plt.savefig(ruta_guardado, bbox_inches='tight')
    
    # GUARDAR COMO CSV
    ruta_csv = os.path.join(CARPETA_RESULTADOS, '4_costos_vs_nodos.csv')
    with open(ruta_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Nodos Explorados', 'Mejor Costo'])
        for n, c in zip(nodos, costos):
            writer.writerow([n, c])
            
    print("Gráfico y CSV guardados: 4_costos_vs_nodos")



# Backtracking (aca se recorre el espacio de busqueda y se realizan todas las validaciones, actualizaciones, etc.)
def funcion_recursiva(nivel, aviones_instanciados):
    global cantidad_pistas
    global aviones
    global mejor_costo
    global mejor_secuencia
    global sol_factibles
    global contador_nodos
    
    #graficos
    global NODOS_MAXIMOS
    global TIEMPO_MAX
    global TIEMPO_INICIAL
    global nodos_tiempo
    global costos_tiempo
    global factibles_infactibles
    global costos_nodos
    global tiempo_usado #para que se grafique solo una vez
    global proximo_muestreo
    global nodos_entre_muestras

    contador_nodos += 1
    tiempo_actual = int(time.time() - TIEMPO_INICIAL) 

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
    #Caso base
    if nivel == len(aviones):
        sol_factibles += 1
        #print("se llego al nivel ", len(aviones))
        costo_secuencia = calcular_costo_arr(aviones_instanciados)
        #print(f'costo acumulado de la secuencia: {costo_secuencia}')
        if es_menor_costo(costo_secuencia, aviones_instanciados): 
            costos_tiempo.append((costo_secuencia, tiempo_actual))
            print(f'[!!!!!!] nueva mejor secuencia encontrada: {mejor_costo} ')
            print('Secuencia (id, tiempo, pista): ')
            print([[avion[0], avion[1], avion[5]] for avion in mejor_secuencia])
            print('')
        #else: print(f'sigue  {mejor_costo}, conseguido con {mejor_secuencia}')
        #else: print(f'{sol_factibles}: costo {costo_secuencia} es mayor que {mejor_costo}')
        #print(mejoramiento)
        return 
    
    avion_actual = aviones[nivel]

    #print("avion ", avion_actual['id'], ", tiene desde ", avion_actual['primer_tiempo'], " hasta ",  avion_actual['ultimo_tiempo'] )
    for pista in range(1, cantidad_pistas + 1):
        for tiempo in range(avion_actual['primer_tiempo'],  avion_actual['ultimo_tiempo'] + 1):
            if es_valido(avion_actual, tiempo, pista, aviones_instanciados):
                #print("Avion ", avion_actual['id'], " probando el tiempo ", tiempo, " en la pista ", pista )
                #arreglo: 
                aviones_instanciados.append([
                                            avion_actual['id'], # 0
                                            tiempo, # 1
                                            avion_actual['tiempo_esperado'], # 2
                                            avion_actual['costo_tarde'], # 3
                                            avion_actual['costo_temprano'], #4
                                            pista # 5
                                            ])
                #dict:
                #aviones_instanciados[avion_actual['id']] = i
                #print(aviones_instanciados)
                funcion_recursiva(nivel+1, aviones_instanciados) #DESDE AQUI EL CODIGO SE EJECUTA EN ORDEN INVERSO 15 -> 14 -> 13 -> 12 -> 11 -> 10


                #arreglo: 
                aviones_instanciados.pop() #para que cuando un avion termine con un valor se pueda instanciar con otro valor
                #dict
                #aviones_instanciados.popitem()
    return 

    """ 
    el return esta implicito cuando no está, 
    es para que despues de que el penultimo pruebe todos los valores del ultimo, 
    el antepenultimo pruebe todos los valores del penultimo
    """

#ordenar los aviones segun el tiempo esperado, menor a mayor -> Heuristica de selección de variable
aviones.sort(key=lambda avion: avion['tiempo_esperado'])

#ordenar los aviones segun el dominio, menor a mayor -> Heuristica 2 pero no se usó
#aviones.sort(key=lambda avion: avion['dominio'])

#Iniciar la busqueda
funcion_recursiva(0, [])