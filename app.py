import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA ASSOCIAÇÃO ---
st.set_page_config(page_title="SISTEMA MONARCA", page_icon="🌑", layout="wide")

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def init_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase = init_db()

# --- ESTILO VISUAL (RANK S) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .stButton>button { background: linear-gradient(45deg, #4b0082, #000000); color: white; border: 1px solid #7928CA; }
    .shadow-card { border-left: 5px solid #7928CA; background: #111; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE IDENTIFICAÇÃO (PARA MILHARES DE USUÁRIOS) ---
if 'user_id' not in st.session_state:
    # No futuro, aqui entrará o Login oficial. Por enquanto, usamos um ID único por navegador.
    st.session_state.user_id = str(uuid.uuid4())

# --- LÓGICA DE DADOS DO CAÇADOR ---
def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            return res.data[0]
        else:
            # Novo Registro na Associação de Caçadores
            novo_h = {"user_id": st.session_state.user_id, "nome": "Recruta", "level": 1, "exp": 0, "gold": 0, "rank": "E", "titulo": "Candidato"}
            supabase.table("hunters").insert(novo_h).execute()
            return novo_h
    except:
        return {"nome": "Offline", "level": 0, "exp": 0, "gold": 0, "rank": "N/A", "titulo": "Sem Conexão"}

hunter = carregar_dados()

# --- SIDEBAR: ASSOCIAÇÃO DE CAÇADORES ---
st.sidebar.image("https://static.wikia.nocookie.net/solo-leveling/images/e/e8/Hunter_Association_Logo.png", width=100) # Logo fictícia
st.sidebar.title("PAINEL DO CAÇADOR")
st.sidebar.markdown(f"**NOME:** {hunter['nome']}")
st.sidebar.markdown(f"**RANK:** {hunter['rank']}")
st.sidebar.metric("OURO", f"{hunter['gold']} G")
st.sidebar.progress(min(hunter['exp']/(hunter['level']*100), 1.0))

# --- ABAS DO SISTEMA ---
tab_quests, tab_arise, tab_loja, tab_inventario = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with tab_quests:
    st.header("Quests de Treinamento Diário")
    with st.form("nova_missao"):
        missao = st.text_input("Qual desafio você enfrentou hoje?")
        submit = st.form_submit_button("REGISTRAR DESAFIO")
        if submit and missao:
            supabase.table("active_quests").insert({"user_id": st.session_state.user_id, "missao": missao}).execute()
            st.rerun()

    st.subheader("Desafios em Aberto")
    qs = supabase.table("active_quests").eq("user_id", st.session_state.user_id).execute()
    for q in qs.data:
        col1, col2 = st.columns([4,1])
        col1.info(f"DESAFIO: {q['missao']}")
        if col2.button("FINALIZAR", key=q['id']):
            # Lógica de recompensa
            supabase.table("hunters").update({"exp": hunter['exp']+50, "gold": hunter['gold']+20}).eq("user_id", st.session_state.user_id).execute()
            # Mover para histórico de sombras (para virar Arise depois)
            supabase.table("shadow_history").insert({"user_id": st.session_state.user_id, "origem": q['missao']}).execute()
            supabase.table("active_quests").delete().eq("id", q['id']).execute()
            st.rerun()

with tab_arise:
    st.header("Extração de Sombras (ARISE)")
    st.write("Transforme seus desafios vencidos em soldados do seu exército.")
    
    historico = supabase.table("shadow_history").eq("user_id", st.session_state.user_id).execute()
    if historico.data:
        for h in historico.data:
            with st.container():
                st.markdown(f"<div class='shadow-card'>Desafio Vencido: {h['origem']}</div>", unsafe_allow_html=True)
                nome_sombra = st.text_input("Dê um nome à essa Sombra:", key=f"name_{h['id']}")
                if st.button("ARISE", key=f"arise_{h['id']}"):
                    if nome_sombra:
                        supabase.table("army").insert({"user_id": st.session_state.user_id, "nome": nome_sombra, "origem": h['origem']}).execute()
                        supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                        st.success(f"A sombra '{nome_sombra}' agora serve ao Monarca!")
                        st.rerun()
    else:
        st.info("Vença desafios nas Quests para poder usar o ARISE.")

with tab_loja:
    st.header("Mercado da Associação")
    itens = [
        {"nome": "Poção de Fadiga", "preço": 100, "desc": "Recupera energia para mais quests."},
        {"nome": "Chave de Dungeon", "preço": 500, "desc": "Acesso a desafios Rank S."},
        {"nome": "Pedra de Re-Awakening", "preço": 2000, "desc": "Mudar seu Rank atual."}
    ]
    for item in itens:
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(f"**{item['nome']}**")
        c2.write(f"{item['preço']} Gold")
        if c3.button("COMPRAR", key=item['nome']):
            if hunter['gold'] >= item['preço']:
                # Lógica de compra
                st.success("Item adquirido!")
            else:
                st.error("Gold insuficiente.")

with tab_inventario:
    st.header("Equipamentos e Títulos")
    st.write(f"**Título Atual:** {hunter['titulo']}")
    # Lista de sombras do exército real
    st.subheader("Seu Exército de Sombras")
    exercito = supabase.table("army").eq("user_id", st.session_state.user_id).execute()
    for s in exercito.data:
        st.markdown(f"🌑 **{s['nome']}** (Nascida de: {s['origem']})")