import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA ASSOCIAÇÃO ---
st.set_page_config(page_title="SISTEMA MONARCA", page_icon="🌑", layout="wide")

# Conexão segura
@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_db()

# Mantém a sessão do usuário
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- LÓGICA DE DADOS ---
def carregar_dados():
    padrao = {"user_id": st.session_state.user_id, "nome": None, "level": 1, "exp": 0, "gold": 0, "rank": "E", "titulo": "Candidato"}
    if not supabase: return padrao
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            dados = res.data[0]
            if dados.get('level', 0) <= 0: dados['level'] = 1
            return dados
        return padrao
    except:
        return padrao

hunter = carregar_dados()

# --- TELA DE DESPERTAR (DEFINIR NOME) ---
if hunter['nome'] is None:
    st.title("🌑 O DESPERTAR")
    st.write("O Sistema detectou um novo Monarca. Como a história deve te chamar?")
    
    novo_nome = st.text_input("Digite seu nome de Caçador:", placeholder="Ex: Sung Jin-Woo")
    
    if st.button("CONFIRMAR DESPERTAR"):
        if novo_nome:
            try:
                # Salva o novo caçador no banco de dados
                supabase.table("hunters").upsert({
                    "user_id": st.session_state.user_id,
                    "nome": novo_nome,
                    "level": 1,
                    "exp": 0,
                    "gold": 0,
                    "rank": "E",
                    "titulo": "Candidato"
                }).execute()
                st.success(f"Bem-vindo ao Sistema, {novo_nome}!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar na Associação: {e}")
        else:
            st.warning("Um Monarca precisa de um nome.")
    st.stop() # Interrompe o restante do app até ele ter um nome

# --- SE O JOGADOR JÁ TEM NOME, MOSTRA O SISTEMA ---
st.sidebar.title("PAINEL DO CAÇADOR")
st.sidebar.markdown(f"**NOME:** {hunter['nome']}")
st.sidebar.markdown(f"**RANK:** {hunter['rank']}")
st.sidebar.metric("GOLD", f"{hunter['gold']} G")

# Barra de XP
lvl = hunter['level']
xp_atual = hunter['exp']
proximo_lvl = lvl * 100
st.sidebar.write(f"XP: {xp_atual} / {proximo_lvl}")
st.sidebar.progress(min(xp_atual / proximo_lvl, 1.0))

# --- ABAS ---
t1, t2, t3, t4 = st.tabs(["⚔️ QUESTS", "🌑 ARISE", "💰 LOJA", "🎒 INVENTÁRIO"])

with t1:
    st.header("Associação de Caçadores: Quests")
    missao = st.text_input("Qual o seu desafio hoje?")
    if st.button("REGISTRAR QUEST"):
        if missao and supabase:
            supabase.table("active_quests").insert({"user_id": hunter['user_id'], "missao": missao}).execute()
            st.rerun()

    # Listagem de Quests
    try:
        qs = supabase.table("active_quests").eq("user_id", hunter['user_id']).execute()
        for q in qs.data:
            c1, c2 = st.columns([4, 1])
            c1.info(f"Quest: {q['missao']}")
            if c2.button("FINALIZAR", key=q['id']):
                # Lógica de Recompensa
                novo_xp = hunter['exp'] + 50
                novo_gold = hunter['gold'] + 20
                
                # Check de Level Up
                novo_lvl = hunter['level']
                if novo_xp >= proximo_lvl:
                    novo_lvl += 1
                    novo_xp = 0
                    st.balloons()

                supabase.table("hunters").update({"exp": novo_xp, "gold": novo_gold, "level": novo_lvl}).eq("user_id", hunter['user_id']).execute()
                supabase.table("shadow_history").insert({"user_id": hunter['user_id'], "origem": q['missao']}).execute()
                supabase.table("active_quests").delete().eq("id", q['id']).execute()
                st.rerun()
    except:
        st.write("Sem quests ativas.")
