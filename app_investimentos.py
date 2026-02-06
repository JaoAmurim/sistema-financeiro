#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
� SISTEMA FINANCEIRO COMPLETO - APP WEB INTERATIVO
Controle total da sua vida financeira: investimentos, gastos, fluxo de caixa e relatórios
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import calendar

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="💰 Minha Vida Financeira",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILO CSS CUSTOMIZADO ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1F4E78;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNÇÕES DE DADOS ==========
DATA_FILE = Path("dados_investimentos.json")

def carregar_dados():
    """Carrega dados do arquivo JSON"""
    dados_padrao = {
        "carteira": [],
        "proventos": [],
        "aportes": [],
        "historico_patrimonio": [],
        "entradas": [],  # Novo: salários, rendas extras
        "saidas": [],    # Novo: despesas do dia a dia
        "despesas_fixas": [],  # Novo: contas mensais fixas
        "metas": {
            "patrimonio_anual": 0,
            "renda_passiva_mensal": 0,
            "economia_mensal": 0
        },
        "cdi_anual": 0,
        "perfil": {
            "nome": "",
            "renda_mensal": 0,
            "data_inicio": datetime.now().strftime('%Y-%m-%d')
        }
    }
    
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            dados_carregados = json.load(f)
        
        # Mesclar com dados padrão para garantir que todas as chaves existam
        for chave, valor in dados_padrao.items():
            if chave not in dados_carregados:
                dados_carregados[chave] = valor
            elif isinstance(valor, dict):
                # Para dicionários aninhados (como 'metas' e 'perfil')
                for sub_chave, sub_valor in valor.items():
                    if sub_chave not in dados_carregados[chave]:
                        dados_carregados[chave][sub_chave] = sub_valor
        
        return dados_carregados
    else:
        return dados_padrao

def salvar_dados(dados):
    """Salva dados no arquivo JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def calcular_patrimonio_atual(carteira):
    """Calcula patrimônio total da carteira"""
    total = 0
    for ativo in carteira:
        total += ativo['cotas'] * ativo['cotacao_atual']
    return total

def calcular_rentabilidade_total(carteira):
    """Calcula rentabilidade total da carteira"""
    investido = sum(ativo['cotas'] * ativo['preco_medio'] for ativo in carteira)
    atual = calcular_patrimonio_atual(carteira)
    if investido > 0:
        return ((atual - investido) / investido) * 100
    return 0

def calcular_proventos_mes_atual(proventos):
    """Calcula total de proventos do mês atual"""
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    total = 0
    for prov in proventos:
        data_prov = datetime.strptime(prov['data'], '%Y-%m-%d')
        if data_prov >= inicio_mes:
            total += prov['valor']
    return total

def calcular_entradas_mes(entradas):
    """Calcula total de entradas do mês atual"""
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    total = 0
    for entrada in entradas:
        data_entrada = datetime.strptime(entrada['data'], '%Y-%m-%d')
        if data_entrada >= inicio_mes:
            total += entrada['valor']
    return total

def calcular_saidas_mes(saidas):
    """Calcula total de saídas do mês atual"""
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    total = 0
    for saida in saidas:
        data_saida = datetime.strptime(saida['data'], '%Y-%m-%d')
        if data_saida >= inicio_mes:
            total += saida['valor']
    return total

def calcular_saldo_mes(entradas, saidas):
    """Calcula saldo do mês (entradas - saídas)"""
    return calcular_entradas_mes(entradas) - calcular_saidas_mes(saidas)

def calcular_taxa_poupanca(entradas, saidas, aportes):
    """Calcula taxa de poupança do mês"""
    entrada_total = calcular_entradas_mes(entradas)
    if entrada_total == 0:
        return 0
    aportes_mes = sum(a['valor'] for a in aportes 
                     if datetime.strptime(a['data'], '%Y-%m-%d').month == datetime.now().month)
    return (aportes_mes / entrada_total) * 100

# ========== CARREGAR DADOS ==========
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

dados = st.session_state.dados

# ========== SIDEBAR - MENU ==========
st.sidebar.markdown("# 🚀 Menu Principal")

# Saudação personalizada
nome = dados.get('perfil', {}).get('nome', '')
if nome:
    st.sidebar.markdown(f"### 👋 Olá, **{nome}**!")
else:
    st.sidebar.markdown("### 👋 Bem-vindo!")

st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "📍 Navegação:",
    ["🏠 Início", "💸 Fluxo de Caixa", "🛒 Despesas", "💼 Carteira", "💰 Proventos", "📅 Aportes", "📈 Performance", "📊 Relatórios", "🎯 Metas", "⚙️ Perfil"]
)

st.sidebar.markdown("---")

# Resumo rápido na sidebar
patrimonio_atual = calcular_patrimonio_atual(dados['carteira'])
saldo_mes = calcular_saldo_mes(dados.get('entradas', []), dados.get('saidas', []))

st.sidebar.markdown("### 💰 Resumo Rápido")
st.sidebar.metric("Patrimônio", f"R$ {patrimonio_atual:,.2f}")
st.sidebar.metric("Saldo do Mês", f"R$ {saldo_mes:,.2f}", 
                 delta="positivo" if saldo_mes > 0 else "negativo")

st.sidebar.markdown("---")

# ========== PÁGINA: INÍCIO ==========
if pagina == "🏠 Início":
    st.markdown('<h1 class="main-header">🏠 Visão Geral da Sua Vida Financeira</h1>', unsafe_allow_html=True)
    
    hoje = datetime.now()
    mes_atual = calendar.month_name[hoje.month]
    st.markdown(f"**📅 {mes_atual} de {hoje.year}** • Atualizado em {hoje.strftime('%d/%m/%Y às %H:%M')}")
    
    # Calcular métricas
    patrimonio = calcular_patrimonio_atual(dados['carteira'])
    entradas_mes = calcular_entradas_mes(dados.get('entradas', []))
    saidas_mes = calcular_saidas_mes(dados.get('saidas', []))
    saldo_mes = entradas_mes - saidas_mes
    proventos_mes = calcular_proventos_mes_atual(dados['proventos'])
    taxa_poupanca = calcular_taxa_poupanca(dados.get('entradas', []), dados.get('saidas', []), dados['aportes'])
    
    # Cards principais - 4 colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Patrimônio Total",
            value=f"R$ {patrimonio:,.2f}",
            help="Valor total de todos os seus investimentos"
        )
    
    with col2:
        st.metric(
            label="💸 Saldo do Mês",
            value=f"R$ {saldo_mes:,.2f}",
            delta=f"{(saldo_mes/entradas_mes*100):.1f}% da renda" if entradas_mes > 0 else None,
            help="Entradas - Saídas deste mês"
        )
    
    with col3:
        st.metric(
            label="💵 Proventos",
            value=f"R$ {proventos_mes:,.2f}",
            delta="Renda Passiva",
            help="Dividendos recebidos este mês"
        )
    
    with col4:
        st.metric(
            label="📊 Taxa de Poupança",
            value=f"{taxa_poupanca:.1f}%",
            delta="🎯 Ideal: >20%",
            help="% da renda que você está investindo"
        )
    
    st.markdown("---")
    
    # Seção: Fluxo de Caixa do Mês
    st.subheader("💸 Fluxo de Caixa de Fevereiro")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🟢 Entradas")
        st.markdown(f"### R$ {entradas_mes:,.2f}")
        if dados.get('entradas'):
            categorias_entrada = {}
            for entrada in dados['entradas']:
                if datetime.strptime(entrada['data'], '%Y-%m-%d').month == hoje.month:
                    cat = entrada.get('categoria', 'Outros')
                    categorias_entrada[cat] = categorias_entrada.get(cat, 0) + entrada['valor']
            
            for cat, valor in sorted(categorias_entrada.items(), key=lambda x: x[1], reverse=True)[:3]:
                st.caption(f"• {cat}: R$ {valor:,.2f}")
    
    with col2:
        st.markdown("### 🔴 Saídas")
        st.markdown(f"### R$ {saidas_mes:,.2f}")
        if dados.get('saidas'):
            categorias_saida = {}
            for saida in dados['saidas']:
                if datetime.strptime(saida['data'], '%Y-%m-%d').month == hoje.month:
                    cat = saida.get('categoria', 'Outros')
                    categorias_saida[cat] = categorias_saida.get(cat, 0) + saida['valor']
            
                st.caption(f"• {cat}: R$ {valor:,.2f}")
    
    with col3:
        st.markdown("### 💰 Saldo")
        cor_saldo = "🟢" if saldo_mes > 0 else "🔴"
        st.markdown(f"### {cor_saldo} R$ {saldo_mes:,.2f}")
        if saldo_mes > 0:
            st.success("🎉 Parabéns! Mês positivo!")
        elif saldo_mes < 0:
            st.warning("⚠️ Atenção ao déficit!")
        else:
            st.info("⚖️ Saldo equilibrado")
    
    # Gráfico de entradas vs saídas
    if dados.get('entradas') or dados.get('saidas'):
        st.markdown("---")
        st.subheader("📊 Visão Geral do Mês")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Entradas',
            x=['Fevereiro'],
            y=[entradas_mes],
            marker_color='#2ecc71',
            text=[f'R$ {entradas_mes:,.2f}'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Saídas',
            x=['Fevereiro'],
            y=[saidas_mes],
            marker_color='#e74c3c',
            text=[f'R$ {saidas_mes:,.2f}'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Scatter(
            name='Saldo',
            x=['Fevereiro'],
            y=[saldo_mes],
            mode='markers+text',
            marker=dict(size=20, color='#3498db', symbol='diamond'),
            text=[f'R$ {saldo_mes:,.2f}'],
            textposition='top center'
        ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Mensagens motivacionais
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Suas Conquistas")
        if patrimonio > 0:
            st.success(f"✅ Você já acumulou R$ {patrimonio:,.2f} em investimentos!")
        if proventos_mes > 0:
            st.success(f"✅ Recebeu R$ {proventos_mes:,.2f} de renda passiva este mês!")
        if taxa_poupanca >= 20:
            st.success(f"✅ Taxa de poupança de {taxa_poupanca:.1f}% - Excelente!")
        if saldo_mes > 0:
            st.success(f"✅ Saldo positivo de R$ {saldo_mes:,.2f} no mês!")
        
        if patrimonio == 0 and proventos_mes == 0:
            st.info("💡 Comece adicionando seus ativos em 'Carteira'!")
    
    with col2:
        st.markdown("### 💡 Dicas Personalizadas")
        if taxa_poupanca < 20:
            st.warning(f"💪 Sua taxa de poupança está em {taxa_poupanca:.1f}%. Tente aumentar para 20%!")
        if saldo_mes < 0:
            st.warning("💰 Revise seus gastos em 'Despesas' para equilibrar as contas.")
        if len(dados['carteira']) < 3:
            st.info("📊 Diversifique! Considere ter pelo menos 3 ativos diferentes.")
        if not dados.get('metas', {}).get('patrimonio_anual'):
            st.info("🎯 Defina suas metas em 'Metas' para acompanhar seu progresso!")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Ações Rápidas")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💸 Adicionar Entrada", use_container_width=True):
            pass
    with col2:
        if st.button("💼 Ver Carteira", use_container_width=True):
            pass
    with col3:
        if st.button("📊 Ver Relatórios", use_container_width=True):
            pass
    with col4:
        if st.button("🎯 Minhas Metas", use_container_width=True):
            pass

# ========== PÁGINA: FLUXO DE CAIXA ==========
elif pagina == "💸 Fluxo de Caixa":
    st.markdown('<h1 class="main-header">💸 Controle de Fluxo de Caixa</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🟢 Entradas", "🔴 Saídas"])
    
    # ===== TAB ENTRADAS =====
    with tab1:
        st.subheader("💰 Registrar Nova Entrada")
        
        with st.form("form_entrada"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                data_entrada = st.date_input("📅 Data", value=datetime.now())
                categoria_entrada = st.selectbox("📂 Categoria", 
                    ["Salário", "Freelance", "Vendas", "Presente", "Reembolso", "Outros"])
            
            with col2:
                descricao_entrada = st.text_input("📝 Descrição", placeholder="Ex: Salário de Fevereiro")
                valor_entrada = st.number_input("💵 Valor (R$)", min_value=0.01, value=100.00, format="%.2f")
            
            with col3:
                recorrente = st.checkbox("🔄 Entrada recorrente mensal")
                st.write("")  # espaçamento
            
            submitted = st.form_submit_button("✅ Registrar Entrada", use_container_width=True)
            
            if submitted:
                nova_entrada = {
                    "data": data_entrada.strftime('%Y-%m-%d'),
                    "categoria": categoria_entrada,
                    "descricao": descricao_entrada,
                    "valor": valor_entrada,
                    "recorrente": recorrente
                }
                dados['entradas'].append(nova_entrada)
                salvar_dados(dados)
                st.success(f"✅ Entrada de R$ {valor_entrada:,.2f} registrada!")
                st.rerun()
        
        # Histórico de entradas
        st.markdown("---")
        st.subheader("📋 Histórico de Entradas")
        
        if dados.get('entradas'):
            df_entradas = pd.DataFrame(dados['entradas'])
            df_entradas['data'] = pd.to_datetime(df_entradas['data'])
            df_entradas = df_entradas.sort_values('data', ascending=False)
            
            # Filtro por mês
            col1, col2 = st.columns([3, 1])
            with col1:
                filtro_mes = st.selectbox("Filtrar por mês:", ["Todos", "Este mês", "Mês passado"])
            
            if filtro_mes == "Este mês":
                df_entradas = df_entradas[df_entradas['data'].dt.month == datetime.now().month]
            elif filtro_mes == "Mês passado":
                df_entradas = df_entradas[df_entradas['data'].dt.month == datetime.now().month - 1]
            
            df_display = df_entradas.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display = df_display[['data', 'categoria', 'descricao', 'valor']]
            df_display.columns = ['Data', 'Categoria', 'Descrição', 'Valor']
            
            st.dataframe(
                df_display.style.format({'Valor': 'R$ {:.2f}'}),
                use_container_width=True,
                hide_index=True
            )
            
            total_exibido = df_entradas['valor'].sum()
            st.metric("💰 Total das entradas exibidas", f"R$ {total_exibido:,.2f}")
        else:
            st.info("📌 Nenhuma entrada registrada ainda!")
    
    # ===== TAB SAÍDAS =====
    with tab2:
        st.subheader("💳 Registrar Nova Saída")
        
        with st.form("form_saida"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                data_saida = st.date_input("📅 Data", value=datetime.now())
                categoria_saida = st.selectbox("📂 Categoria", 
                    ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", 
                     "Educação", "Vestuário", "Contas", "Outros"])
            
            with col2:
                descricao_saida = st.text_input("📝 Descrição", placeholder="Ex: Almoço no restaurante")
                valor_saida = st.number_input("💵 Valor (R$)", min_value=0.01, value=10.00, format="%.2f")
            
            with col3:
                recorrente_saida = st.checkbox("🔄 Despesa recorrente mensal")
                st.write("")  # espaçamento
            
            submitted = st.form_submit_button("✅ Registrar Saída", use_container_width=True)
            
            if submitted:
                nova_saida = {
                    "data": data_saida.strftime('%Y-%m-%d'),
                    "categoria": categoria_saida,
                    "descricao": descricao_saida,
                    "valor": valor_saida,
                    "recorrente": recorrente_saida
                }
                dados['saidas'].append(nova_saida)
                salvar_dados(dados)
                st.success(f"✅ Saída de R$ {valor_saida:,.2f} registrada!")
                st.rerun()
        
        # Histórico de saídas
        st.markdown("---")
        st.subheader("📋 Histórico de Saídas")
        
        if dados.get('saidas'):
            df_saidas = pd.DataFrame(dados['saidas'])
            df_saidas['data'] = pd.to_datetime(df_saidas['data'])
            df_saidas = df_saidas.sort_values('data', ascending=False)
            
            # Filtro por mês
            col1, col2 = st.columns([3, 1])
            with col1:
                filtro_mes = st.selectbox("Filtrar por mês:", ["Todos", "Este mês", "Mês passado"], key="filtro_saida")
            
            if filtro_mes == "Este mês":
                df_saidas = df_saidas[df_saidas['data'].dt.month == datetime.now().month]
            elif filtro_mes == "Mês passado":
                df_saidas = df_saidas[df_saidas['data'].dt.month == datetime.now().month - 1]
            
            df_display = df_saidas.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display = df_display[['data', 'categoria', 'descricao', 'valor']]
            df_display.columns = ['Data', 'Categoria', 'Descrição', 'Valor']
            
            st.dataframe(
                df_display.style.format({'Valor': 'R$ {:.2f}'}),
                use_container_width=True,
                hide_index=True
            )
            
            total_exibido = df_saidas['valor'].sum()
            st.metric("💳 Total das saídas exibidas", f"R$ {total_exibido:,.2f}")
            
            # Gráfico por categoria
            if len(df_saidas) > 0:
                st.markdown("---")
                st.subheader("📊 Gastos por Categoria")
                
                gastos_cat = df_saidas.groupby('categoria')['valor'].sum().sort_values(ascending=False)
                
                fig = px.pie(
                    values=gastos_cat.values,
                    names=gastos_cat.index,
                    title='Distribuição dos Gastos',
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📌 Nenhuma saída registrada ainda!")

# ========== PÁGINA: DESPESAS ==========
elif pagina == "🛒 Despesas":
    st.markdown('<h1 class="main-header">🛒 Controle de Despesas Pessoais</h1>', unsafe_allow_html=True)
    
    st.info("💡 **Dica:** Use esta aba para acompanhar gastos específicos do dia a dia e despesas fixas mensais.")
    
    # Resumo rápido
    despesas_mes = calcular_saidas_mes(dados.get('saidas', []))
    despesas_fixas_total = sum(d.get('valor', 0) for d in dados.get('despesas_fixas', []))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💳 Gastos Variáveis", f"R$ {despesas_mes:,.2f}")
    with col2:
        st.metric("📋 Despesas Fixas", f"R$ {despesas_fixas_total:,.2f}")
    with col3:
        st.metric("💰 Total Mensal", f"R$ {despesas_mes + despesas_fixas_total:,.2f}")
    
    st.markdown("---")
    
    # Despesas Fixas Mensais
    st.subheader("📋 Despesas Fixas Mensais")
    
    with st.expander("➕ Adicionar Despesa Fixa", expanded=False):
        with st.form("form_despesa_fixa"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome_despesa = st.text_input("📝 Nome da Despesa", placeholder="Ex: Aluguel, Internet, Academia")
                categoria_despesa = st.selectbox("📂 Categoria", 
                    ["Moradia", "Transporte", "Saúde", "Educação", "Seguros", "Assinaturas", "Outros"])
            
            with col2:
                valor_despesa = st.number_input("💵 Valor Mensal (R$)", min_value=0.01, value=100.00, format="%.2f")
                dia_vencimento = st.number_input("📅 Dia do Vencimento", min_value=1, max_value=31, value=10)
            
            submitted = st.form_submit_button("✅ Adicionar Despesa Fixa")
            
            if submitted:
                nova_despesa_fixa = {
                    "nome": nome_despesa,
                    "categoria": categoria_despesa,
                    "valor": valor_despesa,
                    "dia_vencimento": dia_vencimento,
                    "ativa": True
                }
                if 'despesas_fixas' not in dados:
                    dados['despesas_fixas'] = []
                dados['despesas_fixas'].append(nova_despesa_fixa)
                salvar_dados(dados)
                st.success(f"✅ Despesa fixa '{nome_despesa}' adicionada!")
                st.rerun()
    
    # Listar despesas fixas
    if dados.get('despesas_fixas'):
        st.markdown("### Lista de Despesas Fixas")
        for idx, despesa in enumerate(dados['despesas_fixas']):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{despesa['nome']}**")
                st.caption(f"{despesa['categoria']} • Vence dia {despesa['dia_vencimento']}")
            
            with col2:
                st.metric("Valor", f"R$ {despesa['valor']:,.2f}")
            
            with col3:
                st.metric("Anual", f"R$ {despesa['valor']*12:,.2f}")
            
            with col4:
                if st.button("🗑️", key=f"del_desp_{idx}"):
                    dados['despesas_fixas'].pop(idx)
                    salvar_dados(dados)
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("📌 Nenhuma despesa fixa cadastrada ainda!")
    
    # Análise de gastos
    if dados.get('saidas'):
        st.markdown("---")
        st.subheader("📊 Análise de Gastos dos Últimos 30 Dias")
        
        df_saidas = pd.DataFrame(dados['saidas'])
        df_saidas['data'] = pd.to_datetime(df_saidas['data'])
        
        # Filtrar últimos 30 dias
        dias_30 = datetime.now() - timedelta(days=30)
        df_recente = df_saidas[df_saidas['data'] >= dias_30]
        
        if len(df_recente) > 0:
            # Gastos por categoria
            gastos_cat = df_recente.groupby('categoria')['valor'].sum().sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🏆 Top Categorias")
                for i, (cat, valor) in enumerate(gastos_cat.head(5).items(), 1):
                    perc = (valor / gastos_cat.sum() * 100)
                    st.write(f"{i}. **{cat}**: R$ {valor:,.2f} ({perc:.1f}%)")
            
            with col2:
                st.markdown("#### 💰 Maior Gasto")
                maior_gasto = df_recente.loc[df_recente['valor'].idxmax()]
                st.error(f"**R$ {maior_gasto['valor']:,.2f}**")
                st.caption(f"{maior_gasto['descricao']} • {maior_gasto['categoria']}")
                st.caption(f"Data: {maior_gasto['data'].strftime('%d/%m/%Y')}")

# ========== PÁGINA: DASHBOARD ==========
elif pagina == "📊 Dashboard":
    st.markdown('<h1 class="main-header">📊 Dashboard de Investimentos</h1>', unsafe_allow_html=True)
    st.markdown(f"**📅 Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Calcular métricas principais
    patrimonio = calcular_patrimonio_atual(dados['carteira'])
    rentabilidade = calcular_rentabilidade_total(dados['carteira'])
    proventos_mes = calcular_proventos_mes_atual(dados['proventos'])
    
    # Cards de métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Patrimônio Atual",
            value=f"R$ {patrimonio:,.2f}",
            delta=f"{rentabilidade:+.2f}%" if rentabilidade != 0 else None
        )
    
    with col2:
        cdi = dados.get('cdi_anual', 0)
        vs_cdi = rentabilidade - cdi if cdi > 0 else 0
        st.metric(
            label="📈 Rentabilidade 2026",
            value=f"{rentabilidade:.2f}%",
            delta=f"{vs_cdi:+.2f}% vs CDI" if cdi > 0 else None
        )
    
    with col3:
        st.metric(
            label="💵 Proventos este Mês",
            value=f"R$ {proventos_mes:,.2f}",
            delta="🎯 Renda Passiva"
        )
    
    st.markdown("---")
    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Composição da Carteira")
        if dados['carteira']:
            df_carteira = pd.DataFrame(dados['carteira'])
            df_carteira['valor_atual'] = df_carteira['cotas'] * df_carteira['cotacao_atual']
            
            fig = px.pie(
                df_carteira,
                values='valor_atual',
                names='codigo',
                title='Distribuição por Ativo',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📌 Adicione ativos na aba 'Minha Carteira' para visualizar a composição.")
    
    with col2:
        st.subheader("📈 Evolução Patrimonial")
        if dados['historico_patrimonio']:
            df_hist = pd.DataFrame(dados['historico_patrimonio'])
            df_hist['data'] = pd.to_datetime(df_hist['data'])
            
            fig = px.line(
                df_hist,
                x='data',
                y='valor',
                title='Histórico do Patrimônio',
                markers=True
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title="Patrimônio (R$)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📌 O histórico será construído conforme você registrar a evolução na aba 'Performance'.")
    
    # Tabela resumo da carteira
    st.markdown("---")
    st.subheader("💼 Resumo dos Ativos")
    if dados['carteira']:
        df_resumo = pd.DataFrame(dados['carteira'])
        df_resumo['Total Investido'] = df_resumo['cotas'] * df_resumo['preco_medio']
        df_resumo['Valor Atual'] = df_resumo['cotas'] * df_resumo['cotacao_atual']
        df_resumo['Rentabilidade'] = ((df_resumo['Valor Atual'] - df_resumo['Total Investido']) / df_resumo['Total Investido'] * 100).round(2)
        df_resumo['Rentabilidade'] = df_resumo['Rentabilidade'].apply(lambda x: f"{x:+.2f}%")
        
        df_display = df_resumo[['codigo', 'tipo', 'cotas', 'preco_medio', 'cotacao_atual', 'Total Investido', 'Valor Atual', 'Rentabilidade']]
        df_display.columns = ['Código', 'Tipo', 'Cotas', 'Preço Médio', 'Cotação Atual', 'Total Investido', 'Valor Atual', 'Rent. %']
        
        st.dataframe(
            df_display.style.format({
                'Preço Médio': 'R$ {:.2f}',
                'Cotação Atual': 'R$ {:.2f}',
                'Total Investido': 'R$ {:.2f}',
                'Valor Atual': 'R$ {:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("⚠️ Nenhum ativo cadastrado ainda. Comece adicionando na aba 'Minha Carteira'!")

# ========== PÁGINA: CARTEIRA ==========
elif pagina == "💼 Carteira":
    st.markdown('<h1 class="main-header">💼 Minha Carteira de Investimentos</h1>', unsafe_allow_html=True)
    
    # Formulário para adicionar novo ativo
    with st.expander("➕ Adicionar Novo Ativo", expanded=False):
        with st.form("form_novo_ativo"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo = st.text_input("🏢 Código do Ativo", placeholder="Ex: MXRF11, ITSA3")
                tipo = st.selectbox("📂 Tipo", ["FII", "Ação", "Renda Fixa"])
                cotas = st.number_input("🔢 Quantidade de Cotas", min_value=1, value=1)
            
            with col2:
                preco_medio = st.number_input("💵 Preço Médio de Compra (R$)", min_value=0.01, value=10.00, format="%.2f")
                cotacao_atual = st.number_input("📈 Cotação Atual (R$)", min_value=0.01, value=10.00, format="%.2f")
            
            submitted = st.form_submit_button("✅ Adicionar à Carteira")
            
            if submitted:
                if codigo.strip():
                    novo_ativo = {
                        "codigo": codigo.upper().strip(),
                        "tipo": tipo,
                        "cotas": cotas,
                        "preco_medio": preco_medio,
                        "cotacao_atual": cotacao_atual,
                        "data_inclusao": datetime.now().strftime('%Y-%m-%d')
                    }
                    dados['carteira'].append(novo_ativo)
                    salvar_dados(dados)
                    st.success(f"✅ {codigo.upper()} adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Por favor, preencha o código do ativo.")
    
    # Exibir carteira atual
    st.markdown("---")
    st.subheader("📋 Ativos na Carteira")
    
    if dados['carteira']:
        for idx, ativo in enumerate(dados['carteira']):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            valor_investido = ativo['cotas'] * ativo['preco_medio']
            valor_atual = ativo['cotas'] * ativo['cotacao_atual']
            rentabilidade = ((valor_atual - valor_investido) / valor_investido * 100) if valor_investido > 0 else 0
            
            with col1:
                st.markdown(f"### {ativo['codigo']}")
                st.caption(f"{ativo['tipo']} • {ativo['cotas']} cotas")
            
            with col2:
                st.metric("Investido", f"R$ {valor_investido:,.2f}")
            
            with col3:
                st.metric("Atual", f"R$ {valor_atual:,.2f}", f"{rentabilidade:+.2f}%")
            
            with col4:
                if st.button("🗑️", key=f"del_{idx}"):
                    dados['carteira'].pop(idx)
                    salvar_dados(dados)
                    st.rerun()
            
            # Editar cotação
            with st.expander(f"✏️ Atualizar cotação de {ativo['codigo']}", expanded=False):
                nova_cotacao = st.number_input(
                    "Nova cotação (R$)",
                    min_value=0.01,
                    value=ativo['cotacao_atual'],
                    format="%.2f",
                    key=f"cotacao_{idx}"
                )
                if st.button("💾 Salvar Cotação", key=f"save_{idx}"):
                    dados['carteira'][idx]['cotacao_atual'] = nova_cotacao
                    salvar_dados(dados)
                    st.success("✅ Cotação atualizada!")
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("📌 Nenhum ativo cadastrado. Use o formulário acima para adicionar!")

# ========== PÁGINA: PROVENTOS ==========
elif pagina == "💰 Proventos":
    st.markdown('<h1 class="main-header">💰 Controle de Proventos</h1>', unsafe_allow_html=True)
    
    # Formulário para adicionar provento
    with st.expander("➕ Registrar Novo Provento", expanded=False):
        with st.form("form_provento"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_prov = st.date_input("📅 Data do Recebimento", value=datetime.now())
                ativo = st.text_input("🏢 Código do Ativo", placeholder="Ex: MXRF11")
                tipo_prov = st.selectbox("📂 Tipo", ["Dividendo", "JCP", "Rendimento", "Juros"])
            
            with col2:
                valor = st.number_input("💵 Valor Recebido (R$)", min_value=0.01, value=1.00, format="%.2f")
            
            submitted = st.form_submit_button("✅ Registrar Provento")
            
            if submitted:
                if ativo.strip():
                    novo_prov = {
                        "data": data_prov.strftime('%Y-%m-%d'),
                        "ativo": ativo.upper().strip(),
                        "tipo": tipo_prov,
                        "valor": valor
                    }
                    dados['proventos'].append(novo_prov)
                    salvar_dados(dados)
                    st.success(f"✅ Provento de {ativo.upper()} registrado!")
                    st.rerun()
                else:
                    st.error("❌ Por favor, preencha o código do ativo.")
    
    # Resumo de proventos
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    total_mes = calcular_proventos_mes_atual(dados['proventos'])
    total_ano = sum(p['valor'] for p in dados['proventos'])
    media_mensal = total_ano / datetime.now().month if datetime.now().month > 0 else 0
    
    with col1:
        st.metric("💵 Recebido este Mês", f"R$ {total_mes:,.2f}")
    
    with col2:
        st.metric("📊 Média Mensal", f"R$ {media_mensal:,.2f}")
    
    with col3:
        st.metric("🎯 Projeção Anual", f"R$ {media_mensal * 12:,.2f}")
    
    # Histórico de proventos
    st.markdown("---")
    st.subheader("📋 Histórico de Proventos")
    
    if dados['proventos']:
        df_prov = pd.DataFrame(dados['proventos'])
        df_prov['data'] = pd.to_datetime(df_prov['data'])
        df_prov = df_prov.sort_values('data', ascending=False)
        
        # Adicionar coluna de índice para remoção
        for idx, provento in enumerate(df_prov.to_dict('records')):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            
            with col1:
                st.write(f"**{provento['data'].strftime('%d/%m/%Y')}**")
            with col2:
                st.write(provento['ativo'])
            with col3:
                st.write(provento['tipo'])
            with col4:
                st.write(f"R$ {provento['valor']:.2f}")
            with col5:
                if st.button("🗑️", key=f"del_prov_{idx}", help="Remover provento"):
                    # Encontrar o índice original no dados['proventos']
                    original_idx = None
                    for i, p in enumerate(dados['proventos']):
                        if (p['data'] == provento['data'].strftime('%Y-%m-%d') and 
                            p['ativo'] == provento['ativo'] and 
                            p['tipo'] == provento['tipo'] and 
                            p['valor'] == provento['valor']):
                            original_idx = i
                            break
                    
                    if original_idx is not None:
                        dados['proventos'].pop(original_idx)
                        salvar_dados(dados)
                        st.success(f"✅ Provento de {provento['ativo']} removido!")
                        st.rerun()
            
            st.markdown("---")
        
        # Gráfico de proventos por mês
        st.markdown("---")
        st.subheader("📊 Proventos por Mês")
        
        df_prov['mes'] = df_prov['data'].dt.to_period('M')
        proventos_mes = df_prov.groupby('mes')['valor'].sum().reset_index()
        proventos_mes['mes'] = proventos_mes['mes'].astype(str)
        
        fig = px.bar(
            proventos_mes,
            x='mes',
            y='valor',
            title='Evolução Mensal de Proventos',
            labels={'mes': 'Mês', 'valor': 'Valor (R$)'},
            color='valor',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📌 Nenhum provento registrado ainda. Use o formulário acima!")

# ========== PÁGINA: APORTES ==========
elif pagina == "📅 Aportes":
    st.markdown('<h1 class="main-header">📅 Planejamento de Aportes</h1>', unsafe_allow_html=True)
    
    # Formulário para registrar aporte
    with st.expander("➕ Registrar Novo Aporte", expanded=False):
        with st.form("form_aporte"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_aporte = st.date_input("📅 Data do Aporte", value=datetime.now())
                ativo = st.text_input("🏢 Código do Ativo", placeholder="Ex: MXRF11")
            
            with col2:
                cotas_aporte = st.number_input("🔢 Quantidade de Cotas", min_value=1, value=1)
                valor_aporte = st.number_input("💵 Valor Total (R$)", min_value=0.01, value=100.00, format="%.2f")
            
            submitted = st.form_submit_button("✅ Registrar Aporte")
            
            if submitted:
                if ativo.strip():
                    novo_aporte = {
                        "data": data_aporte.strftime('%Y-%m-%d'),
                        "ativo": ativo.upper().strip(),
                        "cotas": cotas_aporte,
                        "valor": valor_aporte
                    }
                    dados['aportes'].append(novo_aporte)
                    salvar_dados(dados)
                    st.success(f"✅ Aporte em {ativo.upper()} registrado!")
                    st.rerun()
                else:
                    st.error("❌ Por favor, preencha o código do ativo.")
    
    # Resumo de aportes
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    total_mes = sum(a['valor'] for a in dados['aportes'] 
                   if datetime.strptime(a['data'], '%Y-%m-%d').month == datetime.now().month)
    total_ano = sum(a['valor'] for a in dados['aportes'])
    
    with col1:
        st.metric("💵 Aportado este Mês", f"R$ {total_mes:,.2f}")
    
    with col2:
        st.metric("📊 Total em 2026", f"R$ {total_ano:,.2f}")
    
    # Histórico
    st.markdown("---")
    st.subheader("📋 Histórico de Aportes")
    
    if dados['aportes']:
        df_aportes = pd.DataFrame(dados['aportes'])
        df_aportes['data'] = pd.to_datetime(df_aportes['data'])
        df_aportes = df_aportes.sort_values('data', ascending=False)
        
        df_display = df_aportes.copy()
        df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
        df_display.columns = ['Data', 'Ativo', 'Cotas', 'Valor']
        
        st.dataframe(
            df_display.style.format({'Valor': 'R$ {:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📌 Nenhum aporte registrado ainda!")

# ========== PÁGINA: RELATÓRIOS ==========
elif pagina == "📊 Relatórios":
    st.markdown('<h1 class="main-header">📊 Relatórios e Análises Detalhadas</h1>', unsafe_allow_html=True)
    
    st.info("💡 **Insights completos sobre sua saúde financeira e projeções futuras**")
    
    # Calcular todas as métricas
    patrimonio = calcular_patrimonio_atual(dados['carteira'])
    rentabilidade = calcular_rentabilidade_total(dados['carteira'])
    entradas_mes = calcular_entradas_mes(dados.get('entradas', []))
    saidas_mes = calcular_saidas_mes(dados.get('saidas', []))
    proventos_mes = calcular_proventos_mes_atual(dados['proventos'])
    taxa_poupanca = calcular_taxa_poupanca(dados.get('entradas', []), dados.get('saidas', []), dados['aportes'])
    
    # Tabs de relatórios
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Investimentos", "💰 Finanças Pessoais", "🔮 Projeções", "📊 Comparativos"])
    
    # ===== TAB INVESTIMENTOS =====
    with tab1:
        st.subheader("📊 Análise da Carteira")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Patrimônio", f"R$ {patrimonio:,.2f}")
        with col2:
            st.metric("Rentabilidade", f"{rentabilidade:.2f}%")
        with col3:
            total_investido = sum(a['cotas']*a['preco_medio'] for a in dados['carteira'])
            st.metric("Total Investido", f"R$ {total_investido:,.2f}")
        with col4:
            lucro = patrimonio - total_investido
            st.metric("Lucro/Prejuízo", f"R$ {lucro:,.2f}", delta=f"{rentabilidade:+.2f}%")
        
        if dados['carteira']:
            st.markdown("---")
            st.markdown("#### 🏆 Performance por Ativo")
            
            df_cart = pd.DataFrame(dados['carteira'])
            df_cart['investido'] = df_cart['cotas'] * df_cart['preco_medio']
            df_cart['atual'] = df_cart['cotas'] * df_cart['cotacao_atual']
            df_cart['lucro'] = df_cart['atual'] - df_cart['investido']
            df_cart['rent_%'] = (df_cart['lucro'] / df_cart['investido'] * 100).round(2)
            
            # Ordenar por rentabilidade
            df_cart = df_cart.sort_values('rent_%', ascending=False)
            
            for _, ativo in df_cart.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                
                with col1:
                    emoji = "🟢" if ativo['rent_%'] > 0 else "🔴" if ativo['rent_%'] < 0 else "⚪"
                    st.markdown(f"{emoji} **{ativo['codigo']}** • {ativo['tipo']}")
                
                with col2:
                    st.caption(f"Investido: R$ {ativo['investido']:,.2f}")
                
                with col3:
                    st.caption(f"Atual: R$ {ativo['atual']:,.2f}")
                
                with col4:
                    cor = "green" if ativo['rent_%'] > 0 else "red" if ativo['rent_%'] < 0 else "gray"
                    st.markdown(f":{cor}[{ativo['rent_%']:+.2f}%]")
                
                # Barra de progresso
                progress = min(max((ativo['rent_%'] + 20) / 40, 0), 1)  # Normalizar para 0-1
                st.progress(progress)
                st.markdown("---")
            
            # Gráfico de composição
            st.markdown("#### 📊 Composição da Carteira")
            fig = px.pie(
                df_cart,
                values='atual',
                names='codigo',
                title='Distribuição do Patrimônio',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Adicione ativos na aba 'Carteira' para ver análises detalhadas!")
    
    # ===== TAB FINANÇAS PESSOAIS =====
    with tab2:
        st.subheader("💰 Análise Financeira Pessoal")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Entradas", f"R$ {entradas_mes:,.2f}")
        with col2:
            st.metric("Saídas", f"R$ {saidas_mes:,.2f}")
        with col3:
            saldo = entradas_mes - saidas_mes
            st.metric("Saldo", f"R$ {saldo:,.2f}")
        with col4:
            st.metric("Taxa Poupança", f"{taxa_poupanca:.1f}%")
        
        st.markdown("---")
        
        # Saúde Financeira
        st.markdown("#### 🏥 Indicadores de Saúde Financeira")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Taxa de Poupança**")
            if taxa_poupanca >= 30:
                st.success(f"✅ Excelente! {taxa_poupanca:.1f}% (Ideal: >30%)")
            elif taxa_poupanca >= 20:
                st.info(f"👍 Bom! {taxa_poupanca:.1f}% (Ideal: >30%)")
            elif taxa_poupanca >= 10:
                st.warning(f"⚠️ Pode melhorar! {taxa_poupanca:.1f}% (Ideal: >30%)")
            else:
                st.error(f"❌ Atenção! {taxa_poupanca:.1f}% (Ideal: >30%)")
            
            st.markdown("**💰 Índice de Liquidez**")
            liquidez = (patrimonio / saidas_mes) if saidas_mes > 0 else 0
            if liquidez >= 6:
                st.success(f"✅ Excelente! {liquidez:.1f} meses de reserva")
            elif liquidez >= 3:
                st.info(f"👍 Bom! {liquidez:.1f} meses de reserva")
            else:
                st.warning(f"⚠️ Aumente sua reserva! {liquidez:.1f} meses")
        
        with col2:
            st.markdown("**📈 Crescimento Patrimonial**")
            if len(dados['historico_patrimonio']) >= 2:
                hist = sorted(dados['historico_patrimonio'], key=lambda x: x['data'])
                crescimento_mensal = ((hist[-1]['valor'] - hist[0]['valor']) / hist[0]['valor'] * 100)
                if crescimento_mensal > 5:
                    st.success(f"✅ Ótimo ritmo! {crescimento_mensal:+.1f}%")
                elif crescimento_mensal > 0:
                    st.info(f"👍 Crescendo! {crescimento_mensal:+.1f}%")
                else:
                    st.warning(f"⚠️ Patrimônio estagnado ou caindo")
            else:
                st.info("📌 Registre seu patrimônio em 'Performance' para acompanhar")
            
            st.markdown("**💸 Renda Passiva**")
            percentual_renda_passiva = (proventos_mes / entradas_mes * 100) if entradas_mes > 0 else 0
            if percentual_renda_passiva >= 10:
                st.success(f"✅ Excelente! {percentual_renda_passiva:.1f}% da renda")
            elif percentual_renda_passiva >= 5:
                st.info(f"👍 Bom início! {percentual_renda_passiva:.1f}% da renda")
            elif percentual_renda_passiva > 0:
                st.warning(f"📈 Continue investindo! {percentual_renda_passiva:.1f}%")
            else:
                st.error("❌ Invista em ativos que geram renda!")
        
        # Gráfico de gastos
        if dados.get('saidas'):
            st.markdown("---")
            st.markdown("#### 📊 Onde Seu Dinheiro Está Indo?")
            
            df_saidas = pd.DataFrame(dados['saidas'])
            df_saidas['data'] = pd.to_datetime(df_saidas['data'])
            df_mes = df_saidas[df_saidas['data'].dt.month == datetime.now().month]
            
            if len(df_mes) > 0:
                gastos_cat = df_mes.groupby('categoria')['valor'].sum().sort_values(ascending=True)
                
                fig = px.bar(
                    x=gastos_cat.values,
                    y=gastos_cat.index,
                    orientation='h',
                    title='Gastos por Categoria este Mês',
                    labels={'x': 'Valor (R$)', 'y': 'Categoria'},
                    color=gastos_cat.values,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # ===== TAB PROJEÇÕES =====
    with tab3:
        st.subheader("🔮 Projeções Futuras")
        
        st.info("💡 **Baseado no seu histórico e ritmo atual de investimentos**")
        
        # Parâmetros para projeção
        col1, col2 = st.columns(2)
        
        with col1:
            aporte_mensal = st.number_input(
                "💰 Aporte mensal estimado (R$)",
                min_value=0.0,
                value=float(sum(a['valor'] for a in dados['aportes'][-3:]) / 3 if len(dados['aportes']) >= 3 else 100),
                format="%.2f"
            )
        
        with col2:
            rentabilidade_anual = st.slider(
                "📈 Rentabilidade anual esperada (%)",
                min_value=0.0,
                max_value=30.0,
                value=12.0,
                step=0.5
            )
        
        st.markdown("---")
        
        # Calcular projeções
        patrimonio_inicial = patrimonio
        meses = list(range(1, 37))  # 3 anos
        patrimonio_projetado = []
        
        for mes in meses:
            patrimonio_inicial = patrimonio_inicial * (1 + rentabilidade_anual/100/12) + aporte_mensal
            patrimonio_projetado.append(patrimonio_inicial)
        
        # Exibir projeções chave
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🎯 Em 1 Ano",
                f"R$ {patrimonio_projetado[11]:,.2f}",
                delta=f"+R$ {patrimonio_projetado[11]-patrimonio:,.2f}"
            )
        
        with col2:
            st.metric(
                "🎯 Em 2 Anos",
                f"R$ {patrimonio_projetado[23]:,.2f}",
                delta=f"+R$ {patrimonio_projetado[23]-patrimonio:,.2f}"
            )
        
        with col3:
            st.metric(
                "🎯 Em 3 Anos",
                f"R$ {patrimonio_projetado[35]:,.2f}",
                delta=f"+R$ {patrimonio_projetado[35]-patrimonio:,.2f}"
            )
        
        # Gráfico de projeção
        st.markdown("---")
        st.markdown("#### 📈 Evolução Projetada do Patrimônio")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=meses,
            y=patrimonio_projetado,
            mode='lines+markers',
            name='Projeção',
            line=dict(color='#3498db', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)'
        ))
        
        # Linha atual
        fig.add_hline(
            y=patrimonio,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Atual: R$ {patrimonio:,.2f}"
        )
        
        fig.update_layout(
            xaxis_title="Meses no Futuro",
            yaxis_title="Patrimônio (R$)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Projeção de renda passiva
        st.markdown("---")
        st.markdown("#### 💰 Projeção de Renda Passiva")
        
        dy_medio = 0.08  # 8% ao ano (ajustável)
        renda_passiva_projetada = [(p * dy_medio / 12) for p in patrimonio_projetado]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "💵 Renda Passiva em 1 Ano",
                f"R$ {renda_passiva_projetada[11]:,.2f}/mês"
            )
            st.metric(
                "💵 Renda Passiva em 3 Anos",
                f"R$ {renda_passiva_projetada[35]:,.2f}/mês"
            )
        
        with col2:
            independencia = entradas_mes  # Valor necessário para independência
            meses_para_independencia = None
            
            for i, renda in enumerate(renda_passiva_projetada):
                if renda >= independencia:
                    meses_para_independencia = i + 1
                    break
            
            if meses_para_independencia:
                anos = meses_para_independencia // 12
                meses_rest = meses_para_independencia % 12
                st.success(f"🎯 **Independência Financeira em:**")
                st.markdown(f"### {anos} anos e {meses_rest} meses")
            else:
                st.warning("📈 Aumente aportes para alcançar independência em 3 anos!")
    
    # ===== TAB COMPARATIVOS =====
    with tab4:
        st.subheader("📊 Comparação com Benchmarks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cdi = dados.get('cdi_anual', 0)
            st.metric("CDI Acumulado 2026", f"{cdi:.2f}%")
            
            if rentabilidade > cdi:
                st.success(f"✅ Você está **{rentabilidade - cdi:.2f}%** acima do CDI!")
            elif rentabilidade < cdi:
                st.warning(f"⚠️ Você está **{cdi - rentabilidade:.2f}%** abaixo do CDI")
            else:
                st.info("⚖️ Você está empatado com o CDI")
        
        with col2:
            percentual_cdi = (rentabilidade / cdi * 100) if cdi > 0 else 0
            st.metric("% do CDI", f"{percentual_cdi:.1f}%")
            
            if percentual_cdi >= 110:
                st.success("🔥 Performance excelente!")
            elif percentual_cdi >= 100:
                st.info("✅ Batendo o CDI!")
            else:
                st.warning("📊 Revise sua estratégia")
        
        st.markdown("---")
        st.markdown("#### 💡 Recomendações Personalizadas")
        
        # Recomendações baseadas no perfil
        if taxa_poupanca < 20:
            st.warning("💰 **Aumente sua taxa de poupança**\nTente economizar pelo menos 20% da sua renda mensal.")
        
        if len(dados['carteira']) < 3:
            st.info("🎯 **Diversifique sua carteira**\nTenha pelo menos 3-5 ativos diferentes para reduzir riscos.")
        
        if proventos_mes == 0:
            st.warning("💵 **Invista em ativos que geram renda**\nFIIs e ações pagadoras de dividendos podem gerar renda passiva.")
        
        if rentabilidade < cdi:
            st.error("📉 **Reavalie sua estratégia**\nSua carteira está abaixo do CDI. Considere ativos de maior rentabilidade.")
        
        if patrimonio > 0 and len(dados.get('metas', {})) == 0:
            st.info("🎯 **Defina suas metas**\nEstabeleça objetivos claros de patrimônio e renda passiva.")

# ========== PÁGINA: PERFORMANCE ==========
elif pagina == "📈 Performance":
    st.markdown('<h1 class="main-header">📈 Acompanhamento de Performance</h1>', unsafe_allow_html=True)
    
    # Configurar CDI
    st.subheader("⚙️ Configurações")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        cdi = st.number_input("📊 CDI Acumulado em 2026 (%)", 
                             min_value=0.0, 
                             value=float(dados.get('cdi_anual', 0.0)), 
                             format="%.2f")
    
    with col2:
        if st.button("💾 Salvar CDI"):
            dados['cdi_anual'] = cdi
            salvar_dados(dados)
            st.success("✅ CDI atualizado!")
    
    # Adicionar registro de patrimônio
    st.markdown("---")
    with st.expander("➕ Registrar Patrimônio do Mês", expanded=False):
        with st.form("form_patrimonio"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_registro = st.date_input("📅 Data", value=datetime.now())
            
            with col2:
                valor_patrimonio = st.number_input(
                    "💰 Patrimônio Total (R$)", 
                    min_value=0.01, 
                    value=calcular_patrimonio_atual(dados['carteira']),
                    format="%.2f"
                )
            
            submitted = st.form_submit_button("✅ Registrar")
            
            if submitted:
                novo_registro = {
                    "data": data_registro.strftime('%Y-%m-%d'),
                    "valor": valor_patrimonio
                }
                dados['historico_patrimonio'].append(novo_registro)
                salvar_dados(dados)
                st.success("✅ Patrimônio registrado!")
                st.rerun()
    
    # Gráfico de evolução
    st.markdown("---")
    if dados['historico_patrimonio']:
        df_hist = pd.DataFrame(dados['historico_patrimonio'])
        df_hist['data'] = pd.to_datetime(df_hist['data'])
        df_hist = df_hist.sort_values('data')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_hist['data'],
            y=df_hist['valor'],
            mode='lines+markers',
            name='Patrimônio',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Evolução Patrimonial',
            xaxis_title='Data',
            yaxis_title='Patrimônio (R$)',
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        
        patrimonio_inicial = df_hist.iloc[0]['valor']
        patrimonio_atual = df_hist.iloc[-1]['valor']
        crescimento = ((patrimonio_atual - patrimonio_inicial) / patrimonio_inicial * 100)
        
        with col1:
            st.metric("🏁 Patrimônio Inicial", f"R$ {patrimonio_inicial:,.2f}")
        
        with col2:
            st.metric("📊 Patrimônio Atual", f"R$ {patrimonio_atual:,.2f}")
        
        with col3:
            st.metric("📈 Crescimento", f"{crescimento:+.2f}%")
    else:
        st.info("📌 Registre o patrimônio mensalmente para acompanhar sua evolução!")

# ========== PÁGINA: METAS ==========
elif pagina == "🎯 Metas":
    st.markdown('<h1 class="main-header">🎯 Minhas Metas de Investimento</h1>', unsafe_allow_html=True)
    
    # Configurar metas
    st.subheader("⚙️ Definir Metas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        meta_patrimonio = st.number_input(
            "💰 Meta de Patrimônio para 2026 (R$)",
            min_value=0.0,
            value=float(dados['metas'].get('patrimonio_anual', 0.0)),
            format="%.2f"
        )
    
    with col2:
        meta_renda = st.number_input(
            "💵 Meta de Renda Passiva Mensal (R$)",
            min_value=0.0,
            value=float(dados['metas'].get('renda_passiva_mensal', 0.0)),
            format="%.2f"
        )
    
    if st.button("💾 Salvar Metas"):
        dados['metas']['patrimonio_anual'] = meta_patrimonio
        dados['metas']['renda_passiva_mensal'] = meta_renda
        salvar_dados(dados)
        st.success("✅ Metas atualizadas!")
    
    # Acompanhamento
    st.markdown("---")
    st.subheader("📊 Acompanhamento das Metas")
    
    patrimonio_atual = calcular_patrimonio_atual(dados['carteira'])
    proventos_mes = calcular_proventos_mes_atual(dados['proventos'])
    
    # Meta de Patrimônio
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Meta de Patrimônio")
        if meta_patrimonio > 0:
            progresso_patrimonio = (patrimonio_atual / meta_patrimonio * 100)
            st.progress(min(progresso_patrimonio / 100, 1.0))
            st.metric("Progresso", f"{progresso_patrimonio:.1f}%")
            st.metric("Falta", f"R$ {max(0, meta_patrimonio - patrimonio_atual):,.2f}")
        else:
            st.info("📌 Defina sua meta acima!")
    
    with col2:
        st.markdown("### 💵 Meta de Renda Passiva")
        if meta_renda > 0:
            progresso_renda = (proventos_mes / meta_renda * 100)
            st.progress(min(progresso_renda / 100, 1.0))
            st.metric("Progresso", f"{progresso_renda:.1f}%")
            st.metric("Falta", f"R$ {max(0, meta_renda - proventos_mes):,.2f}")
        else:
            st.info("📌 Defina sua meta acima!")
    
    # Projeções
    st.markdown("---")
    st.subheader("🔮 Projeções")
    
    if patrimonio_atual > 0 and len(dados['historico_patrimonio']) > 1:
        df_hist = pd.DataFrame(dados['historico_patrimonio'])
        df_hist['data'] = pd.to_datetime(df_hist['data'])
        df_hist = df_hist.sort_values('data')
        
        dias_passados = (df_hist.iloc[-1]['data'] - df_hist.iloc[0]['data']).days
        if dias_passados > 0:
            crescimento_dia = (df_hist.iloc[-1]['valor'] - df_hist.iloc[0]['valor']) / dias_passados
            projecao_12m = patrimonio_atual + (crescimento_dia * 365)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📈 Projeção em 12 meses", f"R$ {projecao_12m:,.2f}")
            
            with col2:
                total_prov_ano = sum(p['valor'] for p in dados['proventos'])
                projecao_prov = (total_prov_ano / datetime.now().month) * 12 if datetime.now().month > 0 else 0
                st.metric("💵 Projeção de Proventos/Ano", f"R$ {projecao_prov:,.2f}")

# ========== PÁGINA: PERFIL ==========
elif pagina == "⚙️ Perfil":
    st.markdown('<h1 class="main-header">⚙️ Configurações e Perfil</h1>', unsafe_allow_html=True)
    
    st.subheader("👤 Seus Dados")
    
    with st.form("form_perfil"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input(
                "📝 Nome",
                value=dados.get('perfil', {}).get('nome', ''),
                placeholder="Seu nome"
            )
            renda_mensal = st.number_input(
                "💰 Renda Mensal Média (R$)",
                min_value=0.0,
                value=float(dados.get('perfil', {}).get('renda_mensal', 0)),
                format="%.2f"
            )
        
        with col2:
            data_inicio = st.date_input(
                "📅 Data de Início do Controle",
                value=datetime.strptime(dados.get('perfil', {}).get('data_inicio', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
            )
        
        submitted = st.form_submit_button("💾 Salvar Perfil")
        
        if submitted:
            if 'perfil' not in dados:
                dados['perfil'] = {}
            dados['perfil']['nome'] = nome
            dados['perfil']['renda_mensal'] = renda_mensal
            dados['perfil']['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
            salvar_dados(dados)
            st.success("✅ Perfil atualizado!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("📊 Estatísticas da Sua Jornada")
    
    if dados.get('perfil', {}).get('data_inicio'):
        data_inicio = datetime.strptime(dados['perfil']['data_inicio'], '%Y-%m-%d')
        dias_usando = (datetime.now() - data_inicio).days
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Dias no Sistema", f"{dias_usando}")
        
        with col2:
            st.metric("💼 Ativos na Carteira", f"{len(dados['carteira'])}")
        
        with col3:
            st.metric("💰 Proventos Recebidos", f"{len(dados['proventos'])}")
        
        with col4:
            st.metric("📅 Aportes Realizados", f"{len(dados['aportes'])}")
    
    st.markdown("---")
    st.subheader("⚙️ Configurações Avançadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 Gerenciamento de Dados")
        
        if st.button("📥 Exportar Dados (JSON)", use_container_width=True):
            st.download_button(
                label="💾 Download JSON",
                data=json.dumps(dados, indent=2, ensure_ascii=False),
                file_name=f"backup_investimentos_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        st.markdown("---")
        
        if st.button("🗑️ Limpar Todos os Dados", use_container_width=True, type="secondary"):
            if st.checkbox("⚠️ Confirmo que quero apagar TUDO"):
                dados = {
                    "carteira": [],
                    "proventos": [],
                    "aportes": [],
                    "historico_patrimonio": [],
                    "entradas": [],
                    "saidas": [],
                    "despesas_fixas": [],
                    "metas": {},
                    "cdi_anual": 0,
                    "perfil": {}
                }
                salvar_dados(dados)
                st.success("✅ Dados limpos! Recarregue a página.")
    
    with col2:
        st.markdown("#### ℹ️ Sobre o Sistema")
        st.info("""
        **Sistema Financeiro Completo v2.0**
        
        Criado para ajudar você a:
        - 💸 Controlar entradas e saídas
        - 💼 Gerenciar investimentos
        - 📊 Analisar performance
        - 🎯 Alcançar suas metas
        - 🔮 Projetar seu futuro financeiro
        
        **Desenvolvido com:**
        - Python 3.14
        - Streamlit
        - Plotly
        
        Seus dados são salvos localmente.
        """)

# ========== RODAPÉ ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💡 <b>Dica:</b> Use o sistema regularmente para ter insights mais precisos!</p>
    <p style='font-size: 0.8rem;'>Sistema Financeiro Completo v2.0 | Desenvolvido com ❤️ e Python</p>
</div>
""", unsafe_allow_html=True)
    