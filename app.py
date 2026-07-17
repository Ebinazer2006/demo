import streamlit as st
import requests
from groq import Groq
import pdfplumber
import plotly.express as px
import pandas as pd
import json

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="AI Resume Analyzer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS ---
style = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    header { background-color: transparent !important; }

    /* REMOVE ANCHOR PINS */
    .element-container:has(#stHeader) svg, 
    .stHeading a {
        display: none !important;
    }
    a.header-anchor { display: none !important; }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        min-width: 280px !important;
        transform: none !important;
        transition: none !important;
    }
    
    button[kind="headerNoPadding"] {
        display: none !important;
    }

    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 10px 30px 10px;
        font-weight: 800;
        font-size: 1.2rem;
        color: #0f172a;
    }

    .logo-box {
        background: #4f46e5;
        color: white;
        padding: 10px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-radius: 12px;
        color: #64748b !important;
        text-decoration: none !important;
        font-weight: 600;
        margin-bottom: 8px;
        transition: 0.2s ease;
    }

    .nav-item:hover {
        background-color: #f1f5f9;
        color: #4f46e5 !important;
    }

    .nav-active {
        background-color: #eef2ff !important;
        color: #4f46e5 !important;
    }

    div.stButton > button {
        background-color: #4f46e5;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 8px 20px;
        font-weight: 600;
        transition: 0.3s;
    }
    
    /* FIX FOR BUTTON HOVER WHITE-OUT */
    div.stButton > button:hover {
        background-color: #4338ca !important;
        color: white !important;
        border: none !important;
    }

    /* REDUCE RESULT TITLE FONT SIZE */
    .result-title {
        font-size: 1.8rem !important;
        font-weight: 700;
        margin: 0px !important;
    }

    .score-text {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    </style>
"""
st.markdown(style, unsafe_allow_html=True)

# --- 3. SIDEBAR UI ---
with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-logo">
            <div class="logo-box"><i class="fa-solid fa-robot"></i></div>
            AI MOCKSYSTEM
        </div>
        <p style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-left: 10px;">Main Menu</p>
        <a href="http://localhost/dashboard-ui/dashboard/dashboard.html" target="_self" class="nav-item">
            <i class="fa-solid fa-grip-vertical nav-icon"></i> Dashboard
        </a>
        <a href="#" class="nav-item nav-active">
            <i class="fa-solid fa-file-invoice nav-icon"></i> Resume Analyzer
        </a>
        <a href="http://localhost/dashboard-ui/dashboard/index.html" target="_self" class="nav-item logout-item">
            <i class="fa-solid fa-arrow-right-from-bracket nav-icon"></i> Logout
        </a>
    """, unsafe_allow_html=True)

# --- 4. DIRECT SUPABASE REST API INTEGRATION ---
def save_via_php(filename, result):
    url = "https://lxtzlijirubqqdutplnu.supabase.co/rest/v1/tbl_resume_analysis"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dHpsaWppcnVicXFkdXRwbG51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyMDAxMzIsImV4cCI6MjA5OTc3NjEzMn0.wzaKq0x1a6sFVa-Pngs4kq6mK5icbTXUk2kPRHFFe4M"
    
    ai_summary = result.get('summary', "Summary not generated")
    
    def db_format(item):
        if isinstance(item, list):
            return "||".join(item) if len(item) > 0 and isinstance(item[0], str) else json.dumps(item)
        return str(item)

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {
        "fld_user_id": st.session_state.get('user_id'),
        "fld_filename": filename,
        "fld_score": int(result.get('score', 0)),
        "fld_summary": ai_summary,
        "fld_strengths": db_format(result.get('strengths', [])),
        "fld_weaknesses": db_format(result.get('weaknesses', [])),
        "fld_improvements": db_format(result.get('improvements', [])),
        "fld_projects": json.dumps(result.get('projects', [])),
        "fld_internships": json.dumps(result.get('internships', [])),
        "fld_feedback": result.get('overall_feedback', '')
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        pass

# --- 5. AI LOGIC ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def analyze_resume(text):
    prompt = f"""
    Step 1: Determine if the following text is a professional resume/CV. 
    If it is NOT a resume (e.g., a recipe, a story, random notes, or empty), return exactly: {{"error": "invalid_file"}}

    Step 2: If it IS a resume, analyze it and return a valid JSON object. 
    NOTE: The "summary" MUST be a detailed professional narrative of at least 4-5 sentences (more than 2 lines of text).
    NOTE: Evaluate using high standards of Product Based Companies (PBC). 
    A score of 80+ should be rare and reserved for top-tier talent.

    JSON Structure:
    {{
        "candidate_name": "Full Name",
        "score": 0,
        "summary": "Detailed 4-5 sentence professional summary...",
        "strengths": ["list", "of", "5"],
        "weaknesses": ["list", "of", "5"],
        "improvements": ["3-5", "points"],
        "overall_feedback": "paragraph",
        "projects": [{{ "name": "Title", "description": "Details" }}],
        "internships": [{{ "company": "Name", "role": "Role" }}],
        "chart_data": {{ "Experience": 80, "Technical": 70, "Impact": 90, "Leadership": 60, "Organization": 85 }}
    }}

    Text: {text}
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

# --- 6. MAIN APP LOGIC ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get("user_id", "1")

if not st.session_state.get('analyzed', False):
    st.title("Resume Insights")
    st.write("Upload your PDF to see how your resume stacks up against AI standards.")
    
    uploaded_file = st.file_uploader("", type="pdf")
    if uploaded_file and st.button("Start Analysis", use_container_width=True):
        with st.spinner("Analyzing profile..."):
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    text = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                if not text.strip():
                    st.error("The uploaded PDF is empty or contains no readable text.")
                else:
                    result = analyze_resume(text)
                    if "error" in result:
                        st.error("Invalid File: Please upload a valid professional resume.")
                    else:
                        save_via_php(uploaded_file.name, result)
                        st.session_state.data = result
                        st.session_state.analyzed = True
                        st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")
else:
    data = st.session_state.data
    candidate_name = data.get('candidate_name', 'User')
    score = data.get('score', 0)
    
    # Determine Score Color
    if score >= 80:
        score_color = "#22c55e" # Green
    elif score >= 50:
        score_color = "#eab308" # Yellow
    else:
        score_color = "#ef4444" # Red

    # HEADER WITH BUTTON ON RIGHT
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown(f'<p class="result-title">Analysis Results for {candidate_name}</p>', unsafe_allow_html=True)
        # CHANGED: Label from "PBC Match Score" to "Score"
        st.markdown(f'<p class="score-text">Score: <span style="color:{score_color};">{score}/100</span></p>', unsafe_allow_html=True)
    with col_btn:
        st.write("") # Alignment spacer
        if st.button("New Analysis", use_container_width=True):
            st.session_state.analyzed = False
            st.rerun()

    st.subheader("Professional Summary")
    st.info(data.get('summary', ''))
    
    st.divider()

    # PROJECTS AND INTERNSHIPS DISPLAYED SEPARATELY (Side-by-Side)
    col_proj, col_int = st.columns(2)
    with col_proj:
        st.subheader(" Projects")
        projects = data.get('projects', [])
        if projects:
            for p in projects:
                st.write(f"**{p.get('name')}**")
                st.write(f"{p.get('description')}")
                st.write("")
        else:
            st.write("No projects identified.")

    with col_int:
        st.subheader(" Internships")
        internships = data.get('internships', [])
        if internships:
            for i in internships:
                st.write(f"**{i.get('company')}**")
                st.write(f"*{i.get('role')}*")
                st.write("")
        else:
            st.write("No internships identified.")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ Strengths")
        for s in data.get('strengths', []): st.write(f"- {s}")
    with col2:
        st.warning("⚠️ Areas for Improvement")
        for w in data.get('weaknesses', []): st.write(f"- {w}")

    # SUGGESTIONS TO IMPROVE SCORE
    st.write("") 
    st.subheader("💡 Suggestions to Improve Your Score")
    improvements = data.get('improvements', [])
    if improvements:
        for imp in improvements:
            st.write(f" {imp}")
    else:
        st.write("Your resume is already highly optimized!")
    
    st.divider()
    chart_dict = data.get('chart_data', {})
    if chart_dict:
        df = pd.DataFrame({"Metric": list(chart_dict.keys()), "Score": list(chart_dict.values())})
        fig = px.bar(df, x="Score", y="Metric", orientation='h', color="Metric")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
