import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel Financeiro",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÕES PARA MANIPULAR DADOS ---
# Função para carregar os dados de um arquivo CSV
def carregar_dados(nome_arquivo):
    if os.path.exists(nome_arquivo):
        df = pd.read_csv(nome_arquivo)
    else:
        # Se o arquivo não existe, cria um DataFrame vazio com as colunas certas
        colunas = {
            'vendas.csv': ['data', 'descricao', 'valor'],
            'despesas.csv': ['data', 'categoria', 'valor']
        }
        df = pd.DataFrame(columns=colunas.get(nome_arquivo, []))
    
    # Garante que a coluna 'data' seja do tipo datetime
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'])
    
    return df

# Função para salvar os dados em um arquivo CSV
def salvar_dados(df, nome_arquivo):
    df.to_csv(nome_arquivo, index=False)

# Carrega os dados no início da execução
df_vendas = carregar_dados('vendas.csv')
df_despesas = carregar_dados('despesas.csv')

# --- BARRA LATERAL (MENU DE NAVEGAÇÃO) ---
st.sidebar.header("Menu de Navegação")
pagina = st.sidebar.radio(
    "Escolha uma página",
    ("Painel Principal", "Registrar Venda", "Registrar Despesa", "Calcular Comissões")
)

# --- PÁGINA: PAINEL PRINCIPAL ---
if pagina == "Painel Principal":
    st.title("📊 Painel de Controle Financeiro")
    st.markdown("---")

    # Filtro de Mês/Ano
    st.sidebar.header("Filtros")
    anos_disponiveis = sorted(df_vendas['data'].dt.year.unique()) if not df_vendas.empty else [datetime.now().year]
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis, index=len(anos_disponiveis)-1)
    
    # Filtra os dados pelo ano selecionado
    vendas_ano = df_vendas[df_vendas['data'].dt.year == ano_selecionado]
    despesas_ano = df_despesas[df_despesas['data'].dt.year == ano_selecionado]

    # Agrupando dados por mês
    vendas_mensal = vendas_ano.groupby(vendas_ano['data'].dt.to_period('M'))['valor'].sum()
    despesas_mensal = despesas_ano.groupby(despesas_ano['data'].dt.to_period('M'))['valor'].sum()
    
    # Criando um DataFrame para o resumo
    resumo_df = pd.DataFrame({
        'Vendas': vendas_mensal,
        'Despesas': despesas_mensal
    }).fillna(0)
    resumo_df['Lucro Líquido'] = resumo_df['Vendas'] - resumo_df['Despesas']
    resumo_df.index = resumo_df.index.strftime('%Y-%m') # Formata o índice para melhor visualização

    # Resumo Financeiro (Total do Ano)
    total_vendas = resumo_df['Vendas'].sum()
    total_despesas = resumo_df['Despesas'].sum()
    lucro_liquido_total = resumo_df['Lucro Líquido'].sum()

    st.header(f"Resumo Anual: {ano_selecionado}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
    col2.metric("Total de Despesas", f"R$ {total_despesas:,.2f}")
    col3.metric("Lucro Líquido", f"R$ {lucro_liquido_total:,.2f}", delta=f"{lucro_liquido_total:,.2f}")
    
    st.markdown("---")

    # Gráfico Comparativo
    st.header("Comparativo Mensal: Vendas vs. Despesas")
    if not resumo_df.empty:
        fig = px.bar(
            resumo_df,
            x=resumo_df.index,
            y=['Vendas', 'Despesas'],
            barmode='group',
            title=f"Desempenho Financeiro Mensal em {ano_selecionado}",
            labels={'value': 'Valor (R$)', 'variable': 'Tipo', 'x': 'Mês'},
            color_discrete_map={'Vendas': '#2ECC71', 'Despesas': '#E74C3C'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ainda não há dados de vendas ou despesas registrados para o ano selecionado.")

    # Detalhamento Mensal
    st.header("Resumo Mensal Detalhado")
    st.dataframe(resumo_df.style.format("R$ {:,.2f}"))

# --- PÁGINA: REGISTRAR VENDA ---
elif pagina == "Registrar Venda":
    st.title("✍️ Registrar Nova Venda")
    with st.form("form_venda", clear_on_submit=True):
        data_venda = st.date_input("Data da Venda", datetime.now())
        descricao = st.text_input("Descrição da Venda (Ex: Produto A, Serviço B)")
        valor = st.number_input("Valor da Venda (R$)", min_value=0.01, format="%.2f")
        
        submitted = st.form_submit_button("Registrar Venda")
        if submitted:
            # Adiciona a nova venda ao DataFrame
            nova_venda = pd.DataFrame([{'data': data_venda, 'descricao': descricao, 'valor': valor}])
            df_vendas = pd.concat([df_vendas, nova_venda], ignore_index=True)
            salvar_dados(df_vendas, 'vendas.csv')
            st.success(f"Venda '{descricao}' de R$ {valor:,.2f} registrada com sucesso!")

    st.markdown("---")
    st.header("Últimas Vendas Registradas")
    st.dataframe(df_vendas.sort_values(by='data', ascending=False).head(10))

# --- PÁGINA: REGISTRAR DESPESA ---
elif pagina == "Registrar Despesa":
    st.title("💸 Registrar Nova Despesa")
    with st.form("form_despesa", clear_on_submit=True):
        data_despesa = st.date_input("Data da Despesa", datetime.now())
        categorias = ['Fornecedores', 'Aluguel', 'Salários', 'Marketing', 'Impostos', 'Outros']
        categoria = st.selectbox("Categoria da Despesa", categorias)
        valor = st.number_input("Valor da Despesa (R$)", min_value=0.01, format="%.2f")

        submitted = st.form_submit_button("Registrar Despesa")
        if submitted:
            # Adiciona a nova despesa ao DataFrame
            nova_despesa = pd.DataFrame([{'data': data_despesa, 'categoria': categoria, 'valor': valor}])
            df_despesas = pd.concat([df_despesas, nova_despesa], ignore_index=True)
            salvar_dados(df_despesas, 'despesas.csv')
            st.success(f"Despesa na categoria '{categoria}' de R$ {valor:,.2f} registrada com sucesso!")

    st.markdown("---")
    st.header("Últimas Despesas Registradas")
    st.dataframe(df_despesas.sort_values(by='data', ascending=False).head(10))

# --- PÁGINA: CALCULAR COMISSÕES ---
elif pagina == "Calcular Comissões":
    st.title("💰 Cálculo de Comissões de Venda")
    if not df_vendas.empty:
        percentual = st.slider("Selecione o percentual de comissão (%)", 1, 25, 5)
        
        # Cria uma cópia para não alterar o DataFrame original
        df_comissao = df_vendas.copy()
        
        # Calcula a comissão
        df_comissao['comissao_a_pagar'] = df_comissao['valor'] * (percentual / 100)
        
        total_comissoes = df_comissao['comissao_a_pagar'].sum()
        st.metric("Total a Pagar em Comissões", f"R$ {total_comissoes:,.2f}")

        st.markdown("---")
        st.header("Detalhamento das Comissões por Venda")
        st.dataframe(df_comissao[['data', 'descricao', 'valor', 'comissao_a_pagar']].style.format({
            'valor': 'R$ {:,.2f}',
            'comissao_a_pagar': 'R$ {:,.2f}'
        }))
    else:
        st.info("Não há vendas registradas para calcular comissões.")
