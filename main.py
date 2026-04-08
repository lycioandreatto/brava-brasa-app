import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(page_title="Brava Brasa", page_icon="🔥", layout="wide")

# ===== CONEXÃO FIREBASE =====
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro de conexão Firebase: {e}")

db = firestore.client()

# ===== ESTRUTURA DO CARDÁPIO =====
CARDAPIO_ESTRUTURA = {
    "🍢 ESPETINHOS": ["CARNE", "FRANGO", "CALABRESA", "MISTO", "CORAÇÃO", "QUEIJO"],
    "🥤 BEBIDAS": ["COCA LATA", "FANTA LATA", "GUARANÁ LATA", "ÁGUA MINERAL", "ITAIPAVA", "AMSTEL", "HEINEKEN", "ICE CABARÉ", "VINHO - TAÇA", "DOSE PITÚ", "DREHER"]
}

def carregar_precos():
    precos_ref = db.collection("precos").stream()
    carregados = {doc.id: doc.to_dict().get("valor", 0.0) for doc in precos_ref}
    padrao = {
        "CARNE": 8.0, "FRANGO": 7.0, "CALABRESA": 7.0, "MISTO": 9.0, "CORAÇÃO": 8.0, "QUEIJO": 7.0,
        "COCA LATA": 6.0, "FANTA LATA": 6.0, "GUARANÁ LATA": 6.0, "ÁGUA MINERAL": 4.0,
        "ITAIPAVA": 8.0, "AMSTEL": 9.0, "HEINEKEN": 12.0, "ICE CABARÉ": 10.0,
        "VINHO - TAÇA": 12.0, "DOSE PITÚ": 5.0, "DREHER": 6.0
    }
    for item, valor in padrao.items():
        if item not in carregados:
            carregados[item] = valor
            db.collection("precos").document(item).set({"valor": valor})
    return carregados

def salvar_rascunho_firebase(mesa, itens):
    itens_filtrados = {k: v for k, v in itens.items() if v > 0}
    if itens_filtrados:
        db.collection("pedidos_pendentes").document(mesa).set({"itens": itens_filtrados})
    else:
        db.collection("pedidos_pendentes").document(mesa).delete()

def carregar_rascunhos_firebase():
    docs = db.collection("pedidos_pendentes").stream()
    return {doc.id: doc.to_dict().get("itens", {}) for doc in docs}

# ===== INICIALIZAÇÃO =====
BRASIL = pytz.timezone("America/Sao_Paulo")
precos = carregar_precos()

if "pedidos_ativos" not in st.session_state:
    rascunhos = carregar_rascunhos_firebase()
    mesas_ordenadas = {}
    for i in range(1, 13):
        nome_mesa = f"Mesa {i}"
        base = {item: 0 for cat in CARDAPIO_ESTRUTURA.values() for item in cat}
        if nome_mesa in rascunhos:
            base.update(rascunhos[nome_mesa])
        mesas_ordenadas[nome_mesa] = base
    st.session_state.pedidos_ativos = mesas_ordenadas

if "pagina" not in st.session_state: st.session_state.pagina = "mesas"
if "mesa_atual" not in st.session_state: st.session_state.mesa_atual = None

# ===== CSS PARA MATAR O ESPAÇAMENTO =====
st.markdown("""
<style>
    /* Remove margens inúteis e barra de navegação superior */
    .block-container { padding: 1rem 0.5rem !important; }
    header { visibility: hidden; }
    
    /* Container do Item: Nome à esquerda, Controles à direita */
    .item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 5px;
        border-bottom: 1px solid #eee;
    }
    
    .item-info { flex-grow: 1; }
    .item-name { font-weight: bold; font-size: 16px; margin: 0; }
    .item-price { color: #666; font-size: 14px; margin: 0; }

    /* Bloco de controle: Travado para não separar */
    .control-block {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 120px;
        justify-content: flex-end;
    }
    
    /* Estilo dos botões do Streamlit dentro da linha */
    div[data-testid="stHorizontalBlock"] { gap: 0px !important; }
    
    /* Botões de Mesa */
    .stButton > button { width: 100%; border-radius: 8px; }
    
    /* Barra de Total Fixa */
    .total-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #ff6600; color: white;
        text-align: center; padding: 15px;
        font-size: 20px; font-weight: bold;
        z-index: 999; border-top: 2px solid white;
    }
    
    .card-mesa { padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# =========================
# PÁGINA: MESAS
# =========================
if st.session_state.pagina == "mesas":
    st.title("🍽️ Mesas Ativas")
    lista_mesas = [f"Mesa {i}" for i in range(1, 13)]
    cols = st.columns(2)
    for i, nome in enumerate(lista_mesas):
        with cols[i % 2]:
            itens_mesa = st.session_state.pedidos_ativos.get(nome, {})
            ocupada = any(v > 0 for v in itens_mesa.values())
            cor = "#ff4b4b" if ocupada else "#28a745"
            st.markdown(f'<div class="card-mesa" style="border: 2px solid {cor};"><b>{nome}</b></div>', unsafe_allow_html=True)
            if st.button(f"Abrir {nome}", key=f"btn_{nome}"):
                st.session_state.mesa_atual = nome
                st.session_state.pagina = "pedido"
                st.rerun()

# =========================
# PÁGINA: PEDIDO (CARDÁPIO)
# =========================
elif st.session_state.pagina == "pedido":
    mesa = st.session_state.mesa_atual
    
    col_v, col_t = st.columns([1, 3])
    with col_v:
        if st.button("⬅️ Sair"):
            st.session_state.pagina = "mesas"
            st.rerun()
    with col_t:
        st.subheader(f"📍 {mesa}")

    tabs = st.tabs(["🍢 ESPETINHOS", "🥤 BEBIDAS"])

    def render_item(item, mesa):
        valor = precos.get(item, 0.0)
        qtd = st.session_state.pedidos_ativos[mesa].get(item, 0)
        
        # Usamos st.container para criar a linha e colunas internas bem espremidas
        with st.container():
            # Criamos colunas com proporções que forçam os botões a ficarem juntos
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            
            with c1:
                st.markdown(f"**{item}** \n<small>R$ {valor:.2f}</small>", unsafe_allow_html=True)
            
            with c2:
                if st.button("➖", key=f"sub_{item}_{mesa}"):
                    if st.session_state.pedidos_ativos[mesa][item] > 0:
                        st.session_state.pedidos_ativos[mesa][item] -= 1
                        salvar_rascunho_firebase(mesa, st.session_state.pedidos_ativos[mesa])
                        st.rerun()
            
            with c3:
                # Centraliza o número entre os botões
                st.markdown(f"<h4 style='text-align:center; margin:0;'>{qtd}</h4>", unsafe_allow_html=True)
                
            with c4:
                if st.button("➕", key=f"add_{item}_{mesa}"):
                    st.session_state.pedidos_ativos[mesa][item] += 1
                    salvar_rascunho_firebase(mesa, st.session_state.pedidos_ativos[mesa])
                    st.rerun()
        st.markdown("<hr style='margin:0'>", unsafe_allow_html=True)

    for i, cat in enumerate(CARDAPIO_ESTRUTURA.keys()):
        with tabs[i]:
            for item in CARDAPIO_ESTRUTURA[cat]:
                render_item(item, mesa)

    total = sum(st.session_state.pedidos_ativos[mesa][i] * precos.get(i, 0) for i in st.session_state.pedidos_ativos[mesa])
    st.markdown(f"<div class='total-bar'>TOTAL: R$ {total:.2f}</div>", unsafe_allow_html=True)
    st.write("<br><br><br><br>", unsafe_allow_html=True)

    if total > 0:
        if st.button("✅ FINALIZAR CONTA", use_container_width=True):
            agora = datetime.now(BRASIL)
            pedido_final = {
                "mesa": mesa,
                "itens": {k: v for k, v in st.session_state.pedidos_ativos[mesa].items() if v > 0},
                "total": total,
                "data": agora.strftime("%Y-%m-%d"),
                "hora": agora.strftime("%H:%M")
            }
            db.collection("pedidos").add(pedido_final)
            db.collection("pedidos_pendentes").document(mesa).delete()
            st.session_state.pedidos_ativos[mesa] = {item: 0 for cat in CARDAPIO_ESTRUTURA.values() for item in cat}
            st.success("Pedido Salvo!")
            st.session_state.pagina = "mesas"
            st.rerun()

# =========================
# PÁGINA: RELATÓRIO
# =========================
elif st.session_state.pagina == "relatorio":
    st.header("📊 Vendas")
    data_sel = st.date_input("Data", datetime.now(BRASIL))
    data_str = data_sel.strftime("%Y-%m-%d")
    docs = db.collection("pedidos").where("data", "==", data_str).stream()
    vendas = sorted([d.to_dict() for d in docs], key=lambda x: x['hora'], reverse=True)
    if vendas:
        st.metric("Total Vendido", f"R$ {sum(v['total'] for v in vendas):.2f}")
        for v in vendas:
            with st.expander(f"{v['hora']} - {v['mesa']} | R$ {v['total']:.2f}"):
                for item, qtd in v['itens'].items(): st.write(f"{qtd}x {item}")
    else: st.info("Sem vendas.")

# =========================
# PÁGINA: AJUSTAR PREÇOS
# =========================
elif st.session_state.pagina == "precos":
    st.header("⚙️ Preços")
    for cat, itens in CARDAPIO_ESTRUTURA.items():
        st.subheader(cat)
        for item in itens:
            v_atual = float(precos.get(item, 0.0))
            novo_v = st.number_input(f"{item}", value=v_atual, step=0.5, key=f"p_{item}")
            if novo_v != v_atual:
                db.collection("precos").document(item).set({"valor": novo_v})
                st.toast(f"{item} atualizado!")
