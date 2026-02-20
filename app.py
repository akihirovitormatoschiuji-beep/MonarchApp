import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except:
        return None

supabase = init_db()

# Garante que o ID do usuário existe na sessão do navegador
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- FUNÇÃO PARA CARREGAR DADOS ---
def carregar_dados():
    if not supabase: return None
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

hunter = carregar_dados()

# --- TELA DE REGISTRO (O DESPERTAR) ---
if not hunter:
    st.title("🌑 O DESPERTAR")
    nome_in = st.text_input("Como o Sistema deve te chamar?")
    if st.button("CONFIRMAR DESPERTAR"):
        if nome_in and supabase:
            try:
                supabase.table("hunters").insert({
                    "user_id": st.session_state.user_id, 
                    "nome": nome_in, 
                    "level": 1, "exp": 0, "gold": 0, "rank": "E"
                }).execute()
                st.success("Sincronizando com a Associação...")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar: {e}")
    st.stop()

# --- SE CHEGOU AQUI, O HUNTER EXISTE ---
# Segurança: se hunter['user_id'] falhar, usamos st.session_state.user_id
u_id = hunter.get('user_id', st.session_state.user_id)

st.sidebar.title("🌑 STATUS")
st.sidebar.markdown(f"**NOME:** {hunter.get('nome', 'akz')}")
st.sidebar.markdown(f"**RANK:** {hunter.get('rank', 'E')}")
st.sidebar.metric("GOLD", f"{hunter.get('gold', 0)} G")

# Abas do Sistema
t_q, t_a, t_l, t_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t_q:
    st.header("Quests")
    missao = st.text_input("Qual o desafio de hoje?")
    if st.button("REGISTRAR QUEST") and missao:
        supabase.table("active_quests").insert({"user_id": u_id, "missao": missao}).execute()
        st.rerun()
    
    # Listar Quests com proteção de erro
    try:
        qs = supabase.table("active_quests").eq("user_id", u_id).execute()
        for q in qs.data:
            c1, c2 = st.columns([4,1])
            c1.info(f"Quest: {q['missao']}")
            if c2.button("CONCLUIR", key=f"q_{q['id']}"):
                n_xp = hunter.get('exp', 0) + 50
                n_gold = hunter.get('gold', 0) + 20
                supabase.table("hunters").update({"exp": n_xp, "gold": n_gold}).eq("user_id", u_id).execute()
                supabase.table("shadow_history").insert({"user_id": u_id, "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()
    except:
        st.write("Sem quests ativas.")

with t_a:
    st.header("Arise (Extração)")
    try:
        hist = supabase.table("shadow_history").eq("user_id", u_id).execute()
        if not hist.data: st.write("Vença quests para extrair sombras.")
        for h in hist.data:
            st.warning(f"Sombra disponível de: {h['origem']}")
            n_s = st.text_input("Nome da Sombra:", key=f"name_{h['id']}")
            if st.button("ARISE", key=f"b_{h['id']}"):
                if hunter.get('gold', 0) >= 100:
                    supabase.table("army").insert({"user_id": u_id, "nome": n_s, "origem": h['origem']}).execute()
                    supabase.table("hunters").update({"gold": hunter['gold']-100}).eq("user_id", u_id).execute()
                    supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                    st.rerun()
                else: st.error("Gold insuficiente (100G necessário).")
    except: pass

with t_l:
    st.header("Loja")
    if st.button("Comprar Poção (100 Gold)"):
        if hunter.get('gold', 0) >= 100:
            supabase.table("hunters").update({"gold": hunter['gold']-100}).eq("user_id", u_id).execute()
            st.success("Item comprado!")
            st.rerun()

with t_i:
    st.header("Exército de Sombras")
    try:
        exercito = supabase.table("army").eq("user_id", u_id).execute()
        for s in exercito.data:
            st.write(f"🌑 **{s['nome']}** (Sombra de: {s['origem']})")
    except:
        st.write("Exército vazio.")
