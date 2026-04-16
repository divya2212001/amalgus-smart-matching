# 🪟 AmalGus – Smart Glass Product Discovery

AI-powered B2B/B2C marketplace prototype for the glass industry.  
Buyers describe their requirements in natural language and instantly get ranked, explainable product matches.

---

## Quick Start

### 1. Clone & enter the repo
```bash
git clone https://github.com/divya2212001/amalgus-smart-matching.git
cd amalgus-glass-discovery
```

### 2. Create virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Groq API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at https://console.groq.com

### 5. Run the app
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

---

## Project Structure

```
amalgus/
├── app.py               # Streamlit UI
├── matching_engine.py   # FAISS + Groq matching pipeline
├── products.py          # 15 mock glass & hardware products
├── requirements.txt
├── .env                 # (you create this – not committed)
└── README.md
```

---

## 🧠 How Intelligent Matching Works

Two-stage pipeline:

### Stage 1 – Semantic Retrieval (FAISS)
- Each product is converted into a rich text blob (name + category + description + specs + tags)
- Embedded using `all-MiniLM-L6-v2` (sentence-transformers, runs locally, free)
- Stored in a **FAISS IndexFlatIP** (cosine similarity via inner product on L2-normalised vectors)
- At query time, the buyer's text is embedded and the top 15 nearest neighbours are retrieved in milliseconds

### Stage 2 – LLM Re-ranking & Explanation (Groq)
- Top candidates + buyer query are sent to **Groq (llama-3.1-8b-instant)**
- Groq understands glass domain context: thickness configs (5+12+5), certifications (IS 2553, EN 12150), coatings (Low-E, hydrophobic), use-cases (balcony railing, facade, partition)
- Returns structured JSON with a **match score (0–100)** and a **natural language explanation** per product
- Results are displayed ranked with highlighted specs and visual score bars

### Why this hybrid?
- FAISS alone is fast but keyword-biased
- LLM alone is slow and expensive for large catalogs
- Together: FAISS narrows the search space cheaply → LLM provides nuanced, explainable ranking

---

## AI Tools Used

| Tool | How it helped |
|------|--------------|
| **Claude (claude.ai)** | Architected the full project, wrote all code, designed the UI CSS, created realistic mock product data |
| **Groq (llama3-8b-8192)** | Fast LLM inference for re-ranking and generating match explanations |
| **sentence-transformers** | Local embedding model (no API cost) for FAISS indexing |

---

## Tech Stack

- **Frontend**: Streamlit + custom CSS (DM Sans / DM Serif Display)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, free)
- **Vector DB**: `faiss-cpu` (in-memory, no server needed)
- **LLM**: Groq API – `llama-3.1-8b-instant` (fast, free tier available)
- **Language**: Python 3.11

---

## Mock Product Data

15 products across categories:
- Tempered Glass (6mm, 8mm, 12mm)
- Laminated Safety Glass (8.76mm, 10.38mm)
- Insulated Glass Units (5+12+5, 6+12+6 Low-E)
- Float Glass (4mm)
- Tinted / Reflective Glass (Bronze 6mm)
- Mirror Glass (5mm copper-free)
- Frosted / Decorative Glass
- Wired Fire-Rated Glass
- Window Systems (UPVC + IGU)
- Hardware (Spider fittings, Sealants)

---

## Key Assumptions & Trade-offs

| Assumption / Trade-off | Reason |
|------------------------|--------|
| FAISS in-memory (no persistence) | Sufficient for 15 products; production would use Pinecone/Weaviate |
| `llama-3.1-8b-instant` on Groq | Free tier, ~300 tok/s; production might use `mixtral` or `llama3-70b` for better accuracy |
| `all-MiniLM-L6-v2` embedding model | Fast, lightweight, good enough for domain; `bge-large` would be more accurate |
| Prices in INR/sqm | Realistic for Indian glass market; international units can be added |
| No auth/login | Prototype scope; production needs buyer/supplier accounts |

---

## Bonus Features Implemented

- **Sidebar filters**: category, max price, thickness — applied before LLM stage for efficiency
- **Example query buttons** in sidebar for quick demo
- **Visual match score bar** colour-coded (blue = high, amber = medium)
- **Glass-domain-aware prompting**: LLM system prompt explicitly handles IGU configs, certifications, use-cases
- **Fallback**: if Groq fails, FAISS scores are used directly — no crash

---

## Demo

> Run locally and try:
> - *"6mm tempered glass for office cabin partitions, clear, polished edges"*
> - *"Laminated safety glass for balcony railing, UV protected, high wind"*
> - *"Budget 4mm float glass, residential windows, bulk order"*
> - *"Insulated glass 5+12+5 energy efficient"*