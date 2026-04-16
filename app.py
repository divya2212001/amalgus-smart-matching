import streamlit as st
import json
import numpy as np
from matching_engine import MatchingEngine

st.set_page_config(
    page_title="AmalGus - Smart Glass Discovery",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling the app
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.hero-title{
    font-family: 'DM Serif Display', serif;
    font-size: 3.3rem;
    line-height: 1.15;
    color: #ffffff !important;
    margin-bottom: 0.8rem;
    letter-spacing: -0.5px;
    font-weight: 700;
}

.hero-title span{
    background: linear-gradient(135deg,#38b2d8,#60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub{
    color: #d6e4ff !important;
    font-size: 1.15rem;
    font-weight: 400;
    line-height: 1.8;
    max-width: 850px;
    margin-top: 0.4rem;
    margin-bottom: 2rem;
}

.hero-highlight{
    color: #38b2d8;
    font-weight: 600;
}

.badge {
    display: inline-block;
    background: #e8f4f8;
    color: #1a6fa0;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 4px;
}
.score-bar-wrap {
    background: #e8edf2;
    border-radius: 999px;
    height: 8px;
    margin: 6px 0 12px;
}
.score-bar {
    border-radius: 999px;
    height: 8px;
    background: linear-gradient(90deg, #1a6fa0, #38b2d8);
}
.card {
    background: #ffffff;
    border: 1.5px solid #dde6ef;
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(10,22,40,0.06);
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 6px 24px rgba(10,22,40,0.12); }
.rank-pill {
    background: #0a1628;
    color: #fff;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 8px;
}
.product-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #0a1628;
}
.supplier-tag {
    color: #1a6fa0;
    font-size: 0.85rem;
    font-weight: 500;
}
.price-tag {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0a1628;
}
.why-box {
    background: #f0f7fc;
    border-left: 3px solid #38b2d8;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.88rem;
    color: #2d4a60;
    margin-top: 10px;
}
.divider { border: none; border-top: 1.5px solid #e4eaf0; margin: 10px 0; }
.stButton>button {
    background: linear-gradient(135deg, #0a1628 0%, #1a6fa0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 32px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: 0.3px;
    width: 100%;
    transition: opacity 0.2s;
}
.stButton>button:hover { opacity: 0.88; }
.sidebar-label {
    font-weight: 600;
    color: #38bdf8;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# Init engine and load data (cached to speed up reloads)
@st.cache_resource(show_spinner="Building index…")
def load_engine():
    return MatchingEngine()

engine = load_engine()

# Heaader and query input
col_logo, col_space = st.columns([1, 3])
with col_logo:
    st.markdown("### 🪟 **AmalGus**")

st.markdown('<p class="hero-title">Find the Right Glass,<br><i>Instantly.</i></p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Describe what you need in plain language — our AI matches you with the best suppliers.</p>', unsafe_allow_html=True)

# Sidebar filters 
with st.sidebar:
    st.markdown("## Filters")
    st.markdown('<p class="sidebar-label">Category</p>', unsafe_allow_html=True)
    categories = ["All"] + sorted({p["category"] for p in engine.products})
    selected_cat = st.selectbox("", categories, label_visibility="collapsed")

    st.markdown('<p class="sidebar-label">Max Price (₹/sqm or unit)</p>', unsafe_allow_html=True)
    max_price = st.slider("", 100, 10000, 10000, step=100, label_visibility="collapsed")

    st.markdown('<p class="sidebar-label">Thickness (mm)</p>', unsafe_allow_html=True)
    thickness_opts = ["Any", "4mm", "5mm", "6mm", "8mm", "10mm", "12mm", "5+12+5", "6+12+6"]
    selected_thickness = st.selectbox("", thickness_opts, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### Example queries")
    examples = [
        "6mm tempered glass for office partitions, clear, polished edges",
        "Laminated safety glass for balcony railing, 8-10mm, UV protected",
        "Budget 4mm float glass for residential windows, bulk order",
        "Insulated glass unit 5+12+5 for energy-efficient windows",
        "Bronze tinted glass for facade cladding, heat reflective",
    ]
    for ex in examples:
        if st.button(ex[:55] + ("…" if len(ex) > 55 else ""), key=ex):
            st.session_state["query_prefill"] = ex

# Query box
prefill = st.session_state.get("query_prefill", "")
query = st.text_area(
    "**Describe your requirement:**",
    value=prefill,
    height=100,
    placeholder="e.g. I need 6mm clear tempered glass for office cabin partitions, size around 2m × 1.2m, polished edges, CE certified…"
)

search_clicked = st.button("Find Best Matches")

# Results
if search_clicked and query.strip():
    # Build filter dict
    filters = {}
    if selected_cat != "All":
        filters["category"] = selected_cat
    if max_price < 10000:
        filters["max_price"] = max_price
    if selected_thickness != "Any":
        filters["thickness"] = selected_thickness

    # Warn user if filters are active (might conflict with query)
    if filters:
        active = []
        if "category" in filters: active.append(f"Category = **{filters['category']}**")
        if "max_price" in filters: active.append(f"Max price = **₹{filters['max_price']}**")
        if "thickness" in filters: active.append(f"Thickness = **{filters['thickness']}**")
        if active:
            st.info(f"Active filters: {' | '.join(active)}  \n_Tip: Set filters to 'All' / 'Any' if you get no results._")

    with st.spinner("Matching products with Groq + FAISS…"):
        results = engine.search(query, filters=filters, top_k=5)

    if not results:
        st.warning("No products matched. Try setting **Category → All** and **Thickness → Any** in the sidebar, then search again.")
    else:
        st.markdown(f"### Top {len(results)} Matches")
        st.caption(f"Query: *{query[:120]}{'…' if len(query)>120 else ''}*")
        st.markdown("---")

        for i, r in enumerate(results, 1):
            p = r["product"]
            score = r["score"]
            explanation = r["explanation"]
            bar_color = "#38b2d8" if score >= 70 else "#f0a030" if score >= 40 else "#e05050"

            st.markdown(f"""
            <div class="card">
                <div>
                    <span class="rank-pill">#{i}</span>
                    <span class="product-name">{p['name']}</span>
                    &nbsp;&nbsp;
                    <span class="badge">{p['category']}</span>
                </div>
                <div style="margin-top:6px;">
                    <span class="supplier-tag">{p['supplier']}</span>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span class="price-tag">₹{p['price_inr']:,} / {p['price_unit']}</span>
                </div>
                <hr class="divider"/>
                <div style="font-size:0.9rem; color:#3a4f62; margin-bottom:8px;">{p['description']}</div>
                <div>
                    {''.join(f'<span class="badge">{spec}</span>' for spec in p['key_specs'])}
                </div>
                <div style="margin-top:10px; font-size:0.8rem; color:#5a7080; font-weight:600;">
                    MATCH SCORE &nbsp;
                    <span style="font-size:1rem; color:#0a1628; font-weight:700;">{score}%</span>
                </div>
                <div class="score-bar-wrap">
                    <div class="score-bar" style="width:{score}%; background: linear-gradient(90deg, #1a6fa0, {'#38b2d8' if score>=70 else '#f0a030'});"></div>
                </div>
                <div class="why-box">{explanation}</div>
            </div>
            """, unsafe_allow_html=True)

elif search_clicked:
    st.warning("Please enter a requirement before searching.")


st.markdown("---")
st.caption("AmalGus Marketplace · AI-Powered Glass Discovery · Prototype v1.0")