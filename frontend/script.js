const API_URL = "http://localhost:8000";

// Estado global
let currentMonth = {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1 // JavaScript meses são 0-indexed
};
let viewMode = {
    entradas: "month", // "month" ou "all"
    saidas: "month"    // "month" ou "all"
};

async function fetchData(endpoint, params = {}) {
    try {
        // Construir URL com parâmetros de consulta, se houver
        let url = `${API_URL}/${endpoint}`;
        if (Object.keys(params).length > 0) {
            const queryParams = new URLSearchParams();
            for (const [key, value] of Object.entries(params)) {
                if (value !== null && value !== undefined) {
                    queryParams.append(key, value);
                }
            }
            url += `?${queryParams.toString()}`;
        }
        
        const response = await fetch(url);
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

// Buscar e preencher o seletor de meses disponíveis
async function populateMonthSelector() {
    const mesesDisponiveis = await fetchData("meses-disponiveis");
    const monthSelect = document.getElementById("month-select");
    
    // Limpar opções existentes exceto a primeira (mês atual)
    while (monthSelect.options.length > 1) {
        monthSelect.remove(1);
    }
    
    // Adicionar o mês atual com a data formatada
    const hoje = new Date();
    const mesAtualOption = monthSelect.options[0];
    mesAtualOption.text = `${getNomeMes(hoje.getMonth() + 1)} ${hoje.getFullYear()} (Atual)`;
    
    // Adicionar meses disponíveis no histórico
    if (mesesDisponiveis && mesesDisponiveis.length > 0) {
        mesesDisponiveis.forEach(mes => {
            // Verificar se não é o mês atual
            if (mes.ano !== hoje.getFullYear() || mes.mes !== hoje.getMonth() + 1) {
                const option = document.createElement("option");
                option.value = `${mes.ano}-${mes.mes}`;
                option.text = `${getNomeMes(mes.mes)} ${mes.ano}`;
                monthSelect.appendChild(option);
            }
        });
    }
}

// Função para obter o nome do mês em português
function getNomeMes(mesNumero) {
    const meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ];
    return meses[mesNumero - 1];
}

// Formatar data para exibição
function formatarData(dataString) {
    if (!dataString) return "";
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR');
}

async function renderDashboard() {
    // Passar ano e mês para o endpoint de dashboard se não for o mês atual
    let params = {};
    if (currentMonth.year && currentMonth.month) {
        params = {
            ano: currentMonth.year,
            mes: currentMonth.month
        };
    }
    
    const data = await fetchData("dashboard", params);
    const dashboard = document.getElementById("dashboard");
    
    if (data) {
        dashboard.innerHTML = `
            <div class="mes-referencia">${data.mes_referencia}</div>
            <p>Saldo Disponível: R$ ${data.saldo.toLocaleString('pt-BR')}</p>
            <p>Entradas Totais: R$ ${data.entradas_totais.toLocaleString('pt-BR')} (Recebidas: R$ ${data.entradas_recebidas.toLocaleString('pt-BR')})</p>
            <p>Saídas Totais: R$ ${data.saidas_totais.toLocaleString('pt-BR')} (Pagas: R$ ${data.saidas_pagas.toLocaleString('pt-BR')})</p>
            <p>Pendentes: R$ ${data.pendentes.toLocaleString('pt-BR')}</p>
            <p>Compras Parceladas: ${data.total_itens_parcelados} itens</p>
            <p>Próximas Parcelas (30 dias): R$ ${data.proximas_parcelas.toLocaleString('pt-BR')}</p>
        `;
    } else {
        dashboard.innerHTML = "<p>Erro ao carregar o dashboard.</p>";
    }
}

async function renderEntradas() {
    let entradas;
    let endpoint = "entradas";
    let params = {};
    
    // Verificar o modo de visualização
    if (viewMode.entradas === "all") {
        endpoint = "entradas/todos";
    } else {
        // Modo mensal - usar parâmetros de ano e mês
        params = {
            ano: currentMonth.year,
            mes: currentMonth.month
        };
    }
    
    entradas = await fetchData(endpoint, params);
    
    const table = document.getElementById("entradas");
    table.innerHTML = `
        <tr>
            <th data-label="Nome">Nome</th>
            <th data-label="Valor (R$)">Valor (R$)</th>
            <th data-label="Status">Status</th>
            <th data-label="Data">Data</th>
            <th data-label="Ações">Ações</th>
        </tr>
    `;
    
    if (entradas && entradas.length > 0) {
        entradas.forEach(e => {
            const row = table.insertRow();
            const dataFormatada = formatarData(e.data);
            
            row.innerHTML = `
                <td data-label="Nome">${e.nome}</td>
                <td data-label="Valor (R$)">${e.valor.toLocaleString('pt-BR')}</td>
                <td data-label="Status">${e.status}</td>
                <td data-label="Data">${dataFormatada}</td>
                <td data-label="Ações">
                    <button class="edit" onclick="showEditEntrada(${e.id}, '${e.nome}', ${e.valor}, '${e.status}', '${e.data || ''}')">Editar</button>
                    <button class="delete" onclick="deleteEntrada(${e.id})">Remover</button>
                </td>
            `;
            const editRow = table.insertRow();
            editRow.id = `edit-entrada-${e.id}`;
            editRow.className = "edit-form";
            editRow.innerHTML = `
                <td colspan="5">
                    <form onsubmit="updateEntrada(event, ${e.id})">
                        <input type="text" id="edit-entrada-nome-${e.id}" value="${e.nome}" required>
                        <input type="number" id="edit-entrada-valor-${e.id}" value="${e.valor}" step="0.01" required>
                        <select id="edit-entrada-status-${e.id}">
                            <option value="pendente" ${e.status === 'pendente' ? 'selected' : ''}>Pendente</option>
                            <option value="recebido" ${e.status === 'recebido' ? 'selected' : ''}>Recebido</option>
                        </select>
                        <input type="date" id="edit-entrada-data-${e.id}" value="${e.data || ''}">
                        <div class="form-buttons">
                            <button type="submit">Salvar</button>
                            <button type="button" onclick="hideEditEntrada(${e.id})">Cancelar</button>
                        </div>
                    </form>
                </td>
            `;
        });
    } else {
        const row = table.insertRow();
        row.innerHTML = `<td colspan='5' style='text-align: center;'>
            ${entradas ? 'Nenhuma entrada encontrada neste período.' : 'Erro ao carregar entradas.'}
        </td>`;
    }
    
    // Atualizar botões de visualização
    document.getElementById("show-all-entradas").classList.toggle("active", viewMode.entradas === "all");
    document.getElementById("show-month-entradas").classList.toggle("active", viewMode.entradas === "month");
}

// Função auxiliar para verificar se uma data está próxima (dentro de 7 dias)
function isDateNear(dateString) {
    if (!dateString) return false;
    
    const today = new Date();
    const date = new Date(dateString);
    const diffTime = date.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays >= 0 && diffDays <= 7;
}

// Função auxiliar para verificar se uma data está atrasada
function isDateOverdue(dateString) {
    if (!dateString) return false;
    
    const today = new Date();
    const date = new Date(dateString);
    
    return date < today;
}

async function renderSaidas() {
    let saidas;
    let endpoint = "saidas";
    let params = {};
    
    // Verificar o modo de visualização
    if (viewMode.saidas === "all") {
        endpoint = "saidas/todos";
    } else {
        // Modo mensal - usar parâmetros de ano e mês
        params = {
            ano: currentMonth.year,
            mes: currentMonth.month
        };
    }
    
    saidas = await fetchData(endpoint, params);
    const filterValue = document.getElementById("filter-saidas").value;
    
    const table = document.getElementById("saidas");
    table.innerHTML = `
        <tr>
            <th data-label="Nome">Nome</th>
            <th data-label="Valor (R$)">Valor (R$)</th>
            <th data-label="Flags">Flags</th>
            <th data-label="Vencimento">Vencimento</th>
            <th data-label="Parcelas">Parcelas</th>
            <th data-label="Ações">Ações</th>
        </tr>
    `;
    
    if (saidas && saidas.length > 0) {
        // Filtrar os dados com base na seleção
        let filteredSaidas = saidas;
        
        if (filterValue === "parcelas") {
            filteredSaidas = saidas.filter(s => s.total_parcelas > 1);
        } else if (filterValue === "nao-parcelas") {
            filteredSaidas = saidas.filter(s => !s.total_parcelas || s.total_parcelas <= 1);
        } else if (filterValue === "proximas") {
            const today = new Date();
            const nextMonth = new Date(today);
            nextMonth.setDate(today.getDate() + 30);
            
            filteredSaidas = saidas.filter(s => {
                const vencimento = new Date(s.data_vencimento);
                return vencimento >= today && vencimento <= nextMonth;
            });
        }
        
        if (filteredSaidas.length === 0) {
            const row = table.insertRow();
            row.innerHTML = `<td colspan='6' style='text-align: center;'>
                Nenhuma saída encontrada com os filtros selecionados.
            </td>`;
        } else {
            filteredSaidas.forEach(s => {
                const row = table.insertRow();
                const flags = s.flags ? s.flags.split(",") : [];
                
                // Determinar a classe do item com base em flags e parcelamento
                let className = "";
                if (flags.includes("urg")) className += "urgent ";
                if (flags.includes("feito")) className += "done ";
                if (s.total_parcelas > 1) className += "parcela ";
                
                row.className = className.trim();
                
                // Verifica se o vencimento está próximo ou atrasado
                let vencimentoClass = "";
                if (isDateNear(s.data_vencimento)) vencimentoClass = "vencimento-proxima";
                if (isDateOverdue(s.data_vencimento)) vencimentoClass = "vencimento-atrasado";
                
                // Formatar a data de vencimento
                const dataVencimento = formatarData(s.data_vencimento);
                
                // Informações de parcela
                let parcelaInfo = "";
                if (s.total_parcelas > 1) {
                    parcelaInfo = `${s.parcela_atual}/${s.total_parcelas}`;
                }
                
                row.innerHTML = `
                    <td data-label="Nome">${s.nome}</td>
                    <td data-label="Valor (R$)">${s.valor.toLocaleString('pt-BR')}</td>
                    <td data-label="Flags">${s.flags || ''}</td>
                    <td data-label="Vencimento" class="${vencimentoClass}">${dataVencimento}</td>
                    <td data-label="Parcelas">${parcelaInfo}</td>
                    <td data-label="Ações">
                        <button class="edit" onclick="showEditSaida(${s.id}, '${s.nome}', ${s.valor}, '${s.flags || ''}', '${s.data_vencimento || ''}')">Editar</button>
                        <button class="delete" onclick="deleteSaida(${s.id}, ${s.id_grupo_parcela || 'null'})">Remover</button>
                    </td>
                `;
                
                const editRow = table.insertRow();
                editRow.id = `edit-saida-${s.id}`;
                editRow.className = "edit-form";
                editRow.innerHTML = `
                    <td colspan="6">
                        <form onsubmit="updateSaida(event, ${s.id})">
                            <input type="text" id="edit-saida-nome-${s.id}" value="${s.nome}" required>
                            <input type="number" id="edit-saida-valor-${s.id}" value="${s.valor}" step="0.01" required>
                            <input type="text" id="edit-saida-flags-${s.id}" value="${s.flags || ''}" placeholder="Flags (ex: urg,feito)">
                            <input type="date" id="edit-saida-data-vencimento-${s.id}" value="${s.data_vencimento || ''}">
                            <div class="form-buttons">
                                <button type="submit">Salvar</button>
                                <button type="button" onclick="hideEditSaida(${s.id})">Cancelar</button>
                            </div>
                        </form>
                    </td>
                `;
            });
        }
    } else {
        const row = table.insertRow();
        row.innerHTML = `<td colspan='6' style='text-align: center;'>
            ${saidas ? 'Nenhuma saída encontrada neste período.' : 'Erro ao carregar saídas.'}
        </td>`;
    }
    
    // Atualizar botões de visualização
    document.getElementById("show-all-saidas").classList.toggle("active", viewMode.saidas === "all");
    document.getElementById("show-month-saidas").classList.toggle("active", viewMode.saidas === "month");
}

// Funções para Entradas
function showEditEntrada(id, nome, valor, status, data) {
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
        status: document.getElementById(`edit-entrada-status-${id}`).value,
        data: document.getElementById(`edit-entrada-data-${id}`).value || null
    };
    
    try {
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
            const errorData = await response.json();
            console.error("Erro ao atualizar entrada:", errorData);
            alert(`Erro ao atualizar: ${errorData.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error("Erro ao atualizar entrada:", error);
        alert(`Erro ao atualizar: ${error.message}`);
    }
}

async function deleteEntrada(id) {
    if (confirm("Tem certeza que deseja remover esta entrada?")) {
        try {
            const response = await fetch(`${API_URL}/entradas/${id}`, {
                method: "DELETE"
            });
            
            if (response.ok) {
                await renderEntradas();
                await renderDashboard();
            } else {
                const errorData = await response.json();
                console.error("Erro ao deletar entrada:", errorData);
                alert(`Erro ao deletar: ${errorData.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            console.error("Erro ao deletar entrada:", error);
            alert(`Erro ao deletar: ${error.message}`);
        }
    }
}

// Funções para Saídas
function showEditSaida(id, nome, valor, flags, dataVencimento) {
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
        flags: document.getElementById(`edit-saida-flags-${id}`).value,
        data_vencimento: document.getElementById(`edit-saida-data-vencimento-${id}`).value || null
    };
    
    try {
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
            const errorData = await response.json();
            console.error("Erro ao atualizar saída:", errorData);
            alert(`Erro ao atualizar: ${errorData.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error("Erro ao atualizar saída:", error);
        alert(`Erro ao atualizar: ${error.message}`);
    }
}

async function deleteSaida(id, grupoId) {
    if (grupoId) {
        // É uma parcela de um grupo
        const options = ["Apenas esta parcela", "Todas as parcelas restantes"];
        const choice = confirm("Deseja excluir apenas esta parcela ou todas as parcelas?");
        
        if (choice === null) return; // Cancelou
        
        if (choice) {
            // Excluir todas as parcelas restantes
            try {
                const response = await fetch(`${API_URL}/saidas/grupo/${grupoId}`, {
                    method: "DELETE"
                });
                
                if (response.ok) {
                    await renderSaidas();
                    await renderDashboard();
                } else {
                    const errorData = await response.json();
                    console.error("Erro ao deletar grupo de parcelas:", errorData);
                    alert(`Erro ao deletar: ${errorData.detail || 'Erro desconhecido'}`);
                }
            } catch (error) {
                console.error("Erro ao deletar grupo de parcelas:", error);
                alert(`Erro ao deletar: ${error.message}`);
            }
        } else {
            // Excluir apenas esta parcela
            try {
                const response = await fetch(`${API_URL}/saidas/${id}`, {
                    method: "DELETE"
                });
                
                if (response.ok) {
                    await renderSaidas();
                    await renderDashboard();
                } else {
                    const errorData = await response.json();
                    console.error("Erro ao deletar parcela:", errorData);
                    alert(`Erro ao deletar: ${errorData.detail || 'Erro desconhecido'}`);
                }
            } catch (error) {
                console.error("Erro ao deletar parcela:", error);
                alert(`Erro ao deletar: ${error.message}`);
            }
        }
    } else {
        // Exclusão normal (não é parte de um grupo de parcelas)
        if (confirm("Tem certeza que deseja remover esta saída?")) {
            try {
                const response = await fetch(`${API_URL}/saidas/${id}`, {
                    method: "DELETE"
                });
                
                if (response.ok) {
                    await renderSaidas();
                    await renderDashboard();
                } else {
                    const errorData = await response.json();
                    console.error("Erro ao deletar saída:", errorData);
                    alert(`Erro ao deletar: ${errorData.detail || 'Erro desconhecido'}`);
                }
            } catch (error) {
                console.error("Erro ao deletar saída:", error);
                alert(`Erro ao deletar: ${error.message}`);
            }
        }
    }
}

// Formulários de Adição
document.addEventListener("DOMContentLoaded", function() {
    // Mostrar/ocultar formulário de entrada
    document.getElementById("add-entrada-btn").addEventListener("click", function() {
        document.getElementById("form-entrada-container").style.display = "block";
    });
    
    document.getElementById("cancel-entrada-btn").addEventListener("click", function() {
        document.getElementById("form-entrada-container").style.display = "none";
    });
    
    // Mostrar/ocultar formulário de saída
    document.getElementById("add-saida-btn").addEventListener("click", function() {
        document.getElementById("form-saida-container").style.display = "block";
    });
    
    document.getElementById("cancel-saida-btn").addEventListener("click", function() {
        document.getElementById("form-saida-container").style.display = "none";
    });
    
    // Botões para alternar entre visualização mensal e todos os meses
    document.getElementById("show-all-entradas").addEventListener("click", function() {
        viewMode.entradas = "all";
        renderEntradas();
    });
    
    document.getElementById("show-month-entradas").addEventListener("click", function() {
        viewMode.entradas = "month";
        renderEntradas();
    });
    
    document.getElementById("show-all-saidas").addEventListener("click", function() {
        viewMode.saidas = "all";
        renderSaidas();
    });
    
    document.getElementById("show-month-saidas").addEventListener("click", function() {
        viewMode.saidas = "month";
        renderSaidas();
    });
    
    // Adicionar evento para o seletor de mês
    document.getElementById("month-select").addEventListener("change", function() {
        const selectedValue = this.value;
        
        if (selectedValue === "current") {
            // Mês atual
            currentMonth = {
                year: new Date().getFullYear(),
                month: new Date().getMonth() + 1
            };
        } else {
            // Mês específico no formato "YYYY-MM"
            const [year, month] = selectedValue.split("-");
            currentMonth = {
                year: parseInt(year),
                month: parseInt(month)
            };
        }
        
        // Recarregar os dados com o novo mês
        renderDashboard();
        if (viewMode.entradas === "month") renderEntradas();
        if (viewMode.saidas === "month") renderSaidas();
    });
});

document.getElementById("form-entrada").addEventListener("submit", async (e) => {
    e.preventDefault();
    const entrada = {
        nome: document.getElementById("entrada-nome").value,
        valor: parseFloat(document.getElementById("entrada-valor").value),
        status: document.getElementById("entrada-status").value,
        data: document.getElementById("entrada-data").value || null
    };
    
    try {
        const response = await fetch(`${API_URL}/entradas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entrada)
        });
        
        if (response.ok) {
            await renderEntradas();
            await renderDashboard();
            e.target.reset();
            document.getElementById("form-entrada-container").style.display = "none";
        } else {
            const errorData = await response.json();
            console.error("Erro ao adicionar entrada:", errorData);
            alert(`Erro ao adicionar: ${errorData.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error("Erro ao adicionar entrada:", error);
        alert(`Erro ao adicionar: ${error.message}`);
    }
});

document.getElementById("form-saida").addEventListener("submit", async (e) => {
    e.preventDefault();
    const parcelamento = parseInt(document.getElementById("saida-parcelamento").value);
    
    const saida = {
        nome: document.getElementById("saida-nome").value,
        valor: parseFloat(document.getElementById("saida-valor").value),
        flags: document.getElementById("saida-flags").value,
        data_vencimento: document.getElementById("saida-data-vencimento").value || null,
        parcelamento: parcelamento
    };
    
    try {
        const response = await fetch(`${API_URL}/saidas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(saida)
        });
        
        if (response.ok) {
            await renderSaidas();
            await renderDashboard();
            e.target.reset();
            document.getElementById("form-saida-container").style.display = "none";
        } else {
            const errorData = await response.json();
            console.error("Erro ao adicionar saída:", errorData);
            alert(`Erro ao adicionar: ${errorData.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error("Erro ao adicionar saída:", error);
        alert(`Erro ao adicionar: ${error.message}`);
    }
});

// Listener para o filtro de saídas
document.getElementById("filter-saidas").addEventListener("change", renderSaidas);

async function init() {
    // Popular o seletor de meses
    await populateMonthSelector();
    
    // Renderizar os componentes principais
    await renderDashboard();
    await renderEntradas();
    await renderSaidas();
}

init();