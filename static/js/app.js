const centroInicial = [-6.085, -49.882];
const mapa = L.map("map").setView(centroInicial, 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors"
}).addTo(mapa);

const camadaRota = L.layerGroup().addTo(mapa);

function limparMapa() {
  camadaRota.clearLayers();
  mapa.setView(centroInicial, 13);
  document.getElementById("boxErro").style.display = "none";
  document.getElementById("boxOk").style.display = "none";
  document.getElementById("resumo").innerHTML =
    "Mapa limpo. Escolha uma origem e um destino para consultar.";
  document.getElementById("tabelaModais").innerHTML = "";
}

async function carregarLocais() {
  const boxErro = document.getElementById("boxErro");
  const selOrigem = document.getElementById("selectOrigem");
  const selDestino = document.getElementById("selectDestino");

  try {
    const resp = await fetch("/api/locais");
    const dados = await resp.json();
    if (!resp.ok || dados.erro) {
      throw new Error(dados.erro || "Erro ao carregar locais.");
    }

    const opcoes = ['<option value="">-- Selecione um local --</option>']
      .concat(dados.locais.map((l) => `<option value="${l.nome}">${l.nome}</option>`))
      .join("");

    selOrigem.innerHTML = opcoes;
    selDestino.innerHTML = opcoes;
  } catch (err) {
    boxErro.textContent = err.message;
    boxErro.style.display = "block";
  }
}

async function carregarHistorico() {
  const tbody = document.getElementById("tabelaHistorico");
  try {
    const resp = await fetch("/api/historico");
    const dados = await resp.json();
    if (!resp.ok || dados.erro) {
      throw new Error(dados.erro || "Erro ao carregar histórico.");
    }

    if (!dados.historico.length) {
      tbody.innerHTML = '<tr><td colspan="8">Nenhuma rota salva no banco ainda.</td></tr>';
      return;
    }

    tbody.innerHTML = dados.historico
      .map(
        (h) => `
          <tr>
            <td>${h.id}</td>
            <td>${h.origem}</td>
            <td>${h.destino}</td>
            <td>${h.distancia_km} km</td>
            <td>${h.tempo_pe_min ?? "-"} min</td>
            <td>${h.tempo_moto_min ?? "-"} min</td>
            <td>${h.tempo_carro_min ?? "-"} min</td>
            <td>${h.criado_em}</td>
          </tr>
        `
      )
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8">${err.message}</td></tr>`;
  }
}

async function calcularRota(salvar = true) {
  const boxErro = document.getElementById("boxErro");
  const boxOk = document.getElementById("boxOk");
  const resumo = document.getElementById("resumo");
  const tbody = document.getElementById("tabelaModais");

  const origem = document.getElementById("selectOrigem").value;
  const destino = document.getElementById("selectDestino").value;

  boxErro.style.display = "none";
  boxOk.style.display = "none";

  try {
    const resp = await fetch("/api/rota", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origem, destino, salvar })
    });
    const dados = await resp.json();

    if (!resp.ok || dados.erro) {
      throw new Error(dados.erro || "Erro ao calcular rota.");
    }

    const pOrigem = [dados.origem.lat, dados.origem.lon];
    const pDestino = [dados.destino.lat, dados.destino.lon];

    camadaRota.clearLayers();
    L.marker(pOrigem).addTo(camadaRota).bindPopup(`<b>Origem:</b> ${dados.origem.nome}`);
    L.marker(pDestino).addTo(camadaRota).bindPopup(`<b>Destino:</b> ${dados.destino.nome}`);

    const linha = L.polyline([pOrigem, pDestino], { color: "#2563eb", weight: 4 }).addTo(camadaRota);
    mapa.fitBounds(linha.getBounds(), { padding: [35, 35] });

    resumo.innerHTML = `
      <p><strong>Origem:</strong> ${dados.origem.nome}</p>
      <p><strong>Destino:</strong> ${dados.destino.nome}</p>
      <p><strong>Distância:</strong> ${dados.distancia_km} km</p>
    `;

    tbody.innerHTML = dados.estimativas
      .map(
        (item) => `
          <tr>
            <td>${item.modal}</td>
            <td>${item.velocidade_kmh} km/h</td>
            <td>${item.minutos} min</td>
          </tr>
        `
      )
      .join("");

    if (dados.registro_salvo) {
      boxOk.textContent = `Rota salva no PostgreSQL (Registro #${dados.registro_salvo.id} em ${dados.registro_salvo.criado_em}).`;
      boxOk.style.display = "block";
      await carregarHistorico();
    }
  } catch (err) {
    boxErro.textContent = err.message;
    boxErro.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  carregarLocais();
  carregarHistorico();
});
