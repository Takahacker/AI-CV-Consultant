import streamlit as st
from pypdf import PdfReader

from graph.workflow import cv_graph

st.set_page_config(
    page_title="AI CV Consultant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    h1, h2, h3, h4 {
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.01em;
    }
    h1 { font-size: 2.1rem; margin-bottom: 0.25rem; }
    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .section-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .stButton > button {
        background: #0f172a;
        color: #ffffff;
        border: none;
        padding: 0.65rem 1.4rem;
        font-weight: 600;
        font-size: 0.95rem;
        border-radius: 8px;
        transition: background 0.15s ease, transform 0.05s ease;
    }
    .stButton > button:hover {
        background: #1e293b;
        color: #ffffff;
    }
    .stButton > button:active { transform: translateY(1px); }
    .stTextArea textarea {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        font-size: 0.92rem;
        border-radius: 8px;
    }
    .stRadio > div { gap: 0.5rem; }
    .score-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem 1rem;
        text-align: center;
    }
    .score-value {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
        margin: 0;
    }
    .score-label {
        color: #64748b;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 0.6rem;
    }
    .status-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        height: 100%;
    }
    .status-title { font-weight: 700; font-size: 1.1rem; color: #0f172a; margin-bottom: 0.25rem; }
    .status-text { color: #475569; font-size: 0.95rem; }
    .status-meta { color: #94a3b8; font-size: 0.8rem; margin-top: 0.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: #64748b;
        padding: 0.6rem 1rem;
    }
    .stTabs [aria-selected="true"] { color: #0f172a; }
    div[data-testid="stFileUploader"] section {
        border-radius: 8px;
        border-style: dashed;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


st.title("AI CV Consultant")
st.markdown(
    '<p class="app-subtitle">Avalie e adapte seu currículo a uma vaga específica com apoio de IA.</p>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Como você quer começar</div>', unsafe_allow_html=True)
mode = st.radio(
    "modo",
    options=["evaluate", "build"],
    format_func=lambda x: "Já tenho um currículo" if x == "evaluate" else "Construir do zero",
    horizontal=True,
    label_visibility="collapsed",
)

st.write("")
col_left, col_right = st.columns(2, gap="large")

with col_left:
    if mode == "evaluate":
        st.markdown('<div class="section-label">Seu currículo</div>', unsafe_allow_html=True)
        source = st.radio(
            "origem",
            options=["text", "pdf"],
            format_func=lambda x: "Colar texto" if x == "text" else "Enviar PDF",
            horizontal=True,
            label_visibility="collapsed",
        )

        raw_input = ""
        if source == "pdf":
            uploaded = st.file_uploader(
                "Selecione um arquivo PDF",
                type=["pdf"],
                label_visibility="collapsed",
            )
            if uploaded is not None:
                try:
                    raw_input = extract_pdf_text(uploaded)
                    if not raw_input:
                        st.warning("Não foi possível extrair texto deste PDF. Tente colar o texto manualmente.")
                    else:
                        st.success(f"PDF processado. {len(raw_input)} caracteres extraídos.")
                        with st.expander("Visualizar texto extraído"):
                            st.text(raw_input[:3000] + ("..." if len(raw_input) > 3000 else ""))
                except Exception as e:
                    st.error(f"Falha ao ler o PDF: {e}")
        else:
            raw_input = st.text_area(
                "cv_texto",
                height=380,
                placeholder="Nome, experiências, habilidades, formação acadêmica...",
                label_visibility="collapsed",
            )
    else:
        st.markdown('<div class="section-label">Sua trajetória profissional</div>', unsafe_allow_html=True)
        raw_input = st.text_area(
            "dump",
            height=430,
            placeholder=(
                "Descreva livremente sua experiência. Exemplo: 2 anos como desenvolvedor "
                "Python na empresa X, formado em Ciência da Computação, conhece React, Docker, SQL."
            ),
            label_visibility="collapsed",
        )

with col_right:
    st.markdown('<div class="section-label">Vaga desejada</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "vaga",
        height=430 if mode == "build" else 380,
        placeholder="Cole aqui a descrição completa: responsabilidades, requisitos, stack técnica...",
        label_visibility="collapsed",
    )

st.write("")
run = st.button("Analisar currículo", type="primary", use_container_width=True)

if run:
    if not raw_input.strip() or not job_description.strip():
        st.warning("Preencha o currículo e a descrição da vaga antes de continuar.")
    else:
        with st.spinner("Analisando. Isso pode levar alguns instantes."):
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

        st.divider()

        score = int(result.get("score", 0) or 0)
        if score >= 80:
            color = "#16a34a"
            status_title = "Forte match"
            status_text = "Seu currículo está bem alinhado com a vaga. Ajustes finos podem refinar ainda mais."
        elif score >= 60:
            color = "#d97706"
            status_title = "Match moderado"
            status_text = "O consultor reescreveu seu currículo para melhorar o alinhamento com a vaga."
        else:
            color = "#dc2626"
            status_title = "Requer reformulação"
            status_text = "Seu currículo precisa de ajustes significativos para esta vaga."

        c1, c2 = st.columns([1, 3], gap="large")
        with c1:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="score-value" style="color:{color};">{score}</div>
                    <div class="score-label">Score / 100</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            iterations = int(result.get("iterations", 0) or 0)
            meta_html = (
                f'<div class="status-meta">Iterações do consultor: {iterations}</div>'
                if iterations > 0
                else ""
            )
            st.markdown(
                f"""
                <div class="status-card">
                    <div class="status-title" style="color:{color};">{status_title}</div>
                    <div class="status-text">{status_text}</div>
                    {meta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        tab_report, tab_cv = st.tabs(["Relatório de análise", "Currículo revisado"])

        with tab_report:
            st.markdown(result.get("final_report", "") or "_Sem relatório gerado._")

        with tab_cv:
            revised = result.get("revised_cv", "") or ""
            if revised:
                st.markdown(revised)
                st.download_button(
                    label="Baixar currículo revisado",
                    data=revised,
                    file_name="cv_revisado.md",
                    mime="text/markdown",
                )
            else:
                st.info("Nenhum currículo revisado foi gerado.")
