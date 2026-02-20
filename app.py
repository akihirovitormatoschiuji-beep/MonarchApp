import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

@st.cache_resource
def init_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"].strip(), st.secrets["SUPABASE_KEY"].strip())
    except:
        return None

supabase = init_db()

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- ESTILO ---
st.markdown("<style>.stApp { background-color: #050505; color: #E0E0E0; } .shadow-card { border-left: 5px solid #7928CA; background: #111; padding: 15px; margin: 10px 0; }</style>", unsafe_allow_html=True)

# --- CARREGAR DADOS ---
def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

hunter = carregar_dados()

# --- LOGICA DE REGISTRO ---
if not hunter:
    st.title("🌑 O DESPERTAR")
    nome_in = st.text_input("Seu nome de Caçador:")
    if st.button("CONFIRMAR"):
        if nome_in and supabase:
            supabase.table("hunters").insert({"user_id": st.session_state.user_id, "nome": nome_in, "level": 1, "exp": 0, "gold": 0, "rank": "E"}).execute()
            st.rerun()
    st.stop()

# --- INTERFACE DO CAÇADOR ---
st.sidebar.title("🌑 STATUS")
st.sidebar.markdown(f"**NOME:** {hunter['nome']}  \n**RANK:** {hunter['rank']}")
st.sidebar.metric("GOLD", f"{hunter['gold']} G")

# Abas do Sistema
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests")
    missao = st.text_input("Desafio:")
    if st.button("REGISTRAR") and missao:
        supabase.table("active_quests").insert({"user_id": hunter['user_id'], "missao": missao}).execute()
        st.rerun()
    
    qs = supabase.table("active_quests").eq("user_id", hunter['user_id']).execute()
    for q in qs.data:
        col1, col2 = st.columns([4,1])
        col1.info(q['missao'])
        if col2.button("OK", key=q['id']):
            supabase.table("hunters").update({"exp": hunter['exp']+50, "gold": hunter['gold']+20}).eq("user_id", hunter['user_id']).execute()
            supabase.table("shadow_history").insert({"user_id": hunter['user_id'], "origem": q['missao']}).execute()
            supabase.table("active_quests").delete().eq("id", q['id']).execute()
            st.rerun()

with t_a:
    st.header("Arise")
    hist = supabase.table("shadow_history").eq("user_id", hunter['user_id']).execute()
    for h in hist.data:
        st.markdown(f"<div class='shadow-card'>{h['origem']}</div>", unsafe_allow_html=True)
        n_s = st.text_input("Nome da Sombra:", key=f"s_{h['id']}")
        if st.button("ARISE", key=f"b_{h['id']}") and hunter['gold'] >= 100:
            supabase.table("army").insert({"user_id": hunter['user_id'], "nome": n_s, "origem": h['origem']}).execute()
            supabase.table("hunters").update({"gold": hunter['gold']-100}).eq("user_id", hunter['user_id']).execute()
            supabase.table("shadow_history").delete().eq("id", h['id']).execute()
            st.rerun()

with t_l:
    st.header("Loja")
    if st.button("Comprar Poção (100G)"):
        if hunter['gold'] >= 100:
            supabase.table("hunters").update({"gold": hunter['gold']-100}).eq("user_id", hunter['user_id']).execute()
            st.success("Item comprado!")
            st.rerun()

with t_i:
    st.header("Exército")
    exercito = supabase.table("army").eq("user_id", hunter['user_id']).execute()
    for s in exercito.data:
        st.write(f"🌑 **{s['nome']}** (Sombra de: {s['origem']})")
