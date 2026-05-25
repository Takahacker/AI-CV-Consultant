import io
import re

import streamlit as st
from fpdf import FPDF
from pypdf import PdfReader

from graph.workflow import cv_graph

st.set_page_config(
    page_title="AI CV Consultant",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Reset & base ── */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', system-ui, sans-serif !important;
        background-color: #080808 !important;
        color: #e2e8f0 !important;
    }
    .stApp { background: #080808 !important; }
    .block-container {
        padding: 0 !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 99px; }

    /* ── Hero ── */
    .hero-wrap {
        position: relative;
        background: radial-gradient(ellipse at 60% 0%, #0c1a3a 0%, #0d0d0d 55%),
                    radial-gradient(ellipse at 10% 80%, #050d1f 0%, transparent 50%);
        padding: 4rem 2rem 3.5rem;
        overflow: hidden;
        border-radius: 0 0 20px 20px;
    }
    .hero-wrap::before {
        content: '';
        position: absolute; inset: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%233b82f6' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.6;
    }
    .hero-eyebrow {
        display: inline-flex; align-items: center; gap: 0.5rem;
        background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3);
        color: #60a5fa; font-size: 0.7rem; font-weight: 700;
        letter-spacing: 0.18em; text-transform: uppercase;
        padding: 0.35rem 0.9rem; border-radius: 99px; margin-bottom: 1.5rem;
    }
    .hero-eyebrow::before { content: '◈'; font-size: 0.9rem; }
    .hero-title {
        font-size: clamp(2.5rem, 5vw, 4.5rem);
        font-weight: 900; line-height: 1.0;
        color: #ffffff; letter-spacing: -0.04em;
        margin: 0 0 1rem; text-transform: uppercase;
    }
    .hero-accent { color: #3b82f6; }
    .hero-sub {
        color: #64748b; font-size: 1rem; max-width: 420px;
        line-height: 1.7; margin-bottom: 2.5rem;
    }

    /* ── Main content wrapper ── */
    .content-wrap { padding: 2.5rem 2rem; }

    /* ── Section labels ── */
    .section-label {
        font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em;
        text-transform: uppercase; color: #3b82f6;
        margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.6rem;
    }
    .section-label::after { content: ''; flex: 1; height: 1px; background: #1e1e1e; }

    /* ── Glass cards ── */
    .glass {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 20px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }

    /* ── Inputs ── */
    textarea,
    .stTextArea textarea,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="base-input"] textarea {
        background: #111318 !important;
        border: 1px solid #1e2130 !important;
        border-radius: 14px !important;
        color: #cbd5e1 !important;
        font-family: 'Inter', system-ui !important;
        font-size: 0.88rem !important;
        resize: vertical !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        caret-color: #3b82f6 !important;
    }
    textarea:focus,
    .stTextArea textarea:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
        outline: none !important;
        background: #13161f !important;
    }
    textarea::placeholder,
    .stTextArea textarea::placeholder { color: #2d3346 !important; }
    div[data-baseweb="textarea"],
    div[data-baseweb="base-input"] {
        background: #111318 !important;
        border-radius: 14px !important;
    }
    .stTextArea label { display: none !important; }

    /* ── Radio ── */
    .stRadio > div { gap: 0.5rem; }
    .stRadio label {
        color: #94a3b8 !important;
        font-size: 0.88rem !important;
    }
    .stRadio [data-testid="stMarkdownContainer"] p { color: #94a3b8 !important; }

    /* ── File uploader ── */
    div[data-testid="stFileUploader"] section {
        background: rgba(255,255,255,0.03) !important;
        border: 1px dashed rgba(255,255,255,0.1) !important;
        border-radius: 14px !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color: rgba(59,130,246,0.4) !important;
    }
    div[data-testid="stFileUploader"] * { color: #94a3b8 !important; }

    /* ── Primary button ── */
    .stButton > button {
        background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 60%, #60a5fa 100%) !important;
        color: #fff !important; border: none !important;
        padding: 0.85rem 2rem !important;
        font-weight: 800 !important; font-size: 0.95rem !important;
        border-radius: 14px !important; letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        box-shadow: 0 0 40px rgba(59,130,246,0.2), 0 4px 20px rgba(59,130,246,0.15) !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 60px rgba(59,130,246,0.35), 0 8px 30px rgba(59,130,246,0.25) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: rgba(255,255,255,0.04) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        font-weight: 600 !important; font-size: 0.85rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(59,130,246,0.1) !important;
        border-color: rgba(59,130,246,0.4) !important;
        color: #60a5fa !important;
    }

    /* ── Divider ── */
    hr { border-color: #1e1e1e !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 14px !important;
        padding: 5px !important; gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #4b5563 !important; font-weight: 600 !important;
        border-radius: 10px !important; font-size: 0.85rem !important;
        padding: 0.55rem 1.3rem !important; border: none !important;
        background: transparent !important;
        transition: all 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59,130,246,0.12) !important;
        color: #60a5fa !important;
        box-shadow: none !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

    /* ── Alerts ── */
    .stWarning, .stInfo, .stSuccess, .stError {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
        border-left: 3px solid #3b82f6 !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: #3b82f6 !important; }

    /* ── Markdown content ── */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f1f5f9 !important; }
    .stMarkdown p, .stMarkdown li { color: #94a3b8 !important; line-height: 1.8 !important; }
    .stMarkdown strong { color: #e2e8f0 !important; }
    .stMarkdown hr { border-color: #1e1e1e !important; }

    /* ── Score & result cards ── */
    .result-score-card {
        background: linear-gradient(135deg, #0f0f0f, #050d1f);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 24px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        box-shadow: 0 0 60px rgba(59,130,246,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .result-score-num {
        font-size: 5rem; font-weight: 900; line-height: 1;
        letter-spacing: -0.04em;
    }
    .result-score-denom { font-size: 1.8rem; color: #374151; font-weight: 400; }
    .result-score-lbl {
        font-size: 0.62rem; letter-spacing: 0.2em; text-transform: uppercase;
        color: #374151; margin-top: 0.5rem;
    }
    .result-score-bar {
        background: #1a1a1a; border-radius: 99px; height: 4px;
        margin-top: 1.5rem; overflow: hidden;
        border: 1px solid #222;
    }
    .result-score-fill { height: 100%; border-radius: 99px; }

    .result-status-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 24px;
        padding: 2rem 2.5rem;
        height: 100%;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }
    .result-badge {
        display: inline-block; padding: 0.3rem 0.9rem;
        border-radius: 99px; font-size: 0.68rem; font-weight: 700;
        letter-spacing: 0.12em; text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .result-title { font-size: 1.6rem; font-weight: 800; color: #f1f5f9; margin-bottom: 0.5rem; }
    .result-text { color: #64748b; font-size: 0.93rem; line-height: 1.7; }
    .result-meta {
        display: flex; align-items: center; gap: 0.5rem;
        color: #374151; font-size: 0.78rem;
        margin-top: 1.25rem; padding-top: 1.25rem;
        border-top: 1px solid #1a1a1a;
    }
    .result-meta-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #3b82f6; display: inline-block;
        box-shadow: 0 0 8px #3b82f6;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 10px !important;
        color: #64748b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── PDF generator ─────────────────────────────────────────────────────────────

def _ascii_safe(text: str) -> str:
    replacements = {
        "—": "-", "–": "-", "‒": "-",
        "'": "'", "'": "'", "‘": "'", "’": "'",
        "“": '"', "”": '"', """: '"', """: '"',
        "…": "...", "•": "*", "●": "*",
        "é": "e", "ã": "a", "ç": "c", "õ": "o", "à": "a",
        "ê": "e", "ó": "o", "ú": "u", "í": "i", "á": "a",
        "ô": "o", "â": "a", "ü": "u", "ñ": "n",
        "É": "E", "Ã": "A", "Ç": "C", "Õ": "O", "À": "A",
        "Ê": "E", "Ó": "O", "Ú": "U", "Í": "I", "Á": "A",
        "Ô": "O", "Â": "A", "Ü": "U", "Ñ": "N",
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_cv_pdf(md_text: str) -> bytes:
    L, R, T = 22, 22, 22
    pdf = FPDF()
    pdf.set_margins(L, T, R)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)
    W = pdf.w - L - R

    def cell(text: str, font: str, style: str, size: int,
             rgb: tuple, lh: float, indent: float = 0):
        pdf.set_font(font, style, size)
        pdf.set_text_color(*rgb)
        pdf.set_x(L + indent)
        w = W - indent
        safe = _ascii_safe(text)
        if safe.strip():
            pdf.multi_cell(w, lh, safe)
        pdf.set_x(L)

    for line in md_text.split("\n"):
        if line.startswith("# "):
            cell(line[2:], "Helvetica", "B", 22, (15, 23, 42), 11)
            pdf.ln(1)
        elif line.startswith("## "):
            pdf.ln(4)
            cell(line[3:].upper(), "Helvetica", "B", 11, (30, 58, 138), 8)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.4)
            pdf.line(L, pdf.get_y(), pdf.w - R, pdf.get_y())
            pdf.ln(3)
        elif line.startswith("### "):
            pdf.ln(2)
            cell(line[4:], "Helvetica", "B", 10, (15, 23, 42), 7)
        elif line.startswith("- ") or line.startswith("* "):
            cell("* " + line[2:], "Helvetica", "", 9, (71, 85, 105), 6, indent=5)
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            cell(line.strip("*"), "Helvetica", "B", 9, (51, 65, 85), 6)
        elif line.strip() == "":
            pdf.ln(2)
        else:
            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
            if cleaned.strip():
                cell(cleaned, "Helvetica", "", 9, (71, 85, 105), 6)

    return bytes(pdf.output())


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "\n\n".join(p.extract_text() or "" for p in reader.pages).strip()


def score_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    if score >= 60:
        return "#3b82f6"
    return "#ef4444"


# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-eyebrow">AI Career Platform</div>
        <div class="hero-title">
            CURRICULO<br>
            POWERED BY<br>
            <span class="hero-accent">AI INTELLIGENCE</span>
        </div>
        <div class="hero-sub">
            Uma plataforma que analisa seu currículo em tempo real,
            identifica gaps e reescreve para maximizar suas chances na vaga.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Main form ─────────────────────────────────────────────────────────────────

st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

st.markdown('<div class="section-label">Modo de operação</div>', unsafe_allow_html=True)
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
                "PDF",
                type=["pdf"],
                label_visibility="collapsed",
            )
            if uploaded:
                try:
                    raw_input = extract_pdf_text(uploaded)
                    if not raw_input:
                        st.warning("Não foi possível extrair texto deste PDF.")
                    else:
                        st.success(f"PDF processado — {len(raw_input):,} caracteres extraídos.")
                        with st.expander("Visualizar texto extraído"):
                            st.text(raw_input[:3000] + ("..." if len(raw_input) > 3000 else ""))
                except Exception as e:
                    st.error(f"Falha ao ler o PDF: {e}")
        else:
            raw_input = st.text_area(
                "cv_texto",
                height=360,
                placeholder="Nome, experiências, habilidades, formação acadêmica...",
                label_visibility="collapsed",
            )
    else:
        st.markdown('<div class="section-label">Sua trajetória profissional</div>', unsafe_allow_html=True)
        raw_input = st.text_area(
            "dump",
            height=420,
            placeholder="Descreva livremente sua experiência. Ex: 2 anos como dev Python na empresa X, formado em Ciência da Computação...",
            label_visibility="collapsed",
        )

with col_right:
    st.markdown('<div class="section-label">Vaga desejada</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "vaga",
        height=420 if mode == "build" else 360,
        placeholder="Cole aqui a descrição completa da vaga: responsabilidades, requisitos, stack técnica...",
        label_visibility="collapsed",
    )

st.write("")
run = st.button("◈  ANALISAR CURRÍCULO", type="primary", use_container_width=True)

# ── Results ───────────────────────────────────────────────────────────────────

if run:
    if not raw_input.strip() or not job_description.strip():
        st.warning("Preencha o currículo e a descrição da vaga antes de continuar.")
    else:
        with st.spinner("Processando com IA... Isso pode levar alguns instantes."):
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

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Resultado da análise</div>', unsafe_allow_html=True)

        score = int(result.get("score", 0) or 0)
        color = score_color(score)

        if score >= 80:
            badge_bg = "rgba(34,197,94,0.12)"
            badge_color = "#22c55e"
            status_title = "Forte match"
            status_text = "Seu currículo está bem alinhado com a vaga. Pequenos ajustes podem refiná-lo ainda mais."
        elif score >= 60:
            badge_bg = "rgba(59,130,246,0.12)"
            badge_color = "#3b82f6"
            status_title = "Match moderado"
            status_text = "O consultor de IA reescreveu seu currículo para melhorar o alinhamento com os requisitos da vaga."
        else:
            badge_bg = "rgba(239,68,68,0.12)"
            badge_color = "#ef4444"
            status_title = "Requer reformulação"
            status_text = "Seu currículo precisa de ajustes significativos para competir por esta vaga. O consultor gerou uma versão otimizada."

        c1, c2 = st.columns([1, 3], gap="large")

        with c1:
            st.markdown(
                f"""
                <div class="result-score-card">
                    <div class="result-score-num" style="color:{color};">{score}
                        <span class="result-score-denom">/100</span>
                    </div>
                    <div class="result-score-lbl">Compatibilidade</div>
                    <div class="result-score-bar">
                        <div class="result-score-fill"
                             style="width:{min(score,100)}%; background:{color};
                                    box-shadow: 0 0 12px {color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            iterations = int(result.get("iterations", 0) or 0)
            meta_html = (
                f'<div class="result-meta"><span class="result-meta-dot"></span>'
                f'{iterations} iterações do consultor de IA</div>'
                if iterations > 0 else ""
            )
            st.markdown(
                f"""
                <div class="result-status-card">
                    <div class="result-badge"
                         style="background:{badge_bg}; color:{badge_color};">{status_title}</div>
                    <div class="result-title">{status_title}</div>
                    <div class="result-text">{status_text}</div>
                    {meta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        tab_report, tab_cv = st.tabs(["◈  Relatório de análise", "◈  Currículo revisado"])

        with tab_report:
            st.markdown(result.get("final_report", "") or "_Sem relatório gerado._")

        with tab_cv:
            revised = result.get("revised_cv", "") or ""
            if revised.strip().startswith('{"type":') or revised.strip().startswith('{"status":'):
                revised = ""

            if revised:
                st.markdown(revised)
                st.markdown("<br>", unsafe_allow_html=True)
                dl1, dl2 = st.columns(2)
                with dl1:
                    st.download_button(
                        label="⬇  Baixar Markdown",
                        data=revised,
                        file_name="cv_revisado.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with dl2:
                    pdf_bytes = generate_cv_pdf(revised)
                    st.download_button(
                        label="⬇  Baixar PDF",
                        data=pdf_bytes,
                        file_name="cv_revisado.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.info("O agente não retornou um currículo revisado nesta execução.")

st.markdown("</div>", unsafe_allow_html=True)
