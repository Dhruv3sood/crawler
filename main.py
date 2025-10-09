import sys
import asyncio
import nest_asyncio
import streamlit as st
import json
import requests
from extruct import extract as extruct_extract
from w3lib.html import get_base_url
from src.app.extractor import parse_schema

# --- Windows asyncio fix ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
nest_asyncio.apply()

# --- Streamlit Config ---
st.set_page_config(page_title="🕸️ Web Data Extractor", page_icon="🕸️", layout="wide")
st.title("🕸️ Universal Web Data Extractor")
st.markdown(
    """
This tool extracts structured data from web pages using two strategies:
- 🧠 **AI Schema (CSS)** — Custom AI-based extraction  
- 🧩 **Standards Extractor** — Uses JSON-LD, Microdata, RDFa, OpenGraph, etc.
"""
)

# --- Input Section ---
with st.container(border=True):
    url = st.text_input("🌐 **Enter a URL**", placeholder="https://example.com/product/123", key="url_input")
    strategy = st.radio(
        "🔍 Choose extraction strategy:",
        ["AI Schema (CSS)", "Standards Extractor"],
        horizontal=True,
        index=1,
    )
    extract_btn = st.button("🚀 Extract", type="primary", use_container_width=True)

# --- Helper functions ---
async def extract_ai_schema(url: str):
    """Run custom AI Schema (CSS) extractor."""
    return await parse_schema(url)

def extract_standards(url: str):
    """Extract using extruct (standard syntaxes)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebDataExtractor/1.0)"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text
    base_url = get_base_url(html, url)
    return extruct_extract(
        html,
        base_url=base_url,
        syntaxes=["microdata", "opengraph", "json-ld", "microformat", "rdfa", "dublincore"],
    )

def beautify_json(data):
    """Format JSON in a pretty, compact way."""
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)

# --- Display Helper ---
def display_json_sections(data: dict):
    """Render each syntax in collapsible expanders, 3 per row horizontally, full-width JSON inside."""

    # Prepare syntaxes for display
    syntaxes = []
    for syntax, entries in data.items():
        if not entries:
            continue
        clean_entries = []

        for entry in entries:
            # 🧹 Filter unwanted RDFa-like minimal entries
            if (
                isinstance(entry, dict)
                and list(entry.keys()) == ["@id"]
                or (
                    "http://www.w3.org/1999/xhtml/vocab#role" in entry
                    and len(entry.keys()) <= 2
                )
            ):
                continue

            # 🔹 Microdata filter: only include Products
            if syntax.lower() == "microdata":
                if entry.get("type") != "https://schema.org/Product":
                    continue

            clean_entries.append(entry)

        if clean_entries:
            syntaxes.append((syntax, clean_entries))

    for syntax, entries in syntaxes:
        with st.expander(f"📦 {syntax.upper()} — {len(entries)} entries", expanded=True):
            for entry in entries:
                st.code(beautify_json(entry), language="json", line_numbers=False)


# --- Run Extraction ---
if extract_btn:
    if not url:
        st.error("❌ Please enter a valid URL.")
    else:
        st.info(f"Extracting data using **{strategy}**...")
        with st.spinner("⏳ Fetching and analyzing data..."):
            try:
                if strategy == "AI Schema (CSS)":
                    loop = asyncio.get_event_loop()
                    nest_asyncio.apply()
                    result = loop.run_until_complete(extract_ai_schema(url))
                    st.success("✅ Extraction complete!")
                    st.code(beautify_json(result), language="json")

                else:  # Standards Extractor
                    result = extract_standards(url)
                    st.success("✅ Extraction complete!")
                    display_json_sections(result)

            except Exception as e:
                st.error(f"⚠️ Extraction failed: {e}")
