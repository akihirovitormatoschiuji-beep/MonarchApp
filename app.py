import streamlit as st
from supabase import create_client
import uuid

# --- INICIALIZAÇÃO SEGURA ---
@st.cache_resource
def init_db():
    try:
        # Tenta pegar as chaves. Se falhar, avisa o usuário.
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url.strip(), key.strip())
    except Exception as e:
        return None

supabase = init_db()

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- FUNÇÃO PARA CARREGAR OU CRIAR CAÇADOR ---
def obter_cacador():
    if not supabase:
        return None
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            return res.data[0]
        return "novo" # Sinaliza que precisa de um nome
    except:
        return None

hunter_data = obter_cacador()

# --- INTERFACE DE BOAS-VINDAS / NOME ---
if hunter_data is None:
    st.error("⚠️ Erro de Conexão com a Associação. Verifique se a URL nos Secrets termina em .co e não .com")
    st.stop()

if hunter_data == "novo":
    st.title("🌑 O DESPERTAR")
    st.write("O Sistema não encontrou seu registro. Como a história deve te chamar?")
    nome_input = st.text_input("Digite seu nome de Caçador:")
    
    if st.button("CONFIRMAR DESPERTAR"):
        if nome_input:
            novo_registro = {
                "user_id": st.session_state.user_id,
                "nome": nome_input,
                "level": 1,
                "exp": 0,
                "gold": 0,
                "rank": "E"
            }
            supabase.table("hunters").insert(novo_registro).execute()
            st.success(f"Registro Concluído, {nome_input}!")
            st.rerun()
    st.stop()

# --- SE CHEGOU AQUI, O NOME ESTÁ OK ---
st.sidebar.title("PAINEL DO CAÇADOR")
st.sidebar.markdown(f"**NOME:** {hunter_data['nome']}")
st.sidebar.markdown(f"**RANK:** {hunter_data['rank']}")
# Barra de XP (Proteção contra nível 0)
lvl = hunter_data['level'] if hunter_data['level'] > 0 else 1
prox_lvl = lvl * 100
st.sidebar.progress(min(hunter_data['exp'] / prox_lvl, 1.0))
