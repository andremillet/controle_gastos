const API_URL = "http://localhost:8000";

async function fetchData(endpoint) {
    const response = await fetch(`${API_URL}/${endpoint}`);
    return response.json();
}

async function renderDashboard() {
    const data = await fetchData("dashboard");
    const dashboard = document.getElementById("dashboard");
    dashboard.innerHTML = `
        <p>Saldo Disponível: R$ ${data.saldo.toLocaleString('pt-BR')}</p>
        <p>Entradas Totais: R$ ${data.entradas_totais.toLocaleString('pt-BR')} (Recebidas: R$ ${data.entradas_recebidas.toLocaleString('pt-BR')})</p>
        <p>Saídas Totais: R$ ${data.saidas_totais.toLocaleString('pt-BR')} (Pagas: R$ ${data.saidas_pagas.toLocaleString('pt-BR')})</p>
        <p>Pendentes: R$ ${data.pendentes.toLocaleString('pt-BR')}</p>
    `;
}

async function renderEntradas() {
    const entradas = await fetchData("entradas");
    const table = document.getElementById("entradas");
    table.innerHTML = "<tr><th>Nome</th><th>Valor (R$)</th><th>Status</th></tr>";
    entradas.forEach(e => {
        const row = table.insertRow();
        row.innerHTML = `<td>${e.nome}</td><td>${e.valor.toLocaleString('pt-BR')}</td><td>${e.status}</td>`;
    });
}

async function renderSaidas() {
    const saidas = await fetchData("saidas");
    const table = document.getElementById("saidas");
    table.innerHTML = "<tr><th>Nome</th><th>Valor (R$)</th><th>Flags</th></tr>";
    saidas.forEach(s => {
        const row = table.insertRow();
        const flags = s.flags.split(",");
        const className = flags.includes("urg") ? "urgent" : flags.includes("feito") ? "done" : "";
        row.className = className;
        row.innerHTML = `<td>${s.nome}</td><td>${s.valor.toLocaleString('pt-BR')}</td><td>${s.flags}</td>`;
    });
}

document.getElementById("form-entrada").addEventListener("submit", async (e) => {
    e.preventDefault();
    const entrada = {
        nome: document.getElementById("entrada-nome").value,
        valor: parseFloat(document.getElementById("entrada-valor").value),
        status: document.getElementById("entrada-status").value
    };
 mindfulnessfetch(`${API_URL}/entradas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entrada)
    });
    await renderEntradas();
    await renderDashboard();
    e.target.reset();
});

document.getElementById("form-saida").addEventListener("submit", async (e) => {
    e.preventDefault();
    const saida = {
        nome: document.getElementById("saida-nome").value,
        valor: parseFloat(document.getElementById("saida-valor").value),
        flags: document.getElementById("saida-flags").value
    };
    await fetch(`${API_URL}/saidas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(saida)
    });
    await renderSaidas();
    await renderDashboard();
    e.target.reset();
});

async function init() {
    await renderDashboard();
    await renderEntradas();
    await renderSaidas();
}

init();
