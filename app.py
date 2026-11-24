from flask import Flask, jsonify, render_template, request
from geo_service import buscar_locais, calcular_e_salvar_rota, listar_historico

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/locais", methods=["GET"])
def api_locais():
    dados = buscar_locais()
    status = 400 if "erro" in dados else 200
    return jsonify(dados), status


@app.route("/api/rota", methods=["POST"])
def api_rota():
    payload = request.get_json(silent=True) or {}
    origem = payload.get("origem")
    destino = payload.get("destino")
    salvar = bool(payload.get("salvar", True))

    dados = calcular_e_salvar_rota(origem, destino, salvar=salvar)
    status = 400 if "erro" in dados else 200
    return jsonify(dados), status


@app.route("/api/historico", methods=["GET"])
def api_historico():
    dados = listar_historico()
    status = 400 if "erro" in dados else 200
    return jsonify(dados), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
