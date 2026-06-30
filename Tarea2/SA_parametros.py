import random
import math
import time
import os
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
#  Funciones base (idénticas al original)
# ─────────────────────────────────────────────

def leer_instancia(ruta_archivo):
    with open(ruta_archivo, 'r') as file:
        datos = file.read().split()
    datos = [int(x) for x in datos]
    m  = datos[0]; n  = datos[1]; ne = datos[2]; B  = datos[3]
    idx = 4
    beneficios = datos[idx : idx + m];  idx += m
    costos     = datos[idx : idx + n];  idx += n
    recursos_requeridos = [set() for _ in range(m)]
    for _ in range(ne):
        id_alt = datos[idx]; id_rec = datos[idx + 1]
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

def generar_vecino(solucion, m):
    solucion = set(solucion)
    todas = set(range(m))
    no_sel = list(todas - solucion); sel = list(solucion)
    r = random.random()
    if r < 0.333:
        if no_sel: solucion.add(random.choice(no_sel))
    elif r < 0.666:
        if sel: solucion.remove(random.choice(sel))
    else:
        if sel and no_sel:
            solucion.remove(random.choice(sel))
            solucion.add(random.choice(no_sel))
    return solucion

def greedy_determinista(m, B, beneficios, costos, recursos_requeridos):
    evaluaciones = []
    for i in range(m):
        c = sum(costos[r] for r in recursos_requeridos[i])
        rent = beneficios[i] / c if c > 0 else float('inf')
        evaluaciones.append((rent, i))
    evaluaciones.sort(reverse=True)
    solucion = set()
    for _, i in evaluaciones:
        if calcular_costo(solucion | {i}, recursos_requeridos, costos) <= B:
            solucion.add(i)
    return solucion

def greedy_estocastico(m, B, beneficios, costos, recursos_requeridos, semilla, k=3):
    random.seed(semilla)
    evaluaciones = []
    for i in range(m):
        c = sum(costos[r] for r in recursos_requeridos[i])
        rent = beneficios[i] / c if c > 0 else float('inf')
        evaluaciones.append((rent, i))
    evaluaciones.sort(reverse=True)
    candidatos = [i for _, i in evaluaciones]
    solucion = set()
    while candidatos:
        top_k = candidatos[:k]
        elegido = random.choice(top_k)
        if calcular_costo(solucion | {elegido}, recursos_requeridos, costos) <= B:
            solucion.add(elegido)
        candidatos.remove(elegido)
    return solucion

def simulated_annealing(m, B, beneficios, costos, recursos_requeridos,
                         sol_inicial, T_inicial, alpha, T_min, L):
    solucion_actual  = set(sol_inicial)
    mejor_solucion   = set(solucion_actual)
    mejor_beneficio  = calcular_beneficio(mejor_solucion, beneficios)
    beneficio_actual = mejor_beneficio
    T = T_inicial
    historial_mejor = []

    while T > T_min:
        for _ in range(L):
            vecino = generar_vecino(solucion_actual, m)
            if not es_factible(vecino, recursos_requeridos, costos, B):
                historial_mejor.append(mejor_beneficio)
                continue
            beneficio_vecino = calcular_beneficio(vecino, beneficios)
            delta = beneficio_vecino - beneficio_actual
            if delta > 0:
                solucion_actual  = vecino
                beneficio_actual = beneficio_vecino
                if beneficio_actual > mejor_beneficio:
                    mejor_solucion  = set(solucion_actual)
                    mejor_beneficio = beneficio_actual
            else:
                if random.random() < math.exp(delta / T):
                    solucion_actual  = vecino
                    beneficio_actual = beneficio_vecino
            historial_mejor.append(mejor_beneficio)
        T *= alpha

    return mejor_solucion, mejor_beneficio, historial_mejor

# ─────────────────────────────────────────────
#  Configuración del experimento
# ─────────────────────────────────────────────

# 5 configuraciones a comparar: varían T_inicial, alpha y L de forma razonada
#   C1: enfriamiento lento, mucha exploración (referencia)
#   C2: enfriamiento muy lento, L más grande
#   C3: enfriamiento rápido, L pequeño
#   C4: temperatura inicial baja (poca exploración inicial)
#   C5: temperatura inicial alta, enfriamiento moderado

CONFIGS = {
    "C1":          dict(T_inicial=1000, alpha=0.995, T_min=0.1, L=200),
    "C2":    dict(T_inicial=1000, alpha=0.999, T_min=0.1, L=200),
    #"C3":  dict(T_inicial=1000, alpha=0.90,  T_min=0.1, L=100),
    "C4":    dict(T_inicial=100,  alpha=0.995, T_min=0.1, L=100),
    "C5":    dict(T_inicial=5000, alpha=0.995, T_min=0.1, L=150),
}

N_SEMILLAS_ESTO = 5   # semillas del greedy estocástico por config/instancia

ARCHIVOS = {
    "easy":    "instancias/easy.txt",
    "medium1": "instancias/medium1.txt",
    "medium2": "instancias/medium2.txt",
    "hard":    "instancias/hard.txt",
}

OUTDIR = "resultados_experimentos"
os.makedirs(OUTDIR, exist_ok=True)

# ─────────────────────────────────────────────
#  Cargar instancias
# ─────────────────────────────────────────────

instancias = {}
for nombre, ruta in ARCHIVOS.items():
    if os.path.exists(ruta):
        instancias[nombre] = leer_instancia(ruta)
        m, n, B, *_ = instancias[nombre]
        print(f"Cargada: {nombre} — m={m}, n={n}, B={B}")
    else:
        print(f"AVISO: no se encontró {ruta}, se omite.")

# ─────────────────────────────────────────────
#  Experimento principal
# ─────────────────────────────────────────────
# resultados[instancia][config] = {
#     "det":  beneficio SA con greedy determinista,
#     "esto": [beneficios SA con cada semilla estocástica],
#     "hist_det":  historial de convergencia (det),
#     "hist_esto": historial de convergencia (mejor semilla estocástica),
# }

resultados = {inst: {} for inst in instancias}

for inst_nombre, datos in instancias.items():
    m, n, B, beneficios, costos, recursos_requeridos = datos
    print(f"\n── Instancia: {inst_nombre} ──")

    for cfg_nombre, params in CONFIGS.items():
        # --- Greedy determinista como solución inicial ---
        random.seed(42)
        sol_det = greedy_determinista(m, B, beneficios, costos, recursos_requeridos)
        _, ben_det, hist_det = simulated_annealing(
            m, B, beneficios, costos, recursos_requeridos,
            sol_inicial=sol_det, **params)

        # --- Greedy estocástico como solución inicial (varias semillas) ---
        bens_esto  = []
        hists_esto = []
        for seed in range(N_SEMILLAS_ESTO):
            random.seed(seed)
            sol_esto = greedy_estocastico(m, B, beneficios, costos,
                                          recursos_requeridos, semilla=seed)
            random.seed(42)
            _, ben_esto, hist_esto = simulated_annealing(
                m, B, beneficios, costos, recursos_requeridos,
                sol_inicial=sol_esto, **params)
            bens_esto.append(ben_esto)
            hists_esto.append(hist_esto)

        # Tomar la corrida estocástica con mejor resultado para la curva
        idx_mejor = bens_esto.index(max(bens_esto))

        resultados[inst_nombre][cfg_nombre] = {
            "det":       ben_det,
            "esto_mean": sum(bens_esto) / len(bens_esto),
            "esto_max":  max(bens_esto),
            "esto_min":  min(bens_esto),
            "hist_det":  hist_det,
            "hist_esto": hists_esto[idx_mejor],
        }
        print(f"  {cfg_nombre}: det={ben_det}  "
              f"esto_mean={sum(bens_esto)/len(bens_esto):.1f}  "
              f"esto_max={max(bens_esto)}")

# ─────────────────────────────────────────────
#  Tabla resumen en consola
# ─────────────────────────────────────────────

print("\n" + "=" * 90)
print(f"  {'Config':<22} {'Instancia':<10} "
      f"{'SA+Det':>8} {'SA+Esto(mean)':>14} {'SA+Esto(max)':>13} {'SA+Esto(min)':>13}")
print("=" * 90)
for inst in instancias:
    for cfg in CONFIGS:
        r = resultados[inst][cfg]
        print(f"  {cfg:<22} {inst:<10} "
              f"{r['det']:>8} {r['esto_mean']:>14.1f} "
              f"{r['esto_max']:>13} {r['esto_min']:>13}")
    print("-" * 90)

# ─────────────────────────────────────────────
#  Gráfica 1: Barras — beneficio por config e instancia
# ─────────────────────────────────────────────

cfg_nombres = list(CONFIGS.keys())
inst_nombres = list(instancias.keys())
n_cfg  = len(cfg_nombres)
n_inst = len(inst_nombres)

fig, axes = plt.subplots(1, n_inst, figsize=(5 * n_inst, 5), sharey=False)
if n_inst == 1:
    axes = [axes]

x = range(n_cfg)
ancho = 0.35

for ax, inst in zip(axes, inst_nombres):
    bens_det  = [resultados[inst][c]["det"]       for c in cfg_nombres]
    bens_esto = [resultados[inst][c]["esto_mean"] for c in cfg_nombres]

    bars1 = ax.bar([i - ancho/2 for i in x], bens_det,  width=ancho,
                   label='SA + Greedy det.',  color='#4C72B0', alpha=0.85)
    bars2 = ax.bar([i + ancho/2 for i in x], bens_esto, width=ancho,
                   label='SA + Greedy estoc. (mean)', color='#DD8452', alpha=0.85)

    ax.set_xticks(list(x))
    ax.set_xticklabels([c.split(" ")[0] for c in cfg_nombres], fontsize=9)
    ax.set_title(inst)
    ax.set_ylabel('Beneficio SA')
    ax.legend(fontsize=8)

    # Anotar valores encima de cada barra
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=7)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=7)

fig.suptitle('Beneficio SA según configuración y solución inicial', fontsize=12)
plt.tight_layout()
path1 = os.path.join(OUTDIR, 'comparacion_configs.png')
plt.savefig(path1, dpi=150); plt.close()
print(f"\nGuardado: {path1}")

# ─────────────────────────────────────────────
#  Gráfica 2: Curvas de convergencia por instancia
#  (det vs esto, para cada config — subplots)
# ─────────────────────────────────────────────

COLORES = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']

for inst in inst_nombres:
    fig, axes = plt.subplots(1, n_cfg, figsize=(4 * n_cfg, 4), sharey=True)
    if n_cfg == 1:
        axes = [axes]

    for ax, (cfg, color) in zip(axes, zip(cfg_nombres, COLORES)):
        r = resultados[inst][cfg]
        ax.plot(r["hist_det"],  color=color, linewidth=1.5, label='Det.')
        ax.plot(r["hist_esto"], color=color, linewidth=1.5, linestyle='--',
                alpha=0.7, label='Estoc.')
        ax.set_title(cfg.split(" ")[0], fontsize=9)
        ax.set_xlabel('Iteraciones', fontsize=8)
        if ax == axes[0]:
            ax.set_ylabel('Mejor beneficio', fontsize=8)
        ax.legend(fontsize=7)
        ax.tick_params(labelsize=7)

    fig.suptitle(f'Convergencia SA — {inst}', fontsize=11)
    plt.tight_layout()
    path2 = os.path.join(OUTDIR, f'convergencia_{inst}.png')
    plt.savefig(path2, dpi=150); plt.close()
    print(f"Guardado: {path2}")

print("\nExperimento completo. Archivos en:", OUTDIR)