import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Falha na conexão com o banco: {e}")
        return None

supabase = init_db()

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- LÓGICA DE TÍTULOS ---
def obter_titulo(level):
    level = int(level) if level else 1
    if level >= 50: return "Soberano das Sombras"
    if level >= 15: return "Monarca"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

# --- BUSCA DE DADOS ---
def carregar_hunter():
    if not supabase: return None
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Erro ao ler perfil: {e}")
        return None

hunter = carregar_hunter()

# --- TELA DE REGISTRO ---
if not hunter:
    st.title("🌑 O DESPERTAR")
    nome_in = st.text_input("Defina seu nome de Caçador:")
    if st.button("DESPERTAR"):
        if nome_in and supabase:
            supabase.table("hunters").insert({
                "user_id": st.session_state.user_id, "nome": nome_in,
                "level": 1, "exp": 0, "gold": 0, "rank": "E"
            }).execute()
            st.rerun()
    st.stop()

# --- VARIÁVEIS SEGURAS (GARANTE QUE RANK E TITULO APAREÇAM) ---
uid = hunter.get('user_id')
nome = hunter.get('nome', 'Caçador')
lvl = hunter.get('level', 1)
rank = hunter.get('rank', 'E')
gold = hunter.get('gold', 0)
titulo = obter_titulo(lvl)

# --- SIDEBAR FIXA ---
st.sidebar.title("🌑 STATUS")
st.sidebar.subheader(f"[{titulo}]")
st.sidebar.markdown(f"**NOME:** {nome}")
st.sidebar.markdown(f"**RANK:** {rank} | **NÍVEL:** {lvl}")
st.sidebar.metric("OURO", f"{gold} G")

# --- SISTEMA DE ABAS (SEM CARREGAMENTO INFINITO) ---
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests")
    c1, c2 = st.columns([3, 1])
    m_txt = c1.text_input("Descrição da Missão:", key="q_txt")
    r_sel = c2.selectbox("Rank:", ["E", "D", "C", "B", "A", "S"], key="q_rank")
    recs = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}

    if st.button("REGISTRAR"):
        if m_txt:
            try:
                supabase.table("active_quests").insert({
                    "user_id": uid, "missao": f"[{r_sel}] {m_txt}", "recompensa": recs[r_sel]
                }).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar quest: {e}")

    st.divider()
    try:
        qs = supabase.table("active_quests").eq("user_id", uid).execute()
        if not qs.data: st.write("Nenhuma quest ativa.")
        for q in qs.data:
            col_a, col_b = st.columns([4, 1])
            col_a.info(q['missao'])
            if col_b.button("CONCLUIR", key=f"q_{q['id']}"):
                rec = q.get('recompensa', 20)
                supabase.table("hunters").update({"gold": gold + rec, "exp": hunter.get('exp',0) + (rec // 2)}).eq("user_id", uid).execute()
                supabase.table("shadow_history").insert({"user_id": uid, "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar quests: {e}")

with t_a:
    st.header("Arise")
    try:
        almas = supabase.table("shadow_history").eq("user_id", uid).execute()
        if not almas.data: st.write("Sem almas para extrair.")
        for a in almas.data:
            st.warning(f"Alma: {a['origem']}")
            nome_s = st.text_input("Nome da Sombra:", key=f"s_{a['id']}")
            if st.button("ARISE", key=f"btn_{a['id']}"):
                if nome_s:
                    supabase.table("army").insert({"user_id": uid, "nome": nome_s, "origem": a['origem']}).execute()
                    supabase.table("shadow_history").delete().eq("id", a['id']).execute()
                    st.rerun()
    except Exception as e:
        st.error(f"Erro no sistema Arise: {e}")

with t_l:
    st.header("Loja Dimensional")
    st.write("Poção de Cura - 100 G")
    if st.button("COMPRAR POÇÃO"):
        if gold >= 100:
            supabase.table("hunters").update({"gold": gold - 100}).eq("user_id", uid).execute()
            st.success("Item comprado!")
            st.rerun()
        else: st.error("Ouro insuficiente.")

with t_i:
    st.header("Exército")
    try:
        army = supabase.table("army").eq("user_id", uid).execute()
        if not army.data: st.write("Seu exército está vazio.")
        for s in army.data:
            st.write(f"🌑 **{s['nome']}** — (Origem: {s['origem']})")
    except Exception as e:
        st.error(f"Erro ao carregar exército: {e}")
