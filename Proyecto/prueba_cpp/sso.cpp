#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <random>
#include <chrono>
#include <numeric>
#include <algorithm>
#include <iomanip>
#include <filesystem>

// Espacio de nombres para simplificar
using namespace std;
namespace fs = std::filesystem;

// ==========================================
// Estructuras de Datos
// ==========================================
struct Item {
    double beneficio;
    vector<double> pesos;
};

struct Particula {
    vector<int> solucion;
    vector<int> pbest_solucion;
    double pbest_fitness;
    double fitness;
    bool es_factible;
};

struct ResultadoSSO {
    vector<int> mejor_solucion;
    double mejor_beneficio;
    bool es_factible;
    vector<double> historial_convergencia;
};

// Contadores Globales
long long contador_infactibles = 0;
long long contador_factibles = 0;
long long contador_soluciones = 0;

void reset_contadores() {
    contador_infactibles = 0;
    contador_factibles = 0;
    contador_soluciones = 0;
}

// Configuraci�n del generador de n�meros aleatorios
mt19937 rng(random_device{}());

// ==========================================
// 1. Leer instancias
// ==========================================
void leer_instancia_hao(const string& filepath, int& n, int& l, int& m, 
                        vector<double>& capacidades, vector<vector<Item>>& grupos) {
    ifstream file(filepath);
    if (!file.is_open()) {
        cerr << "Error al abrir el archivo: " << filepath << endl;
        exit(1);
    }

    file >> n >> l >> m;
    capacidades.resize(m);
    for (int i = 0; i < m; ++i) {
        file >> capacidades[i];
    }

    grupos.resize(n, vector<Item>(l));
    string id_grupo;
    for (int i = 0; i < n; ++i) {
        file >> id_grupo;
        for (int j = 0; j < l; ++j) {
            file >> grupos[i][j].beneficio;
            grupos[i][j].pesos.resize(m);
            for (int k = 0; k < m; ++k) {
                file >> grupos[i][j].pesos[k];
            }
        }
    }
}

// ==========================================
// 2. Greedy para generar una soluci�n inicial
// ==========================================
vector<int> generar_solucion_greedy(const vector<vector<Item>>& grupos, int n, int l) {
    vector<int> solucion_greedy(n);
    for (int i = 0; i < n; ++i) {
        int mejor_item = 0;
        double mejor_ratio = -numeric_limits<double>::infinity();

        for (int j = 0; j < l; ++j) {
            double beneficio = grupos[i][j].beneficio;
            double suma_pesos = 0.0;
            for (double p : grupos[i][j].pesos) suma_pesos += p;

            double ratio = (suma_pesos > 0) ? (beneficio / suma_pesos) : beneficio;

            if (ratio > mejor_ratio) {
                mejor_ratio = ratio;
                mejor_item = j;
            }
        }
        solucion_greedy[i] = mejor_item;
    }
    return solucion_greedy;
}

// ==========================================
// 3. Intentar reparar soluciones infactibles
// ==========================================
pair<vector<int>, bool> reparar_solucion(const vector<int>& solucion, const vector<vector<Item>>& grupos, 
                                         const vector<double>& capacidades, int n, int l, int m, int max_intentos = 5) {
    vector<int> solucion_reparada = solucion;
    int intentos = 0;

    while (intentos < max_intentos) {
        vector<double> pesos_totales(m, 0.0);
        
        for (int i = 0; i < n; ++i) {
            const auto& pesos_item = grupos[i][solucion_reparada[i]].pesos;
            for (int r = 0; r < m; ++r) {
                pesos_totales[r] += pesos_item[r];
            }
        }

        double violacion_total = 0.0;
        for (int r = 0; r < m; ++r) {
            double diff = pesos_totales[r] - capacidades[r];
            if (diff > 0) violacion_total += diff;
        }

        if (violacion_total == 0.0) {
            return {solucion_reparada, true};
        }

        bool hubo_intercambio = false;
        pair<int, int> mejor_intercambio = {-1, -1};
        double mejor_reduccion_violacion = 0.0;

        for (int i = 0; i < n; ++i) {
            int item_actual = solucion_reparada[i];
            const auto& pesos_actuales = grupos[i][item_actual].pesos;

            for (int j = 0; j < l; ++j) {
                if (j == item_actual) continue;

                const auto& pesos_candidatos = grupos[i][j].pesos;
                double nueva_violacion_total = 0.0;
                bool abortar = false;

                for (int r = 0; r < m; ++r) {
                    double nuevo_peso_r = pesos_totales[r] - pesos_actuales[r] + pesos_candidatos[r];
                    double diff = nuevo_peso_r - capacidades[r];
                    if (diff > 0) nueva_violacion_total += diff;

                    // PODA (Early Stopping)
                    if (nueva_violacion_total >= (violacion_total - mejor_reduccion_violacion)) {
                        abortar = true;
                        break;
                    }
                }

                if (!abortar) {
                    double reduccion = violacion_total - nueva_violacion_total;
                    if (reduccion > mejor_reduccion_violacion) {
                        mejor_reduccion_violacion = reduccion;
                        mejor_intercambio = {i, j};
                        hubo_intercambio = true;
                    }
                }
            }
        }

        if (hubo_intercambio) {
            solucion_reparada[mejor_intercambio.first] = mejor_intercambio.second;
            intentos++;
        } else {
            return {solucion_reparada, false};
        }
    }
    return {solucion_reparada, false};
}

// ==========================================
// 4. Evaluar fitness de una soluci�n
// ==========================================
pair<double, double> calcular_fitness(const vector<int>& solucion, const vector<vector<Item>>& grupos, bool factible) {
    contador_soluciones++;
    if (factible) {
        contador_factibles++;
        double beneficio_total = 0.0;
        for (size_t i = 0; i < solucion.size(); ++i) {
            beneficio_total += grupos[i][solucion[i]].beneficio;
        }
        return {beneficio_total, beneficio_total};
    } else {
        contador_infactibles++;
        return {-numeric_limits<double>::infinity(), 0.0};
    }
}

// ==========================================
// 5. Simplified Swarm Optimization
// ==========================================
ResultadoSSO sso_mmkp(int n, int l, int m, const vector<double>& capacidades, const vector<vector<Item>>& grupos, 
                      int num_particulas = 50, int max_generaciones = 1000, 
                      double p_mantener = 0.01, double p_pbest = 0.48, double p_gbest = 0.48) {
    
    vector<int> semilla_greedy = generar_solucion_greedy(grupos, n, l);
    vector<Particula> enjambre(num_particulas);
    
    uniform_int_distribution<int> dist_int(0, l - 1);
    uniform_real_distribution<double> dist_real(0.0, 1.0);

    for (int i = 0; i < num_particulas; ++i) {
        enjambre[i].es_factible = false;
        enjambre[i].pbest_fitness = -numeric_limits<double>::infinity();
        enjambre[i].fitness = -numeric_limits<double>::infinity();
        
        if (i == 0) {
            enjambre[i].solucion = semilla_greedy;
        } else {
            enjambre[i].solucion.resize(n);
            for (int d = 0; d < n; ++d) enjambre[i].solucion[d] = dist_int(rng);
        }
        enjambre[i].pbest_solucion = enjambre[i].solucion;
    }

    vector<int> gbest_solucion;
    double gbest_fitness = -numeric_limits<double>::infinity();
    double gbest_beneficio = 0.0;
    bool gbest_factible = false;
    vector<double> historial_convergencia;
    historial_convergencia.reserve(max_generaciones);

    double umbral_1 = p_mantener;
    double umbral_2 = p_mantener + p_pbest;
    double umbral_3 = p_mantener + p_pbest + p_gbest;

    for (int gen = 0; gen < max_generaciones; ++gen) {
        for (auto& particula : enjambre) {
            auto [sol_reparada, es_factible] = reparar_solucion(particula.solucion, grupos, capacidades, n, l, m);
            particula.solucion = sol_reparada;
            particula.es_factible = es_factible;

            auto [fitness, beneficio] = calcular_fitness(particula.solucion, grupos, particula.es_factible);
            particula.fitness = fitness;

            if (fitness > particula.pbest_fitness && particula.es_factible) {
                particula.pbest_fitness = fitness;
                particula.pbest_solucion = particula.solucion;
            }

            if (fitness > gbest_fitness && particula.es_factible) {
                gbest_fitness = fitness;
                gbest_solucion = particula.solucion;
                gbest_beneficio = beneficio;
                gbest_factible = true;
            }
        }

        if (!gbest_factible) {
            historial_convergencia.push_back(0.0);
            continue;
        }

        historial_convergencia.push_back(gbest_beneficio);

        for (auto& particula : enjambre) {
            vector<int> nueva_solucion(n);
            const auto& sol_actual = particula.solucion;
            const auto& pbest_actual = particula.pbest_solucion;

            for (int d = 0; d < n; ++d) {
                double r = dist_real(rng);
                if (r < umbral_1) nueva_solucion[d] = sol_actual[d];
                else if (r < umbral_2) nueva_solucion[d] = pbest_actual[d];
                else if (r < umbral_3) nueva_solucion[d] = gbest_solucion[d];
                else nueva_solucion[d] = dist_int(rng);
            }
            particula.solucion = nueva_solucion;
        }

        if ((gen + 1) % 100 == 0) {
            string estado = gbest_factible ? "Factible" : "Ninguna Factible";
            cout << "Generacion " << setw(4) << (gen + 1) 
                 << " | Mejor Beneficio: " << fixed << setprecision(2) << gbest_beneficio 
                 << " | Estado: " << estado << "\n";
        }
    }

    return {gbest_solucion, gbest_beneficio, gbest_factible, historial_convergencia};
}

// ==========================================
// 6. Ejecuci�n y prints
// ==========================================
int main() {
    string carpeta_instancias = "INSTANCIAS_CPP";
    if (!fs::exists(carpeta_instancias)) {
        cerr << "La carpeta '" << carpeta_instancias << "' no existe.\n";
        return 1;
    }

    vector<string> archivos_instancias;
    for (const auto& entry : fs::directory_iterator(carpeta_instancias)) {
        if (entry.path().extension() == ".txt") {
            archivos_instancias.push_back(entry.path().string());
        }
    }

    if (archivos_instancias.empty()) {
        cerr << "No se encontraron instancias .txt\n";
        return 1;
    }

    int n_ejecuciones = 5;
    fs::create_directories("Resultados");
    string carpeta_salida = "Resultados/Experimento_Cpp";
    fs::create_directories(carpeta_salida);

    int particulas = 25;
    int generaciones = 2000;
    double p_mantener = 0.10, p_pbest = 0.40, p_gbest = 0.40;

    ofstream csv_file(carpeta_salida + "/resumen_global.csv");
    csv_file << "Instancia;N_Ejecuciones;Mejor_Beneficio_Global;Media_Beneficio;Min_Beneficio;Media_Tiempo(s);Media_Factibles;Media_Infactibles\n";

    for (const auto& archivo : archivos_instancias) {
        fs::path p(archivo);
        string instancia_nombre = p.stem().string();

        cout << "\n==========================================\n";
        cout << "Procesando: " << instancia_nombre << " (" << n_ejecuciones << " ejecuciones)\n";
        cout << "==========================================\n";

        int n, l, m;
        vector<double> capacidades;
        vector<vector<Item>> grupos;
        leer_instancia_hao(archivo, n, l, m, capacidades, grupos);

        vector<double> beneficios_ejecuciones;
        vector<double> tiempos_ejecuciones;
        vector<long long> factibles_ejecuciones;
        vector<long long> infactibles_ejecuciones;

        double mejor_beneficio_global = -numeric_limits<double>::infinity();

        for (int ejecucion = 0; ejecucion < n_ejecuciones; ++ejecucion) {
            reset_contadores();
            auto tiempo_inicio = chrono::high_resolution_clock::now();

            ResultadoSSO res = sso_mmkp(n, l, m, capacidades, grupos, particulas, generaciones, p_mantener, p_pbest, p_gbest);

            auto tiempo_fin = chrono::high_resolution_clock::now();
            double tiempo_total = chrono::duration<double>(tiempo_fin - tiempo_inicio).count();

            if (res.mejor_beneficio > mejor_beneficio_global && res.es_factible) {
                mejor_beneficio_global = res.mejor_beneficio;
            }

            beneficios_ejecuciones.push_back(res.es_factible ? res.mejor_beneficio : 0.0);
            tiempos_ejecuciones.push_back(tiempo_total);
            factibles_ejecuciones.push_back(contador_factibles);
            infactibles_ejecuciones.push_back(contador_infactibles);

            cout << "  Ejec. " << (ejecucion + 1) << "/" << n_ejecuciones 
                 << " | Beneficio: " << (res.es_factible ? res.mejor_beneficio : 0.0) 
                 << " | Tiempo: " << fixed << setprecision(2) << tiempo_total << "s\n";
        }

        double sum_beneficios = accumulate(beneficios_ejecuciones.begin(), beneficios_ejecuciones.end(), 0.0);
        double media_beneficios = sum_beneficios / n_ejecuciones;
        double min_beneficio = *min_element(beneficios_ejecuciones.begin(), beneficios_ejecuciones.end());
        double max_beneficio = *max_element(beneficios_ejecuciones.begin(), beneficios_ejecuciones.end());
        
        double sum_tiempos = accumulate(tiempos_ejecuciones.begin(), tiempos_ejecuciones.end(), 0.0);
        double media_tiempos = sum_tiempos / n_ejecuciones;

        double sum_factibles = accumulate(factibles_ejecuciones.begin(), factibles_ejecuciones.end(), 0.0);
        double media_factibles = sum_factibles / n_ejecuciones;

        double sum_infactibles = accumulate(infactibles_ejecuciones.begin(), infactibles_ejecuciones.end(), 0.0);
        double media_infactibles = sum_infactibles / n_ejecuciones;

        csv_file << instancia_nombre << ";" << n_ejecuciones << ";" << max_beneficio << ";" 
                 << media_beneficios << ";" << min_beneficio << ";" << media_tiempos << ";" 
                 << media_factibles << ";" << media_infactibles << "\n";
    }

    csv_file.close();
    cout << "\nEjecuci�n finalizada. Archivo CSV generado.\n";
    return 0;
}
