-- [INIT_HISTORICO]
CREATE TABLE IF NOT EXISTS historico_rotas (
    id SERIAL PRIMARY KEY,
    origem VARCHAR(150) NOT NULL,
    destino VARCHAR(150) NOT NULL,
    distancia_km NUMERIC(10, 2) NOT NULL,
    tempo_pe_min NUMERIC(10, 1),
    tempo_moto_min NUMERIC(10, 1),
    tempo_carro_min NUMERIC(10, 1),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- [LISTAR_LOCAIS]
SELECT TRIM(nome), ST_Y(geom), ST_X(geom)
FROM locais
WHERE nome IS NOT NULL AND geom IS NOT NULL
ORDER BY TRIM(nome);

-- [INSERIR_HISTORICO]
INSERT INTO historico_rotas (
    origem, destino, distancia_km, tempo_pe_min, tempo_moto_min, tempo_carro_min
)
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING id, TO_CHAR(criado_em, 'DD/MM/YYYY HH24:MI:SS');

-- [LISTAR_HISTORICO]
SELECT
    id,
    origem,
    destino,
    distancia_km,
    tempo_pe_min,
    tempo_moto_min,
    tempo_carro_min,
    TO_CHAR(criado_em, 'DD/MM/YYYY HH24:MI:SS')
FROM historico_rotas
ORDER BY id DESC
LIMIT 15;
