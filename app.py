import streamlit as st
from supabase import create_client

# Função para conectar com segurança
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao ler Secrets: {e}")
        return None

supabase = init_connection()

if supabase:
    st.success("Caminho do Monarca Estabelecido! ⚔️")
else:
    st.error("Falha na conexão. Verifique os Secrets.")

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("Erro na conexão com o banco de dados. Verifique as chaves.")
    st.stop()

# --- CONFIGURAÇÃO DE UI ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="⚔️")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
def carregar_player():
    res = supabase.table("player").select("*").limit(1).execute()
    if not res.data:
        # Cria o personagem inicial se o banco estiver vazio
        supabase.table("player").insert({"level": 1, "exp": 0, "rank": "E", "gold": 0}).execute()
        return carregar_player()
    return res.data[0]

# --- INTERFACE PRINCIPAL ---
player = carregar_player()
xp_target = player['level'] * 100

st.sidebar.title(f"🌑 MONARCA")
st.sidebar.markdown(f"### **RANK {player['rank']}**")
st.sidebar.metric("Nível", player['level'], f"{player['exp']}/{xp_target} XP")
st.sidebar.metric("Ouro", f"{player['gold']} G")

# --- MISSÕES ---
st.header("🎯 Central de Missões")

with st.expander("➕ CADASTRAR NOVA MISSÃO"):
    nome_q = st.text_input("O que você precisa fazer?")
    if st.button("PUBLICAR NO SISTEMA"):
        if nome_q:
            supabase.table("custom_quests").insert({"nome": nome_q, "xp": 50}).execute()
            st.success("Missão registrada na nuvem!")
            st.rerun()

st.subheader("Quests Ativas")
quests_res = supabase.table("custom_quests").select("*").execute()

for q in quests_res.data:
    col1, col2 = st.columns([4, 1])
    col1.write(f"⚔️ {q['nome']} | `+50 XP`")
    if col2.button("CONCLUIR", key=f"q_{q['id']}"):
        # Atualiza XP no banco
        novo_xp = player['exp'] + 50
        novo_lvl = player['level']
        
        if novo_xp >= xp_target:
            novo_lvl += 1
            novo_xp = 0
        
        supabase.table("player").update({"exp": novo_xp, "level": novo_lvl}).eq("id", player['id']).execute()
        supabase.table("custom_quests").delete().eq("id", q['id']).execute()
        st.balloons()

        st.rerun()
