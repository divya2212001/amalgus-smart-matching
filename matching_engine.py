"""
matching_engine.py
──────────────────
Two-stage matching pipeline:
  Stage 1 - FAISS cosine-similarity retrieval using sentence-transformers embeddings
  Stage 2 - Groq LLM re-ranks & explains top candidates in natural language

No API key is hard-coded; reads GROQ_API_KEY from environment / .env
"""

from __future__ import annotations
import os, json, re, textwrap
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from products import PRODUCTS

load_dotenv()

# Helpers

def _product_text(p: dict) -> str:
    """Flat text representation of a product for embedding."""
    specs = " ".join(p["key_specs"])
    return f"{p['name']} {p['category']} {p['description']} {specs} {p['tags']}"


def _parse_groq_json(raw: str) -> list[dict]:
    """Extract JSON array from Groq response (handles markdown fences)."""
    raw = raw.strip()
    # strip ```json … ``` fences
    raw = re.sub(r"^```(?:json)?", "", raw).rstrip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find the first [...] block
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


# Engine 

class MatchingEngine:
    def __init__(self):
        self.products = PRODUCTS
        self._groq = Groq(api_key=os.environ["GROQ_API_KEY"])

        # Build FAISS index
        print("Loading embedding model…")
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [_product_text(p) for p in self.products]
        embeddings = self._model.encode(texts, normalize_embeddings=True).astype("float32")

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)   # inner-product == cosine on L2-normed vecs
        self._index.add(embeddings)
        print(f"FAISS index built: {len(self.products)} products, dim={dim}")

    def search(self, query: str, filters: dict | None = None, top_k: int = 5) -> list[dict]:
        """Return top_k ranked results with Groq explanations."""
        # Stage 1: FAISS retrieval (fetch 2× top_k to have headroom for filtering)
        q_emb = self._model.encode([query], normalize_embeddings=True).astype("float32")
        k_fetch = min(len(self.products), top_k * 3)
        scores, indices = self._index.search(q_emb, k_fetch)

        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            p = self.products[idx]

            # Apply hard filters — only when a real value was selected
            if filters:
                # Category filter (skip if "All")
                cat = filters.get("category")
                if cat and cat != "All" and p["category"] != cat:
                    continue

                # Price filter (skip if at slider max i.e. 10000)
                max_price = filters.get("max_price")
                if max_price and max_price < 10000 and p["price_inr"] > max_price:
                    continue

                # Thickness filter (skip if "Any")
                thickness = filters.get("thickness")
                if thickness and thickness != "Any":
                    t_str = thickness.replace("mm", "").strip()
                    # Compound config like "5+12+5" — match by IGU tag
                    if "+" in t_str:
                        config_tag = t_str.replace("+", "").replace(" ", "")
                        product_text = _product_text(p).lower()
                        if t_str not in product_text and config_tag not in product_text:
                            continue
                    else:
                        try:
                            target_mm = float(t_str)
                            # ±2mm tolerance to handle "8-10mm" range queries
                            if p["thickness_mm"] is not None and abs(p["thickness_mm"] - target_mm) > 2.0:
                                continue
                        except ValueError:
                            pass

            candidates.append({"product": p, "faiss_score": float(score)})

        if not candidates:
            return []

        # Trim to top_k candidates for LLM stage
        candidates = candidates[:top_k + 2]
        return self._groq_rerank(query, candidates, top_k)


    def _groq_rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """Ask Groq to score & explain each candidate against the buyer query."""
        catalog_json = json.dumps([
            {
                "id": c["product"]["id"],
                "name": c["product"]["name"],
                "category": c["product"]["category"],
                "specs": c["product"]["key_specs"],
                "price_inr": c["product"]["price_inr"],
                "price_unit": c["product"]["price_unit"],
                "description": c["product"]["description"],
                "faiss_score": round(c["faiss_score"], 4),
            }
            for c in candidates
        ], indent=2)

        system_prompt = textwrap.dedent("""
            You are an expert glass industry product advisor for AmalGus marketplace.
            Your job: given a buyer query and candidate products, return a JSON array
            (no other text) with re-ranked results.

            Rules:
            - Understand glass specs: thickness (mm), configuration (e.g. 5+12+5),
              certifications, coatings, use-case (partition, facade, railing, window, etc.)
            - score: integer 0-100 reflecting relevance to the buyer query
            - explanation: 1-2 clear sentences why this product matches (or partially matches)
            - Return AT MOST {top_k} items, best match first
            - Output ONLY valid JSON array, nothing else

            Schema:
            [
              {{"id": "P001", "score": 88, "explanation": "..."}}
            ]
        """).replace("{top_k}", str(top_k))

        user_msg = f"Buyer query: {query}\n\nCandidate products:\n{catalog_json}"

        response = self._groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content
        ranked = _parse_groq_json(raw)

        id_map = {c["product"]["id"]: c["product"] for c in candidates}
        results = []
        for r in ranked[:top_k]:
            pid = r.get("id")
            if pid in id_map:
                results.append({
                    "product": id_map[pid],
                    "score": max(0, min(100, int(r.get("score", 50)))),
                    "explanation": r.get("explanation", "Good semantic match."),
                })

        if not results:
            for c in candidates[:top_k]:
                results.append({
                    "product": c["product"],
                    "score": int(c["faiss_score"] * 100),
                    "explanation": "Matched based on product specifications and description.",
                })

        return results