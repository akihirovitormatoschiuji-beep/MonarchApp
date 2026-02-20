import streamlit as st
from supabase import create_client
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑", layout="wide")

# --- ESTILO VISUAL SOLO LEVELING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stButton>button { width: 100%; background-color: #1f6feb; color: white; border-radius: 5px; }
    .shadow-card { background-color: #1C2128; border: 1px solid #7928CA; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_db()

# --- FUNÇÕES DE LÓGICA ---
def carregar_player():
    try:
        res = supabase.table("player").select("*").limit(1).execute()
        if res.data: return res.data[0]
        return {"level": 1, "exp": 0, "rank": "E", "gold": 0, "titulo": "Nenhum", "id": 1}
    except:
        return {"level": 1, "exp": 0, "rank": "E", "gold": 0, "titulo": "Nenhum", "id": 1}

# --- INTERFACE LATERAL (STATUS) ---
if supabase:
    player = carregar_player()
    
    st.sidebar.title("🌑 SISTEMA MONARCA")
    st.sidebar.image("https://i.pinimg.com/originals/82/8b/4b/828b4b3b2b1b3b3b3b3b3b3b3b3b3b3b.jpg", width=150) # Link de exemplo
    st.sidebar.markdown(f"### **{st.session_state.get('user_name', 'Sung Jin-Woo')}**")
    st.sidebar.markdown(f"**TÍTULO:** `{player.get('titulo', 'O Desperto')}`")
    st.sidebar.divider()
    
    st.sidebar.metric("NÍVEL", player['level'])
    st.sidebar.metric("RANK", player['rank'])
    st.sidebar.metric("GOLD", f"{player['gold']} G")
    
    xp_prox_lvl = player['level'] * 100
    progresso_xp = min(player['exp'] / xp_prox_lvl, 1.0)
    st.sidebar.write(f"XP: {player['exp']} / {xp_prox_lvl}")
    st.sidebar.progress(progresso_xp)

    # --- ABAS PRINCIPAIS ---
    tab1, tab2, tab3 = st.tabs(["⚔️ Missões", "👤 Sombras", "🎖️ Inventário"])

    with tab1:
        st.header("Painel de Quests")
        with st.expander("➕ REGISTRAR NOVA MISSÃO"):
            nome_q = st.text_input("O que o Sistema exige?")
            if st.button("ACEITAR QUEST"):
                if nome_q:
                    supabase.table("custom_quests").insert({"nome": nome_q, "xp": 50}).execute()
                    st.success("Quest adicionada ao log.")
                    st.rerun()

        st.subheader("Quests Ativas")
        try:
            quests = supabase.table("custom_quests").select("*").execute()
            for q in quests.data:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**QUEST:** {q['nome']}  \n`Recompensa: +50 XP | +10 Gold`")
                if c2.button("CONCLUIR", key=f"q_{q['id']}"):
                    # Atualiza XP e Gold
                    novo_xp = player['exp'] + 50
                    novo_gold = player['gold'] + 10
                    novo_lvl = player['level']
                    if novo_xp >= xp_prox_lvl:
                        novo_lvl += 1
                        novo_xp = 0
                        st.balloons()
                    
                    supabase.table("player").update({"exp": novo_xp, "gold": novo_gold, "level": novo_lvl}).eq("id", player['id']).execute()
                    supabase.table("custom_quests").delete().eq("id", q['id']).execute()
                    st.rerun()
        except:
            st.info("Nenhuma quest no log.")

    with tab2:
        st.header("Manifestação de Sombras")
        st.write("Custo de Extração: `100 Gold`")
        if st.button("SURJA! (ERISE)"):
            if player['gold'] >= 100:
                sombras_possiveis = ["Igris", "Tank", "Iron", "Tusk", "Beru", "Greed"]
                nova_sombra = random.choice(sombras_possiveis)
                # Tenta salvar a sombra no banco
                try:
                    supabase.table("shadows").insert({"nome": nova_sombra}).execute()
                    supabase.table("player").update({"gold": player['gold'] - 100}).eq("id", player['id']).execute()
                    st.success(f"A sombra de {nova_sombra} foi extraída!")
                    st.rerun()
                except:
                    st.error("Tabela 'shadows' não encontrada no banco.")
            else:
                st.warning("Gold insuficiente para extração.")
        
        st.subheader("Seu Exército")
        try:
            minhas_sombras = supabase.table("shadows").select("*").execute()
            for s in minhas_sombras.data:
                st.markdown(f"<div class='shadow-card'>🌑 Sombra: <b>{s['nome']}</b></div>", unsafe_allow_html=True)
        except:
            st.write("O exército está vazio.")

    with tab3:
        st.header("Títulos e Equipamentos")
        titulos_disponiveis = ["Assassino de Lobos", "Monarca das Sombras", "Caminhante do Abismo"]
        for t in titulos_disponiveis:
            c1, c2 = st.columns([3, 1])
            c1.write(f"🎖️ {t}")
            if c2.button("EQUIPAR", key=t):
                supabase.table("player").update({"titulo": t}).eq("id", player['id']).execute()
                st.success(f"Título {t} equipado!")
                st.rerun()

else:
    st.error("Falha na conexão com o Sistema Central (Supabase).")