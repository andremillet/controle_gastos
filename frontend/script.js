const API_URL = "http://localhost:8000";

async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_URL}/${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Erro ao buscar ${endpoint}:`, error);
        return null;
    }
}

async function renderDashboard() {
    const data = await fetchData("dashboard");
    const dashboard = document.getElementById("dashboard");
    if (data) {
        dashboard.innerHTML = `
            <p>Saldo Disponível: R$ ${data.saldo.toLocaleString('pt-BR')}</p>
            <p>Entradas Totais: R$ ${data.entradas_totais.toLocaleString('pt-BR')} (Recebidas: R$ ${data.entradas_recebidas.toLocaleString('pt-BR')})</p>
            <p>Saídas Totais: R$ ${data.saidas_totais.toLocaleString('pt-BR')} (Pagas: R$ ${data.saidas_pagas.toLocaleString('pt-BR')})</p>
            <p>Pendentes: R$ ${data.pendentes.toLocaleString('pt-BR')}</p>
        `;
    } else {
        dashboard.innerHTML = "<p>Erro ao carregar o dashboard.</p>";
    }
}

async function renderEntradas() {
    const entradas = await fetchData("entradas");
    const table = document.getElementById("entradas");
    table.innerHTML = `
        <tr>
            <th data-label="Nome">Nome</th>
            <th data-label="Valor (R$)">Valor (R$)</th>
            <th data-label="Status">Status</th>
            <th data-label="Ações">Ações</th>
        </tr>
    `;
    if (entradas) {
        entradas.forEach(e => {
            const row = table.insertRow();
            row.innerHTML = `
                <td data-label="Nome">${e.nome}</td>
                <td data-label="Status">${e.status}</td>
                <td data-label="Valor (R$)">${e.valor.toLocaleString('pt-BR')}</td>
                <td data-label="Ações">
                    <button class="edit" onclick="showEditEntrada(${e.id}, '${e.nome}', ${e.valor}, '${e.status}')">Editar</button>
                    <button class="delete" onclick="deleteEntrada(${e.id})">Remover</button>
                </td>
            `;
            const editRow = table.insertRow();
            editRow.id = `edit-entrada-${e.id}`;
            editRow.className = "edit-form";
            editRow.innerHTML = `
                <td colspan="4">
                    <form onsubmit="updateEntrada(event, ${e.id})">
                        <input type="text" id="edit-entrada-nome-${e.id}" value="${e.nome}" required>
                        <input type="number" id="edit-entrada-valor-${e.id}" value="${e.valor}" step="0.01" required>
                        <select id="edit-entrada-status-${e.id}">
                            <option value="pendente" ${e.status === 'pendente' ? 'selected' : ''}>Pendente</option>
                            <option value="recebido" ${e.status === 'recebido' ? 'selected' : ''}>Recebido</option>
                        </select>
                        <button type="submit">Salvar</button>
                        <button type="button" onclick="hideEditEntrada(${e.id})">Cancelar</button>
                    </form>
                </td>
            `;
        });
    } else {
        const row = table.insertRow();
        row.innerHTML = "<td colspan='4'>Erro ao carregar entradas.</td>";
    }
}

async function renderSaidas() {
    const saidas = await fetchData("saidas");
    const table = document.getElementById("saidas");
    table.innerHTML = `
        <tr>
            <th data-label="Nome">Nome</th>
            <th data-label="Valor (R$)">Valor (R$)</th>
            <th data-label="Flags">Flags</th>
            <th data-label="Ações">Ações</th>
        </tr>
    `;
    if (saidas) {
        saidas.forEach(s => {
            const row = table.insertRow();
            const flags = s.flags.split(",");
            const className = flags.includes("urg") ? "urgent" : flags.includes("feito") ? "done" : "";
            row.className = className;
           row.innerHTML = `
                <td data-label="Nome">${s.nome}</td>
                <td data-label="Valor (R$)">${s.valor.toLocaleString('pt-BR')}</td>
                <td data-label="Flags">${s.flags}</td>
                <td data-label="Ações">
                    <button class="edit" onclick="showEditSaida(${s.id}, '${s.nome}', ${s.valor}, '${s.flags}')">Editar</button>
                    <button class="delete" onclick="deleteSaida(${s.id})">Remover</button>
                </td>
            `;
            const editRow = table.insertRow();
            editRow.id = `edit-saida-${s.id}`;
            editRow.className = "edit-form";
            editRow.innerHTML = `
                <td colspan="4">
                    <form onsubmit="updateSaida(event, ${s.id})">
                        <input type="text" id="edit-saida-nome-${s.id}" value="${s.nome}" required>
                        <input type="number" id="edit-saida-valor-${s.id}" value="${s.valor}" step="0.01" required>
                        <input type="text" id="edit-saida-flags-${s.id}" value="${s.flags}" placeholder="Flags (ex: urg,feito)">
                        <button type="submit">Salvar</button>
                        <button type="button" onclick="hideEditSaida(${s.id})">Cancelar</button>
                    </form>
                </td>
            `;
        });
    } else {
        const row = table.insertRow();
        row.innerHTML = "<td colspan='4'>Erro ao carregar saídas.</td>";
    }
}

// Funções para Entradas
function showEditEntrada(id, nome, valor, status) {
    document.getElementById(`edit-entrada-${id}`).style.display = "table-row";
}

function hideEditEntrada(id) {
    document.getElementById(`edit-entrada-${id}`).style.display = "none";
}

async function updateEntrada(event, id) {
    event.preventDefault();
    const entrada = {
        nome: document.getElementById(`edit-entrada-nome-${id}`).value,
        valor: parseFloat(document.getElementById(`edit-entrada-valor-${id}`).value),
        status: document.getElementById(`edit-entrada-status-${id}`).value
    };
    const response = await fetch(`${API_URL}/entradas/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entrada)
    });
    if (response.ok) {
        hideEditEntrada(id);
        await renderEntradas();
        await renderDashboard();
    } else {
        console.error("Erro ao atualizar entrada:", response.status);
    }
}

async function deleteEntrada(id) {
    if (confirm("Tem certeza que deseja remover esta entrada?")) {
        const response = await fetch(`${API_URL}/entradas/${id}`, {
            method: "DELETE"
        });
        if (response.ok) {
            await renderEntradas();
            await renderDashboard();
        } else {
            console.error("Erro ao deletar entrada:", response.status);
        }
    }
}

// Funções para Saídas
function showEditSaida(id, nome, valor, flags) {
    document.getElementById(`edit-saida-${id}`).style.display = "table-row";
}

function hideEditSaida(id) {
    document.getElementById(`edit-saida-${id}`).style.display = "none";
}

async function updateSaida(event, id) {
    event.preventDefault();
    const saida = {
        nome: document.getElementById(`edit-saida-nome-${id}`).value,
        valor: parseFloat(document.getElementById(`edit-saida-valor-${id}`).value),
        flags: document.getElementById(`edit-saida-flags-${id}`).value
    };
    const response = await fetch(`${API_URL}/saidas/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(saida)
    });
    if (response.ok) {
        hideEditSaida(id);
        await renderSaidas();
        await renderDashboard();
    } else {
        console.error("Erro ao atualizar saída:", response.status);
    }
}

async function deleteSaida(id) {
    if (confirm("Tem certeza que deseja remover esta saída?")) {
        const response = await fetch(`${API_URL}/saidas/${id}`, {
            method: "DELETE"
        });
        if (response.ok) {
            await renderSaidas();
            await renderDashboard();
        } else {
            console.error("Erro ao deletar saída:", response.status);
        }
    }
}

// Formulários de Adição
document.getElementById("form-entrada").addEventListener("submit", async (e) => {
    e.preventDefault();
    const entrada = {
        nome: document.getElementById("entrada-nome").value,
        valor: parseFloat(document.getElementById("entrada-valor").value),
        status: document.getElementById("entrada-status").value
    };
    const response = await fetch(`${API_URL}/entradas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entrada)
    });
    if (response.ok) {
        await renderEntradas();
        await renderDashboard();
        e.target.reset();
    } else {
        console.error("Erro ao adicionar entrada:", response.status);
    }
});

document.getElementById("form-saida").addEventListener("submit", async (e) => {
    e.preventDefault();
    const saida = {
        nome: document.getElementById("saida-nome").value,
        valor: parseFloat(document.getElementById("saida-valor").value),
        flags: document.getElementById("saida-flags").value
    };
    const response = await fetch(`${API_URL}/saidas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(saida)
    });
    if (response.ok) {
        await renderSaidas();
        await renderDashboard();
        e.target.reset();
    } else {
        console.error("Erro ao adicionar saída:", response.status);
    }
});

async function init() {
    await renderDashboard();
    await renderEntradas();
    await renderSaidas();
}

init(); 
