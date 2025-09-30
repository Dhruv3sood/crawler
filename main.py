import sys
import nest_asyncio
import streamlit as st
import asyncio
from src.app.extractor import (
    parse_schema,
    parse_json_ld,
    parse_opengraph,
    parse_twitter,
    parse_microdata,
    parse_rdfa
)

# --- FIX FOR WINDOWS ASYNCIO ---
# This is necessary to run Playwright (used by crawl4ai) on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

nest_asyncio.apply()

# --- App Configuration ---
st.set_page_config(
    page_title="Web Data Extractor",
    page_icon="🕸️",
    layout="wide"
)

# --- Parser Mapping ---
# Maps user-friendly names to the actual parser functions
PARSERS = {
    "JSON-LD": parse_json_ld,
    "Microdata": parse_microdata,
    "OpenGraph": parse_opengraph,
    "Twitter Cards": parse_twitter,
    "RDFA": parse_rdfa,
    "AI Schema (CSS)": parse_schema,
}

# --- App UI ---
st.title("🕸️ Universal Web Data Extractor")
st.markdown(
    "Enter a URL, select one or more extraction methods, and view the results. "
    "The app will try the selected methods in order and stop at the first one that returns data."
)

# --- Input Fields ---
with st.container(border=True):
    url = st.text_input(
        "**URL to Scrape**",
        placeholder="https://example.com/product/123",
        key="url_input"
    )

    available_parsers = list(PARSERS.keys())
    selected_parsers = st.multiselect(
        "**Choose Extraction Methods** (in order of execution)",
        options=available_parsers,
        default=[ "AI Schema (CSS)"] # Sensible defaults
    )

    start_button = st.button("Extract Data", type="primary", use_container_width=True)

# --- Execution Logic ---
if start_button:
    if not url:
        st.error("Please enter a URL to start extraction.")
    elif not selected_parsers:
        st.error("Please select at least one extraction method.")
    else:
        # Placeholders for live updates
        log_placeholder = st.empty()
        result_placeholder = st.empty()

        async def run_extraction():
            for parser_name in selected_parsers:
                parser_func = PARSERS[parser_name]
                st.info(f"▶️ Trying method: **{parser_name}**...")

                try:
                    if parser_name == "AI Schema (CSS)":
                        data = await parser_func(url)
                    else:
                        data = await parser_func(url)

                    if data:
                        st.success(f"✅ Success! Data found using **{parser_name}**.")
                        with result_placeholder.container():
                            st.subheader("Extracted Data")
                            st.json(data)
                        return True
                    else:
                        st.warning(f"🟡 Method '{parser_name}' ran but found no data.")
                except Exception as e:
                    st.error(f"❌ Method '{parser_name}' failed with an error: {e}")
            return False

        # --- Async Run Fix for Windows/Streamlit ---
        with st.spinner("Extraction in progress... Please wait."):
            try:
                if sys.platform.startswith("win"):
                    # Use ProactorEventLoop for Playwright subprocesses
                    loop = asyncio.ProactorEventLoop()
                    asyncio.set_event_loop(loop)
                else:
                    loop = asyncio.get_event_loop()

                # Apply nest_asyncio to allow Streamlit to run async inside an existing loop
                import nest_asyncio
                nest_asyncio.apply()

                is_successful = loop.run_until_complete(run_extraction())
            except Exception as e:
                st.error(f"❌ Extraction failed: {e}")
                is_successful = False

        if not is_successful:
            st.error("🚫 All selected extraction methods failed or found no data.")