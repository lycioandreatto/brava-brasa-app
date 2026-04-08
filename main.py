import streamlit as st
import json
from datetime import datetime
import os
import pandas as pd
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# ===== CONFIGURAÇÃO STREAMLIT =====
st.set_page_config(page_title="Brava Brasa", page_icon="🔥", layout="wide")

# ===== FIREBASE (CONEXÃO SEGURA) =====
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")

db = firestore.client()

# ===== FUNÇÕES DE DADOS =====
def salvar_pedido_firebase(pedido):
    db.collection("pedidos").add(pedido)

def carregar_precos():
    precos_padrao = {
        "CARNE": 8, "FRANGO": 7, "CALABRESA": 7, "CORAÇÃO": 8, 
        "QUEIJO": 6, "MISTO": 9, "COCA": 6, "GUARANA": 6, "HEINEKEN": 10
    }
    try:
        precos_ref = db.collection("precos").stream()
        precos_carregados = {doc.id: doc.to_dict().get("valor", 0) for doc in precos_ref}
        
        # Preenche com padrão se o Firebase estiver vazio
        for item, valor in precos_padrao.items():
            if item not in precos_carregados:
                precos_carregados[item] = valor
                db.collection("precos").document(item).set({"valor": valor})
        return precos_carregados
    except:
        return precos_padrao

def salvar_preco_firebase(item, valor):
    db.collection("precos").document(item).set({"valor": valor})

# ===== ESTILO CSS CUSTOMIZADO =====
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .btn-mais { background-color: #28a745 !important; color: white !important; }
    .btn-menos { background-color: #dc3545 !important; color: white !important; }
    .card-mesa {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
        text-align: center;
        margin-bottom: 10px;
    }
    .total-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ff6600;
        color: white;
        text-align: center;
        padding: 15px;
        font-size: 24px;
        font-weight: bold;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# ===== INICIALIZAÇÃO DE ESTADO =====
BRASIL = pytz.timezone("America/Sao_Paulo")
precos = carregar_precos()

if "pagina" not in st.session_state: st.session_state.pagina = "mesas"
if "mesa_selecionada" not in st.session_state: st.session_state.mesa_selecionada = None
if "pedidos_ativos" not in st.session_state: st.session_state.pedidos_ativos = {}

# ===== NAVEGAÇÃO =====
st.sidebar.title("🔥 Brava Brasa")
opcao = st.sidebar.radio("Navegação", ["Mesas", "Relatórios", "Ajustar Preços"])

if opcao == "Relatórios": st.session_state.pagina = "relatorios"
elif opcao == "Ajustar Preços": st.session_state.pagina = "precos"
else: 
    if st.session_state.pagina not in ["pedido"]: st.session_state.pagina = "mesas"

# =========================
# PÁGINA: GESTÃO DE MESAS
# =========================
if st.session_state.pagina == "mesas":
    st.header("🪑 Mesas Ativas")
    mesas_lista = [f"Mesa {i}" for i in range(1, 11)]
    
    cols = st.columns(2)
    for idx, nome_mesa in enumerate(mesas_lista):
        with cols[idx % 2]:
            esta_ocupada = nome_mesa in st.session_state.pedidos_ativos
            cor = "🔴" if esta_ocupada else "🟢"
            
            st.markdown(f"""<div class="card-mesa"><h3>{cor} {nome_mesa}</h3></div>""", unsafe_allow_html=True)
            if st.button(f"Abrir/Ver {nome_mesa}", key=f"btn_{nome_mesa}"):
                if nome_mesa not in st.session_state.pedidos_ativos:
                    st.session_state.pedidos_ativos[nome_mesa] = {item: 0 for item in precos}
                st.session_state.mesa_selecionada = nome_mesa
                st.session_state.pagina = "pedido"
                st.rerun()

# =========================
# PÁGINA: LANÇAR PEDIDO
# =========================
elif st.session_state.pagina == "pedido":
    mesa = st.session_state.mesa_selecionada
    st.header(f"📝 Pedido: {mesa}")
    
    if st.button("⬅️ Voltar para Mesas"):
        st.session_state.pagina = "mesas"
        st.rerun()

    st.divider()
    
    # Grid de Itens
    for item, valor in precos.items():
        c1, c2, c3, c4 = st.columns([3, 2, 1, 2])
        qtd_atual = st.session_state.pedidos_ativos[mesa][item]
        
        with c1: st.markdown(f"**{item}**\nR$ {valor}")
        with c2:
            if st.button(f"➕", key=f"add_{item}"):
                st.session_state.pedidos_ativos[mesa][item] += 1
                st.rerun()
        with c3: st.markdown(f"### {qtd_atual}")
        with c4:
            if st.button(f"➖", key=f"sub_{item}"):
                if st.session_state.pedidos_ativos[mesa][item] > 0:
                    st.session_state.pedidos_ativos[mesa][item] -= 1
                    st.rerun()

    # Cálculo Total
    total = sum(st.session_state.pedidos_ativos[mesa][i] * precos[i] for i in precos)
    
    st.markdown(f"<div class='total-footer'>TOTAL: R$ {total:.2f}</div>", unsafe_allow_html=True)
    st.write("\n\n") # Espaço para o footer não cobrir o botão

    if total > 0:
        if st.button("✅ FINALIZAR E SALVAR", use_container_width=True):
            agora = datetime.now(BRASIL)
            dados_final = {
                "mesa": mesa,
                "itens": {k: v for k, v in st.session_state.pedidos_ativos[mesa].items() if v > 0},
                "total": total,
                "data": agora.strftime("%Y-%m-%d"),
                "hora": agora.strftime("%H:%M"),
                "timestamp": agora
            }
            salvar_pedido_firebase(dados_final)
            del st.session_state.pedidos_ativos[mesa]
            st.success("Pedido enviado com sucesso!")
            st.session_state.pagina = "mesas"
            st.rerun()

# =========================
# PÁGINA: AJUSTAR PREÇOS
# =========================
elif st.session_state.pagina == "precos":
    st.header("⚙️ Ajustar Valores")
    for item, valor in precos.items():
        novo_v = st.number_input(f"Preço {item}", value=float(valor), step=0.5, key=f"edit_{item}")
        if novo_v != float(valor):
            salvar_preco_firebase(item, novo_v)
            st.toast(f"Preço de {item} atualizado!")

# =========================
# PÁGINA: RELATÓRIOS
# =========================
elif st.session_state.pagina == "relatorios":
    st.header("📊 Vendas de Hoje")
    hoje = datetime.now(BRASIL).strftime("%Y-%m-%d")
    
    pedidos_ref = db.collection("pedidos").where("data", "==", hoje).stream()
    lista_pedidos = [p.to_dict() for p in pedidos_ref]
    
    if lista_pedidos:
        df = pd.DataFrame(lista_pedidos)
        st.metric("Faturamento Total Hoje", f"R$ {df['total'].sum():.2f}")
        st.dataframe(df[['hora', 'mesa', 'total']])
    else:
        st.info("Nenhum pedido realizado hoje.")
