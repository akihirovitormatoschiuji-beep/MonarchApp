import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DE UI ---
st.set_page_config(page_title="MONARCH SYSTEM", page_icon="⚔️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161B22; border-radius: 5px; color: white; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #6272A4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
conn = sqlite3.connect('monarch_v1.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS player 
             (level INTEGER, exp INTEGER, gold INTEGER, rank TEXT, titulo TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS custom_quests 
             (id INTEGER PRIMARY KEY, nome TEXT, xp INTEGER, diff TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS registry_hunters 
             (id INTEGER PRIMARY KEY, nome TEXT, rank TEXT, obs TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS shadows (nome TEXT, classe TEXT)''')

if c.execute("SELECT count(*) FROM player").fetchone()[0] == 0:
    c.execute("INSERT INTO player VALUES (1, 0, 0, 'E', 'Desperto')")
conn.commit()

# --- CARREGAMENTO ---
lvl, exp, gold, rank_p, titulo = c.execute("SELECT * FROM player").fetchone()
xp_target = lvl * 100

# --- INTERFACE LATERAL ---
st.sidebar.title(f"🌑 {titulo}")
st.sidebar.markdown(f"### **RANK {rank_p}**")
st.sidebar.metric("Nível", lvl, f"{exp}/{xp_target} XP")
st.sidebar.metric("Gold", f"{gold} G")
st.sidebar.divider()

# --- CONTEÚDO ---
tab1, tab2, tab3 = st.tabs(["🎯 MISSÕES", "🏛️ ASSOCIAÇÃO", "🎒 EXÉRCITO"])

with tab1:
    st.header("🎯 Central de Missões")
    
    with st.expander("➕ CRIAR NOVA MISSÃO"):
        n_q = st.text_input("Nome da Missão")
        d_q = st.select_slider("Dificuldade", options=["E", "D", "C", "B", "A", "S"])
        xp_reward = {"E": 20, "D": 60, "C": 150, "B": 400, "A": 800, "S": 2000}
        if st.button("PUBLICAR NO SISTEMA"):
            if n_q:
                c.execute("INSERT INTO custom_quests (nome, xp, diff) VALUES (?, ?, ?)", (n_q, xp_reward[d_q], d_q))
                conn.commit()
                st.rerun()

    st.subheader("Quests Ativas")
    active_qs = c.execute("SELECT * FROM custom_quests").fetchall()
    for qid, qn, qxp, qd in active_qs:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**[{qd}]** {qn} | `+{qxp} XP`")
        if col2.button("FINALIZAR", key=f"finish_{qid}"):
            c.execute("UPDATE player SET exp=exp+?, gold=gold+? WHERE rowid=1", (qxp, qxp//2))
            c.execute("DELETE FROM custom_quests WHERE id=?", (qid,))
            conn.commit()
            st.balloons()
            st.rerun()

with tab2:
    st.header("🏛️ Associação de Caçadores")
    st.write("Cadastre as pessoas que te inspiram ou seus rivais para monitorar o ranking.")
    
    with st.expander("👤 CADASTRAR CAÇADOR"):
        h_nome = st.text_input("Nome do Caçador")
        h_rank = st.selectbox("Rank do Indivíduo", ["E", "D", "C", "B", "A", "S", "Nacional"])
        h_obs = st.text_area("Especialidade/Observação")
        if st.button("REGISTRAR CAÇADOR"):
            if h_nome:
                c.execute("INSERT INTO registry_hunters (nome, rank, obs) VALUES (?, ?, ?)", (h_nome, h_rank, h_obs))
                conn.commit()
                st.rerun()
    
    hunters = c.execute("SELECT nome, rank, obs FROM registry_hunters").fetchall()
    if hunters:
        df = pd.DataFrame(hunters, columns=["Nome", "Rank", "Observação"])
        st.table(df)
    else:
        st.info("Nenhum caçador registrado na sua rede.")

with tab3:
    st.header("🌑 Exército de Sombras")
    s_name = st.text_input("Extrair sombra de um desafio concluído:")
    if st.button("ERGA-SE"):
        if s_name:
            c.execute("INSERT INTO shadows VALUES (?, 'Soldado')", (s_name,))
            conn.commit()
            st.success(f"A sombra de {s_name} foi extraída.")
    
    st.subheader("Sombras Sob seu Comando")
    shadow_list = c.execute("SELECT * FROM shadows").fetchall()
    for sn, sc in shadow_list:
        st.write(f"👤 {sn} ({sc})")

# --- LEVEL UP ---
if exp >= xp_target:
    c.execute("UPDATE player SET level=level+1, exp=0 WHERE rowid=1")
    conn.commit()
    st.rerun()