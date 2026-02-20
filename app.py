import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

@st.cache_resource
def init_db():
    try:
        return create_client(st.secrets["SUPABASE_URL"].strip(), st.secrets["SUPABASE_KEY"].strip())
    except: return None

supabase = init_db()

# --- GERENCIAMENTO DE SESSÃO (A CHAVE PARA PARAR O ERRO) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Função para buscar dados e travar na sessão
def sincronizar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            st.session_state.hunter = res.data[0]
            return True
        return False
    except:
        return False

# Títulos
def obter_titulo(level):
    if level >= 50: return "Soberano das Sombras"
    if level >= 15: return "Monarca"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

# --- FLUXO DE SEGURANÇA ---
if 'hunter' not in st.session_state:
    if not sincronizar_dados():
        st.title("🌑 O DESPERTAR")
        nome_in = st.text_input("Seu nome de Caçador:")
        if st.button("CONFIRMAR"):
            if nome_in and supabase:
                supabase.table("hunters").insert({
                    "user_id": st.session_state.user_id, "nome": nome_in, 
                    "level": 1, "exp": 0, "gold": 0, "rank": "E"
                }).execute()
                sincronizar_dados()
                st.rerun()
        st.stop()

# Criamos variáveis locais CURTAS e SEGURAS a partir da sessão
# Isso impede o AttributeError de aparecer no meio do app
h = st.session_state.hunter
u_id = h.get('user_id')
h_nome = h.get('nome', 'Caçador')
h_lvl = h.get('level', 1)
h_gold = h.get('gold', 0)
h_rank = h.get('rank', 'E')

# --- SIDEBAR ---
st.sidebar.title("🌑 STATUS")
st.sidebar.subheader(f"[{obter_titulo(h_lvl)}]")
st.sidebar.markdown(f"**NOME:** {h_nome}")
st.sidebar.metric("OURO", f"{h_gold} G")

# --- ABAS ---
tab_q, tab_a, tab_l, tab_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with tab_q:
    st.header("Quests")
    col_m, col_r = st.columns([3, 1])
    m_txt = col_m.text_input("Nova Missão:", key="input_q")
    r_sel = col_r.selectbox("Rank:", ["E", "D", "C", "B", "A", "S"], key="input_r")
    recs = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}

    if st.button("REGISTRAR QUEST"):
        if m_txt and supabase:
            supabase.table("active_quests").insert({
                "user_id": u_id, "missao": f"[{r_sel}] {m_txt}", "recompensa": recs[r_sel]
            }).execute()
            st.rerun()

    st.divider()
    try:
        quests = supabase.table("active_quests").eq("user_id", u_id).execute()
        for q in quests.data:
            c1, c2 = st.columns([4, 1])
            c1.info(q['missao'])
            if c2.button("FINALIZAR", key=f"btn_{q['id']}"):
                recompensa = q.get('recompensa', 20)
                # Atualiza no banco
                supabase.table("hunters").update({
                    "gold": h_gold + recompensa, 
                    "exp": h.get('exp', 0) + (recompensa // 2)
                }).eq("user_id", u_id).execute()
                # Cria alma para Arise
                supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
                # Deleta quest
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                # Limpa sessão para forçar recarregamento dos novos dados
                del st.session_state.hunter
                st.rerun()
    except: st.write("Sincronizando quests...")

with tab_a:
    st.header("Arise")
    try:
        almas = supabase.table("shadow_history").eq("user_id", u_id).execute()
        if not almas.data: st.write("Nenhuma alma disponível.")
        for a in almas.data:
            st.warning(f"Alma: {a['origem']}")
            nome_s = st.text_input("Nome da Sombra:", key=f"s_{a['id']}")
            if st.button("ARISE", key=f"arise_{a['id']}"):
                if nome_s:
                    supabase.table("army").insert({"user_id": u_id, "nome": nome_s, "origem": a['origem']}).execute()
                    supabase.table("shadow_history").delete().eq("id", a['id']).execute()
                    del st.session_state.hunter
                    st.rerun()
    except: st.write("Aguardando almas...")

with tab_i:
    st.header("Exército")
    try:
        exercito = supabase.table("army").eq("user_id", u_id).execute()
        for s in exercito.data:
            st.write(f"🌑 **{s['nome']}** ({s['origem']})")
    except: pass
