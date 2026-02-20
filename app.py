import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SISTEMA MONARCA", page_icon="🌑", layout="wide")

# Conexão segura
@st.cache_resource
def init_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase = init_db()

# --- ESTILO ---
st.markdown("<style>.stApp { background-color: #050505; color: #E0E0E0; }</style>", unsafe_allow_html=True)

# ID do Usuário
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- CARREGAR DADOS (COM TRAVA ANTIGRADUAÇÃO ZERO) ---
def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            dados = res.data[0]
            # Se o nível for 0 por erro no banco, corrigimos aqui
            if dados['level'] <= 0: dados['level'] = 1
            return dados
        else:
            novo = {"user_id": st.session_state.user_id, "nome": "Recruta", "level": 1, "exp": 0, "gold": 0, "rank": "E", "titulo": "Candidato"}
            supabase.table("hunters").insert(novo).execute()
            return novo
    except:
        return {"nome": "Offline", "level": 1, "exp": 0, "gold": 0, "rank": "N/A", "titulo": "Sem Conexão"}

hunter = carregar_dados()

# --- SIDEBAR ---
st.sidebar.title("PAINEL DO CAÇADOR")
st.sidebar.markdown(f"**NOME:** {hunter['nome']}")
st.sidebar.markdown(f"**RANK:** {hunter['rank']}")
st.sidebar.metric("OURO", f"{hunter['gold']} G")

# Barra de XP com trava contra divisão por zero
proximo_nivel = (hunter['level'] * 100) if hunter['level'] > 0 else 100
progresso = min(hunter['exp'] / proximo_nivel, 1.0)
st.sidebar.write(f"XP: {hunter['exp']} / {proximo_nivel}")
st.sidebar.progress(progresso)

# --- ABAS ---
t1, t2, t3, t4 = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t1:
    st.header("Associação de Caçadores: Quests")
    missao = st.text_input("Qual o seu desafio hoje?")
    if st.button("REGISTRAR QUEST"):
        if missao and supabase:
            supabase.table("active_quests").insert({"user_id": hunter['user_id'], "missao": missao}).execute()
            st.rerun()

    # Listar Quests
    try:
        qs = supabase.table("active_quests").eq("user_id", hunter['user_id']).execute()
        for q in qs.data:
            col1, col2 = st.columns([4, 1])
            col1.info(f"Quest: {q['missao']}")
            if col2.button("CONCLUIR", key=q['id']):
                # Ganha XP e Ouro
                supabase.table("hunters").update({"exp": hunter['exp']+50, "gold": hunter['gold']+20}).eq("user_id", hunter['user_id']).execute()
                supabase.table("shadow_history").insert({"user_id": hunter['user_id'], "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()
    except:
        st.write("Sem quests ativas.")

with t2:
    st.header("Extração de Sombras")
    st.write("Custo: 100 Gold")
    # Aqui entra o sistema de Arise que você quer
    res_hist = supabase.table("shadow_history").eq("user_id", hunter['user_id']).execute()
    if res_hist.data:
        for h in res_hist.data:
            st.write(f"Desafio Vencido: {h['origem']}")
            nome_s = st.text_input("Dê um nome à sombra:", key=f"s_{h['id']}")
            if st.button("ARISE", key=f"btn_{h['id']}"):
                if hunter['gold'] >= 100:
                    supabase.table("army").insert({"user_id": hunter['user_id'], "nome": nome_s, "origem": h['origem']}).execute()
                    supabase.table("hunters").update({"gold": hunter['gold']-100}).eq("user_id", hunter['user_id']).execute()
                    supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                    st.success("ERISE!")
                    st.rerun()
                else:
                    st.error("Ouro insuficiente.")
