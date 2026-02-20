import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA ASSOCIAÇÃO ---
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

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .shadow-card { border-left: 5px solid #7928CA; background: #111; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS DO CAÇADOR ---
def carregar_dados():
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            d = res.data[0]
            if d.get('level', 0) <= 0: d['level'] = 1
            return d
        return None
    except:
        return None

hunter = carregar_dados()

# --- INTERFACE PRINCIPAL ---
if hunter:
    # Sidebar de Status
    st.sidebar.title("🌑 STATUS")
    st.sidebar.markdown(f"**NOME:** {hunter['nome']}")
    st.sidebar.markdown(f"**RANK:** {hunter['rank']}")
    st.sidebar.metric("GOLD", f"{hunter['gold']} G")
    
    prox_lvl = hunter['level'] * 100
    st.sidebar.write(f"XP: {hunter['exp']} / {prox_lvl}")
    st.sidebar.progress(min(hunter['exp'] / prox_lvl, 1.0))
    
    # Sistema de Abas Reinstalado
    tab_q, tab_a, tab_l, tab_i = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

    with tab_q:
        st.header("Quests da Associação")
        nova_q = st.text_input("Novo desafio:")
        if st.button("REGISTRAR"):
            supabase.table("active_quests").insert({"user_id": hunter['user_id'], "missao": nova_q}).execute()
            st.rerun()
        
        # Listar Quests Ativas
        qs = supabase.table("active_quests").eq("user_id", hunter['user_id']).execute()
        for q in qs.data:
            c1, c2 = st.columns([4,1])
            c1.info(q['missao'])
            if c2.button("CONCLUIR", key=q['id']):
                # Ganha recompensa
                n_xp = hunter['exp'] + 50
                n_gold = hunter['gold'] + 20
                n_lvl = hunter['level']
                if n_xp >= prox_lvl:
                    n_lvl += 1
                    n_xp = 0
                supabase.table("hunters").update({"exp": n_xp, "gold": n_gold, "level": n_lvl}).eq("user_id", hunter['user_id']).execute()
                supabase.table("shadow_history").insert({"user_id": hunter['user_id'], "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()

    with tab_a:
        st.header("Extração de Sombras (ARISE)")
        hist = supabase.table("shadow_history").eq("user_id", hunter['user_id']).execute()
        for h in hist.data:
            st.markdown(f"<div class='shadow-card'>Desafio: {h['origem']}</div>", unsafe_allow_html=True)
            nome_s = st.text_input("Dê um nome:", key=f"s_{h['id']}")
            if st.button("ARISE", key=f"btn_{h['id']}"):
                if hunter['gold'] >= 100:
                    supabase.table("army").insert({"user_id": hunter['user_id'], "nome": nome_s, "origem": h['origem']}).execute()
                    supabase.table("hunters").update({"gold": hunter['gold'] - 100}).eq("user_id", hunter['user_id']).execute()
                    supabase.table("shadow_history").delete().eq("id", h['id']).execute()
                    st.rerun()
                else: st.error("Gold insuficiente.")

    with tab_l:
        st.header("Mercado")
        itens = [{"n": "Poção", "p": 100}, {"n": "Chave", "p": 500}]
        for i in itens:
            c1, c2, c3 = st.columns(3)
            c1.write(i['n'])
            c2.write(f"{i['p']} G")
            if c3.button("COMPRAR", key=i['n']):
                if hunter['gold'] >= i['p']:
                    supabase.table("hunters").update({"gold": hunter['gold'] - i['p']}).eq("user_id", hunter['user_id']).execute()
                    st.success("Comprado!")
                    st.rerun()

    with tab_i:
        st.header("Seu Exército")
        exercito = supabase.table("army").eq("user_id", hunter['user_id']).execute()
        for s in exercito.data:
            st.write(f"🌑 **{s['nome']}** (Origem: {s['origem']})")

else:
    st
