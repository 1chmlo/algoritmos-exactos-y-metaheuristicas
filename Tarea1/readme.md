# Tarea 1

## Dependencias

Para poder ejecutar los scripts correctamente es necesario tener instalado **Python 3.x** y la librería **matplotlib**.

Puedes instalarla ejecutando:

```bash
pip install matplotlib
```

## Estructura de Scripts

1. **`1_Backtracking.py`**:
   - Se utilizan como parámetros:
     - Para ejecutar: la cantidad de pistas y el caso a utilizar (quedó por defecto con el case1.txt y 3 pistas y son los únicos relevantes para la revisión del funcionamiento de los algoritmos).

     - Para graficar: el numero de nodos, el tiempo, el numero de muestras por nodo (cada cuantos nodos se va a tomar la muestra del costo en el gráfico de nodos costo). Estos parámetros no afectan el funcionamiento ni la condicion de término del algoritmo.

   - Genera gráficos y archivos `.csv` y `.png` con estadísticas de la ejecución, guardándolos en la carpeta `resultados_BT/`.

2. **`2_Forward_Checking.py`**:
   - Mantiene los parámetros y, al igual que BT, tras su ejecución guarda los gráficos y `.csv` y `.png` de métricas dentro de `resultados_FC/`.

3. **`3_Comparar_graficos.py`**:
   - Se utiliza como parámetro el caso a comparar (ej: case1)
   - Lee las ejecuciones más recientes de los métodos BT y FC guardadas en los directorios de resultados.
   - Genera gráficos comparativos solapados (Nodos vs Tiempo, Evolución del costo mínimo, Soluciones encontradas, etc.).
   - Guarda los resultados gráficos de la comparativa agrupados por timestamp en la carpeta `Comparaciones/`.

## Cómo Ejecutar

1. Abre cualquiera de los scripts y ubícate en la sección de Configuración para elegir con cuantas pistas realizar la ejecucion (parametro: "cantidad_pistas"), además de elegir el caso a ejecutar (por ejemplo, ajusta `NOMBRE_ARCHIVO = 'case4.txt'` y `cantidad_pistas = 3` en los algoritmos, o `CASO = "case4"` en el comparador).
2. Ejecuta Backtracking:
   ```bash
   python 1_Backtracking.py
   ```
3. Ejecuta Forward Checking:
   ```bash
   python 2_Forward_Checking.py
   ```
4. Finalmente, si quieres comparar la ejecucion de los algoritmos:
   ```bash
   python 3_Comparar_graficos.py
   ```
