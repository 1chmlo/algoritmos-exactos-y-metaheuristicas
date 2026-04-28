import os
import csv
import matplotlib.pyplot as plt
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
# Caso a comparar (ejemplo: 'case1', 'case2', 'case3', 'case4', 'wnspesados')
CASO = "case4"

# Directorios base de los algoritmos
DIRECTORIO_BT = os.path.join(os.path.dirname(__file__), 'resultados_BT')
DIRECTORIO_FC = os.path.join(os.path.dirname(__file__), 'resultados_FC')

# =============================================================================

def obtener_ultima_carpeta_caso(ruta_base, nombre_caso):
    try:
        # Filtrar carpetas que empiezan con el nombre del caso ("case1_...")
        carpetas = [
            os.path.join(ruta_base, d) 
            for d in os.listdir(ruta_base) 
            if os.path.isdir(os.path.join(ruta_base, d)) and d.startswith(nombre_caso + "_")
        ]
        
        if not carpetas:
            return None
            
        # Ordenar por fecha de modificación (la más reciente primero)
        carpetas.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return carpetas[0]
    except FileNotFoundError:
        print(f"No se encontró el directorio: {ruta_base}")
        return None

def leer_csv(ruta_csv):
    x, y, z = [], [], []
    if not os.path.exists(ruta_csv):
        print(f"Advertencia: No se encontró {ruta_csv}")
        return x, y, z

    with open(ruta_csv, mode='r') as file:
        reader = csv.reader(file)
        next(reader) # Saltar encabezados
        for row in reader:
            if not row: continue
            x.append(float(row[0]))
            y.append(float(row[1]))
            if len(row) > 2:
                z.append(float(row[2]))
    return x, y, z

def graficar_comparacion(ruta1, ruta2):
    nombre1 = os.path.basename(ruta1)
    nombre2 = os.path.basename(ruta2)
    
    print(f"Comparando:\n1: {nombre1}\n2: {nombre2}\n")

    # Crear carpeta para guardar comparaciones
    fecha_ejecucion = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta_salida = os.path.join(os.path.dirname(__file__), 'Comparaciones', f"Comparacion_{CASO}_{fecha_ejecucion}")
    os.makedirs(carpeta_salida, exist_ok=True)

    # 1. Nodos vs Tiempo
    t1_1, n1_1, _ = leer_csv(os.path.join(ruta1, '1_nodos_vs_tiempo.csv'))
    t2_1, n2_1, _ = leer_csv(os.path.join(ruta2, '1_nodos_vs_tiempo.csv'))

    if t1_1 and t2_1:
        plt.figure(figsize=(10, 5))
        plt.plot(t1_1, n1_1, label=f'Backtracking ({nombre1})', color='blue', linewidth=2)
        plt.plot(t2_1, n2_1, label=f'Forward Checking ({nombre2})', color='orange', linewidth=2, linestyle='--')
        plt.title(f'Comparación ({CASO}): Nodos Explorados vs Tiempo')
        plt.xlabel('Tiempo (segundos)')
        plt.ylabel('Cantidad de Nodos')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(os.path.join(carpeta_salida, 'comparativa_1_nodos_vs_tiempo.png'), bbox_inches='tight')
        plt.close()

    # 2. Costos vs Tiempo
    t1_2, c1_2, _ = leer_csv(os.path.join(ruta1, '2_costos_vs_tiempo.csv'))
    t2_2, c2_2, _ = leer_csv(os.path.join(ruta2, '2_costos_vs_tiempo.csv'))

    if t1_2 and t2_2:
        plt.figure(figsize=(10, 5))
        plt.step(t1_2, c1_2, where='post', label=f'Backtracking ({nombre1})', color='green', marker='o')
        plt.step(t2_2, c2_2, where='post', label=f'Forward Checking ({nombre2})', color='limegreen', marker='x', linestyle='--')
        plt.title(f'Comparación ({CASO}): Evolución del Mejor Costo en el Tiempo')
        plt.xlabel('Tiempo (segundos)')
        plt.ylabel('Mejor Costo Encontrado')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(os.path.join(carpeta_salida, 'comparativa_2_costos_vs_tiempo.png'), bbox_inches='tight')
        plt.close()

    # 3. Soluciones vs Tiempo
    t1_3, f1_3, inf1_3 = leer_csv(os.path.join(ruta1, '3_soluciones_vs_tiempo.csv'))
    t2_3, f2_3, inf2_3 = leer_csv(os.path.join(ruta2, '3_soluciones_vs_tiempo.csv'))

    if t1_3 and t2_3:
        plt.figure(figsize=(10, 5))
        plt.plot(t1_3, f1_3, label=f'Factibles BT ({nombre1})', color='green', linewidth=2)
        plt.plot(t2_3, f2_3, label=f'Factibles FC ({nombre2})', color='limegreen', linewidth=2, linestyle='--')
        
        plt.plot(t1_3, inf1_3, label=f'Infactibles BT ({nombre1})', color='red', linewidth=2)
        plt.plot(t2_3, inf2_3, label=f'Infactibles FC ({nombre2})', color='salmon', linewidth=2, linestyle='--')

        plt.yscale('log')
        plt.title(f'Comparación ({CASO}): Soluciones Factibles e Infactibles vs Tiempo')
        plt.xlabel('Tiempo (segundos)')
        plt.ylabel('Cantidad de Soluciones (Log)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(os.path.join(carpeta_salida, 'comparativa_3_soluciones_vs_tiempo.png'), bbox_inches='tight')
        plt.close()

    # 4. Costos vs Nodos
    n1_4, c1_4, _ = leer_csv(os.path.join(ruta1, '4_costos_vs_nodos.csv'))
    n2_4, c2_4, _ = leer_csv(os.path.join(ruta2, '4_costos_vs_nodos.csv'))

    if n1_4 and n2_4:
        plt.figure(figsize=(10, 5))
        plt.step(n1_4, c1_4, where='post', label=f'Backtracking ({nombre1})', color='purple', marker='o')
        plt.step(n2_4, c2_4, where='post', label=f'Forward Checking ({nombre2})', color='violet', marker='x', linestyle='--')
        plt.title(f'Comparación ({CASO}): Mejor Costo vs Nodos Explorados')
        plt.xlabel('Nodos Explorados')
        plt.ylabel('Mejor Costo Encontrado')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(os.path.join(carpeta_salida, 'comparativa_4_costos_vs_nodos.png'), bbox_inches='tight')
        plt.close()

    print(f"Comparaciones generadas con éxito en: {carpeta_salida}")

if __name__ == "__main__":
    ruta_al_1 = obtener_ultima_carpeta_caso(DIRECTORIO_BT, CASO)
    ruta_al_2 = obtener_ultima_carpeta_caso(DIRECTORIO_FC, CASO)

    if ruta_al_1 and ruta_al_2:
        graficar_comparacion(ruta_al_1, ruta_al_2)
    else:
        if not ruta_al_1:
            print(f"No se encontraron resultados para el caso '{CASO}' en {DIRECTORIO_BT}")
        if not ruta_al_2:
            print(f"No se encontraron resultados para el caso '{CASO}' en {DIRECTORIO_FC}")