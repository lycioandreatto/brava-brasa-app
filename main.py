import streamlit as st
import urllib.parse

st.set_page_config(page_title="Match do Espeto", page_icon="🔥", layout="wide")

# ESTILO
st.markdown("""
<style>

.stApp{
background:#f3f3f3;
font-family:sans-serif;
}

.title{
text-align:center;
color:#ff2e8a;
font-size:40px;
font-weight:bold;
}

.subtitle{
text-align:center;
margin-bottom:30px;
}

.card{
background:white;
padding:15px;
border-radius:15px;
box-shadow:0 3px 10px rgba(0,0,0,0.1);
margin-bottom:15px;
}

button{
background:#ff2e8a !important;
color:white !important;
border-radius:8px !important;
}

.total{
font-size:24px;
color:#ff2e8a;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🔥 MATCH DO ESPETO</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Encontro Perfeito do Sabor</div>', unsafe_allow_html=True)

# CARDÁPIO
menu = {
"Espeto de Carne": {"preco":8,"img":"https://i.imgur.com/Jp1XK9P.jpg"},
"Espeto de Frango": {"preco":7,"img":"https://i.imgur.com/Qb6KX7A.jpg"},
"Espeto de Linguiça": {"preco":7,"img":"https://i.imgur.com/ExxZ4pC.jpg"},
"Queijo Coalho": {"preco":9,"img":"https://i.imgur.com/T1xKQy2.jpg"},
"Coca Cola": {"preco":5,"img":"https://i.imgur.com/0umadnY.jpg"},
"Guaraná": {"preco":5,"img":"https://i.imgur.com/q3Z3N6X.jpg"},
"Água": {"preco":3,"img":"https://i.imgur.com/G9dZL6V.jpg"}
}

if "cart" not in st.session_state:
    st.session_state.cart={}

st.header("🍢 Cardápio")

for item,data in menu.items():

    col1,col2,col3,col4=st.columns([1,2,1,1])

    with col1:
        st.image(data["img"],width=80)

    with col2:
        st.write(f"**{item}**")
        st.write(f"R$ {data['preco']}")

    with col3:
        if st.button("+",key=item):
            st.session_state.cart[item]=st.session_state.cart.get(item,0)+1

    with col4:
        if item in st.session_state.cart:
            st.write(f"x{st.session_state.cart[item]}")
        else:
            st.write("0")

# CARRINHO
st.header("🛒 Seu Pedido")

total=0
pedido=""

for item,qtd in st.session_state.cart.items():
    preco=menu[item]["preco"]
    subtotal=preco*qtd
    total+=subtotal

    st.write(f"{qtd}x {item} - R$ {subtotal}")
    pedido+=f"{qtd}x {item} - R$ {subtotal}\n"

st.markdown(f"<div class='total'>Total: R$ {total}</div>",unsafe_allow_html=True)

# DADOS
st.header("📍 Entrega")

nome=st.text_input("Nome")
telefone=st.text_input("Telefone")
endereco=st.text_input("Endereço")
obs=st.text_area("Observação")

pagamento=st.selectbox(
"Forma de pagamento",
["PIX","Dinheiro","Cartão de Crédito","Cartão de Débito"]
)

numero="5579998439298"

mensagem=f"""
Pedido - Match do Espeto 🔥

Cliente: {nome}
Telefone: {telefone}

Itens:
{pedido}

Total: R$ {total}

Pagamento: {pagamento}

Endereço:
{endereco}

Obs:
{obs}
"""

link=f"https://wa.me/{numero}?text={urllib.parse.quote(mensagem)}"

st.markdown(
f'<a href="{link}" target="_blank"><button style="width:100%;height:55px;font-size:18px;background:#ff2e8a;color:white;border:none;border-radius:10px;">📲 Fazer Pedido no WhatsApp</button></a>',
unsafe_allow_html=True
)
