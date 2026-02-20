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
if 'user_id' not in st.session_state: st.session_state.user_id = str(uuid.uuid4())

def obter_titulo(level):
    if level >= 50: return "Soberano das Sombras"
    if level >= 15: return "Monarca"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        return res.data[0] if res.data else None
    except: return None

hunter = carregar_dados()

# --- TELA INICIAL ---
if not hunter:
    st.title("🌑 O DESPERTAR")
    nome = st.text_input("Nome do Monarca:")
    if st.button("CONFIRMAR") and nome:
        supabase.table("hunters").insert({"user_id": st.session_state.user_id, "nome": nome, "level": 1, "exp": 0, "gold": 0, "rank": "E"}).execute()
        st.rerun()
    st.stop()

u_id = hunter['user_id']
# --- SIDEBAR ---
st.sidebar.title("🌑 STATUS")
st.sidebar.subheader(f"[{obter_titulo(hunter['level'])}]")
st.sidebar.markdown(f"**NOME:** {hunter['nome']} | **LVL:** {hunter['level']}")
st.sidebar.metric("OURO", f"{hunter['gold']} G")

# --- ABAS ---
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests")
    c1, c2 = st.columns([3, 1])
    m_txt = c1.text_input("Missão:")
    r_sel = c2.selectbox("Rank:", ["E", "D", "C", "B", "A", "S"])
    recs = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}

    if st.button("REGISTRAR"):
        if m_txt:
            # Enviando a recompensa para a coluna que você criou no SQL Editor
            supabase.table("active_quests").insert({"user_id": u_id, "missao": f"[{r_sel}] {m_txt}", "recompensa": recs[r_sel]}).execute()
            st.rerun()

    st.divider()
    qs = supabase.table("active_quests").eq("user_id", u_id).execute()
    for q in qs.data:
        col1, col2 = st.columns([4, 1])
        col1.info(q['missao'])
        if col2.button("CONCLUIR", key=q['id']):
            g = q.get('recompensa', 20)
            # Atualiza Hunter
            supabase.table("hunters").update({"gold": hunter['gold']+g, "exp": hunter['exp']+(g//2)}).eq("user_id", u_id).execute()
            # Gera "Alma" para o Arise
            supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
            # Deleta Quest
            supabase.table("active_quests").delete().eq("id", q['id']).execute()
            st.rerun()

with t_a:
    st.header("Arise")
    hists = supabase.table("shadow_history").eq("user_id", u_id).execute()
    if not hists.data:
        st.write("Sem almas disponíveis. Complete quests primeiro!")
    for h in hists.data:
        st.warning(f"Alma disponível: {h['origem']}")
        n_som = st.text_input("Nome da Sombra:", key=f"s_{h['id']}")
        if st.button("EXTRAIR", key=f"b_{h['id']}") and n_som:
            supabase.table("army").insert({"user_id": u_id, "nome": n_som, "origem": h['origem']}).execute()
            supabase.table("shadow_history").delete().eq("id", h['id']).execute()
            st.success("Erga-se!")
            st.rerun()

with t_l: st.write("Loja em breve...")
with t_i:
    st.header("Exército")
    army = supabase.table("army").eq("user_id", u_id).execute()
    for s in army.data: st.write(f"🌑 {s['nome']} ({s['origem']})")
