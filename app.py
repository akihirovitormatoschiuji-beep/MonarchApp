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

# Garante um ID estável para a sessão
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- LÓGICA DE TÍTULOS ---
def obter_titulo(level):
    if level >= 50: return "Soberano das Sombras"
    if level >= 30: return "Monarca"
    if level >= 15: return "Candidato a Rei"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

# --- CARREGAR DADOS ---
def carregar_dados():
    if not supabase: return None
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        return res.data[0] if res.data else None
    except: return None

hunter = carregar_dados()

# --- TELA DE REGISTRO ---
if not hunter:
    st.title("🌑 O DESPERTAR")
    nome_in = st.text_input("Como o Sistema deve te chamar?")
    if st.button("CONFIRMAR DESPERTAR"):
        if nome_in and supabase:
            supabase.table("hunters").insert({
                "user_id": st.session_state.user_id, "nome": nome_in, 
                "level": 1, "exp": 0, "gold": 0, "rank": "E"
            }).execute()
            st.rerun()
    st.stop()

# --- SEGURANÇA DE DADOS ---
# Usamos o ID que vem do banco ou o da sessão para evitar o AttributeError
u_id = hunter.get('user_id', st.session_state.user_id)
titulo_atual = obter_titulo(hunter.get('level', 1))

st.sidebar.title("🌑 STATUS DO MONARCA")
st.sidebar.subheader(f"[{titulo_atual}]")
st.sidebar.markdown(f"**NOME:** {hunter.get('nome')}")
st.sidebar.markdown(f"**NÍVEL:** {hunter.get('level', 1)} | **RANK:** {hunter.get('rank')}")
st.sidebar.metric("OURO", f"{hunter.get('gold', 0)} G")

# --- SISTEMA DE ABAS ---
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests da Associação")
    c_q1, c_q2 = st.columns([3, 1])
    missao_txt = c_q1.text_input("Descrição do Desafio:", key="input_missao")
    rank_q = c_q2.selectbox("Rank:", ["E", "D", "C", "B", "A", "S"], key="rank_select")
    
    recompensas = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}
    
    if st.button("REGISTRAR QUEST NO SISTEMA"):
        if missao_txt:
            try:
                supabase.table("active_quests").insert({
                    "user_id": u_id, 
                    "missao": f"[{rank_q}] {missao_txt}", 
                    "recompensa": recompensas[rank_q]
                }).execute()
                st.success("Quest registada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar quest: {e}")

    st.divider()
    # Listagem segura de quests
    try:
        res_qs = supabase.table("active_quests").eq("user_id", u_id).execute()
        for q in res_qs.data:
            col1, col2 = st.columns([4, 1])
            col1.info(q['missao'])
            if col2.button("CONCLUIR", key=f"btn_q_{q['id']}"):
                ganho = q.get('recompensa', 20)
                n_gold = hunter.get('gold', 0) + ganho
                n_exp = hunter.get('exp', 0) + (ganho // 2)
                n_lvl = hunter.get('level', 1)
                
                if n_exp >= (n_lvl * 100):
                    n_lvl += 1
                    n_exp = 0
                    st.balloons()
                
                supabase.table("hunters").update({"gold": n_gold, "exp": n_exp, "level": n_lvl}).eq("user_id", u_id).execute()
                supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()
    except: st.write("A carregar quests...")

with t_a:
    st.header("Arise (Extração de Sombras)")
    try:
        res_hist = supabase.table("shadow_history").eq("user_id", u_id).execute()
        if not res_hist.data:
            st.write("Vença quests para libertar almas.")
        for h in res_hist.data:
            st.warning(f"Alma: {h['origem']}")
            nome_sombra = st.text_input("Nome da Sombra:", key=f"name_{h['id']}")
            if st.button("ARISE", key=f"arise_{h['id']}"):
                if nome_sombra:
                    supabase.table("army").insert({"user_id": u_id, "nome": nome_sombra, "origem": h['origem']}).execute()
                    supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                    st.rerun()
                else: st.warning("Dê um nome à sua sombra.")
    except: st.write("O sistema Arise está a sincronizar...")

# Mantemos Loja e Inventário como antes, apenas com chaves seguras
with t_l:
    st.header("Loja Dimensional")
    if st.button("Comprar Poção (100G)", key="buy_pot"):
        if hunter.get('gold', 0) >= 100:
            supabase.table("hunters").update({"gold": hunter['gold'] - 100}).eq("user_id", u_id).execute()
            st.rerun()

with t_i:
    st.header("Exército de Sombras")
    try:
        res_army = supabase.table("army").eq("user_id", u_id).execute()
        for s in res_army.data:
            st.markdown(f"🌑 **{s['nome']}** — *{s['origem']}*")
    except: pass
