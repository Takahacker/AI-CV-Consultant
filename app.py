import streamlit as st
from graph.workflow import cv_graph

st.set_page_config(page_title="AI CV Consultant", page_icon="📄", layout="wide")

st.title("📄 AI CV Consultant")
st.caption("Construa ou adapte seu currículo com inteligência artificial.")

# --- Sidebar: modo de operação ---
with st.sidebar:
    st.header("Configuração")
    mode = st.radio(
        "O que você deseja fazer?",
        options=["evaluate", "build"],
        format_func=lambda x: "Tenho um CV — quero avaliar/adaptar" if x == "evaluate" else "Não tenho CV — quero construir do zero",
    )
    st.divider()
    st.caption("Powered by NVIDIA NIM + LangGraph + DeepAgents")

# --- Inputs principais ---
col1, col2 = st.columns(2)

with col1:
    if mode == "evaluate":
        st.subheader("Seu Currículo")
        raw_input = st.text_area(
            "Cole o texto do seu CV aqui",
            height=350,
            placeholder="Nome, experiências, habilidades, formação...",
        )
    else:
        st.subheader("Suas Informações")
        raw_input = st.text_area(
            "Descreva livremente sua trajetória profissional",
            height=350,
            placeholder="Ex: Trabalhou 2 anos como desenvolvedor Python na empresa X, formado em Ciência da Computação, conhece React, Docker, SQL...",
        )

with col2:
    st.subheader("Vaga Desejada")
    job_description = st.text_area(
        "Cole a descrição da vaga aqui",
        height=350,
        placeholder="Requisitos, responsabilidades, stack técnica...",
    )

# --- Botão de execução ---
run = st.button("🚀 Analisar", type="primary", use_container_width=True)

if run:
    if not raw_input.strip() or not job_description.strip():
        st.warning("Preencha os dois campos antes de continuar.")
    else:
        with st.spinner("Analisando... isso pode levar alguns instantes."):
            initial_state = {
                "mode": mode,
                "raw_input": raw_input,
                "job_description": job_description,
                "parsed_cv": {},
                "job_requirements": {},
                "score": 0,
                "gaps": [],
                "revised_cv": "",
                "iterations": 0,
                "final_report": "",
            }
            result = cv_graph.invoke(initial_state)

        # --- Resultados ---
        st.divider()

        # Score em destaque
        score = result["score"]
        col_score, col_status = st.columns([1, 3])
        with col_score:
            color = "green" if score >= 80 else "orange" if score >= 60 else "red"
            st.markdown(f"### Score\n# :{color}[{score}/100]")
        with col_status:
            if score >= 80:
                st.success("Forte match com a vaga. Pequenos ajustes podem turbinar ainda mais.")
            elif score >= 60:
                st.warning("Match moderado. O DeepAgent reescreveu seu CV para melhorar o alinhamento.")
            else:
                st.error("CV precisa de reformulação significativa para esta vaga.")

        st.divider()

        tab_report, tab_cv = st.tabs(["📊 Relatório de Análise", "📝 CV Revisado"])

        with tab_report:
            st.markdown(result["final_report"])

        with tab_cv:
            st.markdown(result["revised_cv"])
            st.download_button(
                label="⬇️ Baixar CV revisado (.md)",
                data=result["revised_cv"],
                file_name="cv_revisado.md",
                mime="text/markdown",
            )
