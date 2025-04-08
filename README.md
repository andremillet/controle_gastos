# Controle de Gastos Familiares

Uma aplicação web simples para controle financeiro pessoal e familiar, com foco em gerenciamento de entradas, saídas e parcelamentos.

## Funcionalidades

### Dashboard
- Visão geral do saldo atual
- Total de entradas (recebidas e pendentes)
- Total de saídas (pagas e pendentes)
- Sumário de compras parceladas
- Previsão de parcelas a vencer nos próximos 30 dias
- **Filtro por mês** - Visualização de dados por mês específico

### Gerenciamento de Entradas
- Cadastrar fontes de renda e pagamentos a receber
- Acompanhar status (pendente ou recebido)
- Visualizar histórico de entradas
- **Filtro mensal** - Exibição de entradas do mês atual ou visualização completa

### Gerenciamento de Saídas
- Cadastrar despesas e contas a pagar
- Marcação de pagamentos realizados
- Flags para priorização (urgente, feito, etc.)
- **Filtro mensal** - Exibição de saídas do mês atual ou visualização completa
- **Sistema de parcelamento**:
  - Dividir compras em parcelas (2x, 3x, 5x, 6x, 10x, 12x)
  - Acompanhamento de parcelas a vencer
  - Visualização de parcelas pendentes
  - Filtros adicionais para visualizar apenas itens parcelados
  - Alerta visual para vencimentos próximos
  
## Tecnologias

### Backend
- Python 3.13
- FastAPI (framework web)
- SQLite (banco de dados)
- Uvicorn (servidor ASGI)

### Frontend
- HTML5
- CSS3 (design responsivo)
- JavaScript puro (sem frameworks)

## Instalação e Execução

1. Certifique-se de ter Python 3.13 instalado
2. Crie um ambiente virtual: `python -m venv .venv`
3. Ative o ambiente virtual:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Instale as dependências: `pip install -e .`
5. Execute a migração do banco de dados (necessário apenas na primeira vez ou após alterações no esquema):
   ```bash
   python backend/migrate_db.py
   ```
6. Execute o script de inicialização: `./start-app.sh`

## Uso do Sistema

### Controle Mensal
1. Use o seletor de mês no topo da página para alternar entre diferentes meses
2. O dashboard e as listas de entradas/saídas serão atualizados automaticamente para mostrar dados do mês selecionado
3. Para visualizar todos os registros (sem filtro mensal), clique no botão "Ver Todos os Meses"

### Sistema de Parcelamento
1. Ao cadastrar uma nova despesa, selecione o número de parcelas desejado
2. O sistema automaticamente criará todas as parcelas mensais com os vencimentos
3. Use os filtros para visualizar suas parcelas e compras parceladas
4. Cada parcela pode ser gerenciada individualmente (marcar como paga, alterar valor, etc.)
5. Ao excluir uma parcela, você pode optar por excluir apenas essa parcela ou todas as parcelas restantes

## Flags do Sistema

- `urg`: Marca um item como urgente (destacado em vermelho)
- `feito`: Marca um item como pago/concluído (destacado em verde)
- `parc2`, `parc3`, `parc5`, etc.: Indica o número de parcelas (gerado automaticamente)
- `no_rec`: Para despesas não recorrentes
