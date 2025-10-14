import sys
import asyncio
import nest_asyncio
import streamlit as st
import json
import requests
from extruct import extract as extruct_extract
from w3lib.html import get_base_url
from src.app.extractor import parse_schema
from src.core.utils.standards_extractor import extract_standard

# --- Windows asyncio fix ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
nest_asyncio.apply()

st.set_page_config(page_title="🕸️ Web Data Extractor", page_icon="🕸️", layout="wide")
st.title("🕸️ Universal Web Data Extractor")

with st.container(border=True):
    url = st.text_input(
        "🌐 **Enter a URL**",
        placeholder="https://example.com/product/123",
        key="url_input",
    )
    strategy = st.radio(
        "🔍 Choose extraction strategy:",
        ["AI Schema (CSS)", "Standards Extractor"],
        horizontal=True,
        index=1,
    )
    extract_btn = st.button("🚀 Extract", type="primary", use_container_width=True)


def beautify_json(data):
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def display_json_sections(data: dict):
    syntaxes = []
    for syntax, entries in data.items():
        if not entries:
            continue
        clean_entries = []
        for entry in entries:
            if (
                isinstance(entry, dict)
                and list(entry.keys()) == ["@id"]
                or (
                    "http://www.w3.org/1999/xhtml/vocab#role" in entry
                    and len(entry.keys()) <= 2
                )
            ):
                continue
            clean_entries.append(entry)
        if clean_entries:
            syntaxes.append((syntax, clean_entries))
    for syntax, entries in syntaxes:
        with st.expander(
            f"📦 {syntax.upper()} — {len(entries)} entries", expanded=True
        ):
            for entry in entries:
                st.code(beautify_json(entry), language="json", line_numbers=False)


async def extract_and_display_standards(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text
    base_url = get_base_url(html, url)
    data = extruct_extract(
        html,
        base_url=base_url,
        syntaxes=[
            "microdata",
            "opengraph",
            "json-ld",
            "microformat",
            "rdfa",
            "dublincore",
        ],
    )

    # Zuerst das Endergebnis anzeigen
    st.subheader("✅ Schritt 1: Kombiniertes Endergebnis (Produkt)")
    result = await extract_standard(
        data, url, preferred=["microdata", "json-ld", "rdfa", "opengraph"]
    )
    st.code(beautify_json(result), language="json")

    # Danach die Rohdaten pro Syntax anzeigen
    st.subheader("🔍 Schritt 2: Extrahierte Rohdaten pro Syntax")
    display_json_sections(data)


if extract_btn:
    if not url:
        st.error("❌ Bitte gib eine gültige URL ein.")
    else:
        st.info(f"Extrahiere Daten mit **{strategy}**...")
        with st.spinner("⏳ Daten werden geladen und analysiert..."):
            try:
                if strategy == "AI Schema (CSS)":
                    loop = asyncio.get_event_loop()
                    nest_asyncio.apply()
                    result = loop.run_until_complete(parse_schema(url))
                    st.success("✅ Extraktion abgeschlossen!")
                    st.code(beautify_json(result), language="json")
                else:
                    loop = asyncio.get_event_loop()
                    nest_asyncio.apply()
                    loop.run_until_complete(extract_and_display_standards(url))
                    st.success("✅ Extraktion abgeschlossen!")
            except Exception as e:
                st.error(f"⚠️ Extraktion fehlgeschlagen: {e}")
