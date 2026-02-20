import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

@st.cache_resource
def init_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"].strip(), st.secrets["SUPABASE_KEY"].strip())
    except: return None

supabase = init_db()

# Garante um ID único na sessão
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

def obter_titulo(level):
    if level >= 50: return "Soberano das Sombras"
    if level >= 15: return "Monarca"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

# --- FUNÇÃO DE CARREGAMENTO COM VALIDAÇÃO ---
def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            return res.data[0]
        return None
    except: return None

hunter = carregar_dados()

# --- TELA DE REGISTRO (BLOQUEIO INICIAL) ---
if hunter is None:
    st.title("🌑 O DESPERTAR")
    nome = st.text_input("Como o Sistema deve te chamar?")
    if st.button("CONFIRMAR"):
        if nome and supabase:
            supabase.table("hunters").insert({
                "user_id": st.session_state.user_id, "nome": nome, 
                "level": 1, "exp": 0, "gold": 0, "rank": "E"
            }).execute()
            st.rerun()
    st.stop() # Mata a execução aqui até o hunter existir

# --- A PARTIR DAQUI, O HUNTER É GARANTIDO ---
u_id = hunter['user_id'] # Agora isso nunca vai dar erro

# SIDEBAR
st.sidebar.title("🌑 STATUS")
st.sidebar.subheader(f"[{obter_titulo(hunter['level'])}]")
st.sidebar.markdown(f"**NOME:** {hunter['nome']} | **LVL:** {hunter['level']}")
st.sidebar.metric("OURO", f"{hunter['gold']} G")

# ABAS
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests")
    c1, c2 = st.columns([3, 1])
    m_txt = c1.text_input("Missão:", key="new_quest_input")
    r_sel = c2.selectbox("Rank:", ["E", "D", "C", "B", "A", "S"])
    recs = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}

    if st.button("REGISTRAR"):
        if m_txt:
            try:
                supabase.table("active_quests").insert({
                    "user_id": u_id, 
                    "missao": f"[{r_sel}] {m_txt}", 
                    "recompensa": recs[r_sel]
                }).execute()
                st.rerun()
            except:
                st.error("Erro na coluna 'recompensa'. Rode o comando SQL no Supabase!")

    st.divider()
    qs_res = supabase.table("active_quests").eq("user_id", u_id).execute()
    for q in qs_res.data:
        col1, col2 = st.columns([4, 1])
        col1.info(q['missao'])
        if col2.button("CONCLUIR", key=f"q_{q['id']}"):
            val = q.get('recompensa', 20)
            supabase.table("hunters").update({"gold": hunter['gold']+val, "exp": hunter['exp']+(val//2)}).eq("user_id", u_id).execute()
            supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
            supabase.table("active_quests").delete().eq("id", q['id']).execute()
            st.rerun()

with t_a:
    st.header("Arise")
    hist_res = supabase.table("shadow_history").eq("user_id", u_id).execute()
    if not hist_res.data:
        st.write("Sem almas para extrair.")
    for h in hist_res.data:
        st.warning(f"Alma: {h['origem']}")
        n_s = st.text_input("Nome da Sombra:", key=f"name_{h['id']}")
        if st.button("EXTRAIR", key=f"arise_{h['id']}"):
            if n_s:
                supabase.table("army").insert({"user_id": u_id, "nome": n_s, "origem": h['origem']}).execute()
                supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                st.rerun()

with t_i:
    st.header("Exército")
    army_res = supabase.table("army").eq("user_id", u_id).execute()
    for s in army_res.data:
        st.write(f"🌑 **{s['nome']}** (Sombra de: {s['origem']})")
