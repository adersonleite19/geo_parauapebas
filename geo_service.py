import math
import os
import psycopg2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUERIES_PATH = os.path.join(BASE_DIR, "queries.sql")

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "geoprocessamento"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "123"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}

VELOCIDADES_KMH = {
    "Pessoa a pé": 5,
    "Bicicleta": 15,
    "Moto": 40,
    "Carro": 30,
    "Avião": 300,
}


def carregar_queries():
    queries = {}
    chave_atual = None
    linhas_atual = []

    with open(QUERIES_PATH, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            limpa = linha.strip()
            if limpa.startswith("-- [") and limpa.endswith("]"):
                if chave_atual:
                    queries[chave_atual] = "\n".join(linhas_atual).strip()
                chave_atual = limpa[4:-1]
                linhas_atual = []
            elif chave_atual:
                linhas_atual.append(linha.rstrip("\n"))

    if chave_atual:
        queries[chave_atual] = "\n".join(linhas_atual).strip()

    return queries


def haversine_km(lat1, lon1, lat2, lon2):
    r_terra_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return round(r_terra_km * c, 2)


def inicializar_banco():
    queries = carregar_queries()
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(queries["INIT_HISTORICO"])
        conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def buscar_locais():
    queries = carregar_queries()
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(queries["LISTAR_LOCAIS"])
        linhas = cur.fetchall()
    except Exception as exc:
        return {"erro": f"Falha ao consultar locais no PostGIS: {exc}"}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    locais = [
        {"nome": str(nome).strip(), "lat": float(lat), "lon": float(lon)}
        for nome, lat, lon in linhas
        if lat is not None and lon is not None
    ]
    return {"locais": locais}


def listar_historico():
    queries = carregar_queries()
    conn = None
    cur = None
    try:
        inicializar_banco()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(queries["LISTAR_HISTORICO"])
        linhas = cur.fetchall()
    except Exception as exc:
        return {"erro": f"Falha ao ler histórico: {exc}"}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    historico = [
        {
            "id": row[0],
            "origem": row[1],
            "destino": row[2],
            "distancia_km": float(row[3]),
            "tempo_pe_min": float(row[4]) if row[4] is not None else None,
            "tempo_moto_min": float(row[5]) if row[5] is not None else None,
            "tempo_carro_min": float(row[6]) if row[6] is not None else None,
            "criado_em": row[7],
        }
        for row in linhas
    ]
    return {"historico": historico}


def calcular_e_salvar_rota(origem_nome, destino_nome, salvar=True):
    if not origem_nome or not destino_nome:
        return {"erro": "Selecione a origem e o destino antes de calcular."}

    if origem_nome.strip().lower() == destino_nome.strip().lower():
        return {"erro": "A origem e o destino devem ser locais diferentes."}

    consulta = buscar_locais()
    if "erro" in consulta:
        return consulta

    locais = consulta["locais"]
    origem = next(
        (item for item in locais if item["nome"].lower() == origem_nome.strip().lower()),
        None,
    )
    destino = next(
        (item for item in locais if item["nome"].lower() == destino_nome.strip().lower()),
        None,
    )

    if not origem or not destino:
        return {"erro": "Origem ou destino não encontrado na tabela locais."}

    distancia_km = haversine_km(
        origem["lat"], origem["lon"], destino["lat"], destino["lon"]
    )

    estimativas = [
        {
            "modal": modal,
            "velocidade_kmh": vel,
            "minutos": round((distancia_km / vel) * 60, 1),
        }
        for modal, vel in VELOCIDADES_KMH.items()
    ]

    tempos_map = {item["modal"]: item["minutos"] for item in estimativas}
    registro_salvo = None

    if salvar:
        queries = carregar_queries()
        conn = None
        cur = None
        try:
            inicializar_banco()
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                queries["INSERIR_HISTORICO"],
                (
                    origem["nome"],
                    destino["nome"],
                    distancia_km,
                    tempos_map.get("Pessoa a pé"),
                    tempos_map.get("Moto"),
                    tempos_map.get("Carro"),
                ),
            )
            salvo = cur.fetchone()
            conn.commit()
            if salvo:
                registro_salvo = {"id": salvo[0], "criado_em": salvo[1]}
        except Exception as exc:
            return {"erro": f"Rota calculada, mas falhou ao salvar no banco: {exc}"}
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return {
        "origem": origem,
        "destino": destino,
        "distancia_km": distancia_km,
        "estimativas": estimativas,
        "registro_salvo": registro_salvo,
    }
