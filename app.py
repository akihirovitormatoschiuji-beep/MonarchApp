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
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- LÓGICA DE TÍTULOS ---
def obter_titulo(level):
    if level >= 50: return "Soberano das Sombras"
    if level >= 30: return "Monarca"
    if level >= 15: return "Candidato a Rei"
    if level >= 5: return "Caçador Veterano"
    return "Candidato"

# --- FUNÇÃO CARREGAR DADOS ---
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

# --- STATUS E TÍTULO ---
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
    st.header("Associação de Caçadores: Quests")
    c_q1, c_q2 = st.columns([3, 1])
    missao = c_q1.text_input("Descrição do Desafio:")
    rank_q = c_q2.selectbox("Rank da Quest:", ["E", "D", "C", "B", "A", "S"])
    
    recompensas = {"E": 20, "D": 50, "C": 100, "B": 250, "A": 600, "S": 2000}
    
    if st.button("REGISTRAR QUEST NO SISTEMA"):
        if missao:
            supabase.table("active_quests").insert({
                "user_id": u_id, "missao": f"[{rank_q}] {missao}", "recompensa": recompensas[rank_q]
            }).execute()
            st.success(f"Quest Rank {rank_q} registrada!")
            st.rerun()

    st.divider()
    qs = supabase.table("active_quests").eq("user_id", u_id).execute()
    for q in qs.data:
        col1, col2 = st.columns([4, 1])
        col1.info(q['missao'])
        if col2.button("CONCLUIR", key=f"q_{q['id']}"):
            ganho = q.get('recompensa', 20)
            n_gold = hunter.get('gold', 0) + ganho
            n_exp = hunter.get('exp', 0) + (ganho // 2)
            n_level = hunter.get('level', 1)
            
            # Lógica de Level Up
            if n_exp >= (n_level * 100):
                n_level += 1
                n_exp = 0
                st.balloons()
            
            supabase.table("hunters").update({"gold": n_gold, "exp": n_exp, "level": n_level}).eq("user_id", u_id).execute()
            supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
            supabase.table("active_quests").delete().eq("id", q['id']).execute()
            st.rerun()

with t_a:
    st.header("Arise (Extração de Sombras)")
    hist = supabase.table("shadow_history").eq("user_id", u_id).execute()
    if not hist.data:
        st.write("Não há almas para extrair. Conclua quests primeiro.")
    
    for h in hist.data:
        with st.container():
            st.markdown(f"**Alma Disponível:** {h['origem']}")
            nome_s = st.text_input("Dê um nome à sombra:", key=f"n_{h['id']}")
            if st.button("ARISE", key=f"b_{h['id']}"):
                if nome_s:
                    supabase.table("army").insert({"user_id": u_id, "nome": nome_s, "origem": h['origem']}).execute()
                    supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                    st.success(f"A sombra {nome_s} jurou lealdade!")
                    st.rerun()
                else: st.warning("A sombra precisa de um nome.")

with t_l:
    st.header("Loja Dimensional")
    itens = [
        {"nome": "Poção de Cura", "preco": 100, "desc": "Restaura o vigor."},
        {"nome": "Pedra de Rank Up", "preco": 5000, "desc": "Aumenta seu Rank de Caçador."}
    ]
    for item in itens:
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{item['nome']}**\n*{item['desc']}*")
        c2.write(f"{item['preco']} G")
        if c3.button("COMPRAR", key=item['nome']):
            if hunter.get('gold', 0) >= item['preco']:
                supabase.table("hunters").update({"gold": hunter['gold'] - item['preco']}).eq("user_id", u_id).execute()
                st.success(f"Adquiriu {item['nome']}!")
                st.rerun()
            else: st.error("Ouro insuficiente.")

with t_i:
    st.header("Exército de Sombras")
    army = supabase.table("army").eq("user_id", u_id).execute()
    for s in army.data:
        st.markdown(f"🌑 **{s['nome']}** — *Nascido de: {s['origem']}*")
