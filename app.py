import streamlit as st
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="🌑")

# Tenta conectar e captura o erro exato
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro nos Secrets: {e}")
        return None

supabase = get_supabase()

# Identificador único do navegador
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- FUNÇÃO DE CARREGAMENTO ---
def carregar_dados():
    if not supabase:
        return {"nome": "ERRO DE CONEXÃO", "level": 1, "exp": 0, "rank": "N/A"}
    
    try:
        res = supabase.table("hunters").select("*").eq("user_id", st.session_state.user_id).execute()
        if res.data:
            return res.data[0]
        return "novo"
    except Exception as e:
        st.warning(f"Erro ao buscar caçador: {e}")
        return {"nome": "BANCO OFFLINE", "level": 1, "exp": 0, "rank": "N/A"}

hunter = carregar_dados()

# --- TELA DE REGISTRO (DEFINIR SEU NOME) ---
if hunter == "novo":
    st.title("🌑 O DESPERTAR")
    st.write("A Associação de Caçadores não encontrou seu registro.")
    
    nome_input = st.text_input("Como o Sistema deve te chamar?", placeholder="Digite seu nome aqui...")
    
    if st.button("REGISTRAR NA ASSOCIAÇÃO"):
        if nome_input:
            try:
                dados_novos = {
                    "user_id": st.session_state.user_id,
                    "nome": nome_input,
                    "level": 1,
                    "exp": 0,
                    "gold": 0,
                    "rank": "E",
                    "titulo": "Candidato"
                }
                supabase.table("hunters").insert(dados_novos).execute()
                st.success("Registro concluído! Recarregando...")
                st.rerun()
            except Exception as e:
                st.error(f"Não foi possível salvar seu nome: {e}")
                st.info("Dica: Verifique se você criou a tabela 'hunters' no SQL Editor do Supabase.")
        else:
            st.warning("Insira um nome para prosseguir.")
    st.stop()

# --- APP PRINCIPAL (SÓ APARECE APÓS O NOME SER SALVO) ---
st.sidebar.title("🌑 STATUS")
st.sidebar.markdown(f"**NOME:** {hunter.get('nome')}")
st.sidebar.markdown(f"**RANK:** {hunter.get('rank')}")
st.sidebar.metric("OURO", f"{hunter.get('gold', 0)} G")

st.title(f"Bem-vindo, {hunter.get('nome')}!")
st.write("O Sistema está operacional. Suas Quests aparecerão abaixo.")
