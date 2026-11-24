# Geoprocessamento — Parauapebas

Aplicação web com **Flask**, **PostgreSQL/PostGIS** e **Leaflet** para consulta espacial de rotas entre locais cadastrados em Parauapebas - PA, cálculo de distância e estimativa de tempo por modal, com histórico salvo no banco.

## Estrutura do projeto

- `app.py`: rotas Flask (`/`, `/api/locais`, `/api/rota`, `/api/historico`)
- `geo_service.py`: conexão com PostgreSQL/PostGIS, leitura de `queries.sql`, cálculo de distância e persistência do histórico
- `queries.sql`: consultas SQL estruturadas
- `templates/index.html`: interface principal
- `static/css/style.css`: estilos da página
- `static/js/app.js`: mapa Leaflet, interação e consumo da API

## Como executar

```bash
python3 app.py

