from datetime import datetime
import streamlit as st
import chromadb

# Import custom functions for financial data, news scraping and chatbot (if implemented)
from functions.fin_api import get_esg_company_financials
from functions.news_scraper import display_articles

from functions.chatbot import get_chat_response_hist

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="esg")

st.set_page_config(layout="wide", page_title="ESG Dashboard", page_icon="🌱")

col_logo, col_title, col_chat = st.columns([3, 4, 1])
with col_logo:
    st.image("logo.webp", use_container_width=True)
with col_title:
    st.title("🌱 ESG Dashboard")
    
with col_chat:
    st.write("")
    st.write("")
    with st.popover("Chat", use_container_width=True):
        st.subheader("ESG Chatbot")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        chat_window = st.container(height=350)
        with chat_window:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("How can I help?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            recent_history = st.session_state.messages[-6:]
            with st.spinner("Analyzing..."):
                response = get_chat_response_hist(prompt, collection, recent_history)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

st.divider()

tab_dashboard, tab_news, tab_financials = st.tabs([
    "📊 Dashboard",
    "📰 ESG News",
    "💹 Financials",
])

# ---------------------------------------------------------------------------
# Tab 1 — Looker Studio embed
# ---------------------------------------------------------------------------
with tab_dashboard:
    st.caption("Powered by Looker Studio")
    LOOKER_URL = "https://datastudio.google.com/embed/reporting/b295d785-ed80-45b4-8261-24c14c6e357e/page/p_j76if3pr2d"
    st.components.v1.iframe(LOOKER_URL, height=850, scrolling=True)

# ---------------------------------------------------------------------------
# Tab 2 — ESG News
# ---------------------------------------------------------------------------
with tab_news:
    st.subheader("Company relevant ESG News")
    st.info("News articles are sourced from the ESG News website (https://esgnews.com/).")

    company_map = {
        "Nike": "nike",
        "Adidas": "adidas",
        "Puma": "puma",
    }

    selected_company = st.selectbox(
        "Select a company for news",
        list(company_map.keys()),
        key="news_company_select",
    )

    @st.cache_data(show_spinner=False)
    def load_company_news(company_tag: str):
        return display_articles(company_tag)

    with st.spinner("Loading ESG-related articles..."):
        articles = load_company_news(company_map[selected_company])

    if not articles:
        st.warning("No relevant ESG articles found.")
    else:
        for article in articles:
            title = article.get("title") or article["url"]

            st.markdown(f"### [{title}]({article['url']})")
            st.markdown(
                f"**Pillar:** {article['main_pillar']}  \n"
                f"**Relevance:** {article['strength'].capitalize()}"
            )
            st.markdown(article["message"])

            if article.get("matched_keywords"):
                st.caption("Matched keywords: " + ", ".join(article["matched_keywords"]))

            st.divider()

# ---------------------------------------------------------------------------
# Tab 3 — Financials
# ---------------------------------------------------------------------------


# cache the financial data to avoid hitting API limits during development
@st.cache_data
def load_financial_data():
    return get_esg_company_financials()


# create tab for displaying financial metrics for the companies
with tab_financials:
    st.subheader("Basic Financial Data")

    if "financial_data" not in st.session_state:
        st.session_state.financial_data = load_financial_data()
        st.session_state.financial_timestamp = datetime.now()

    financial_data = st.session_state.financial_data

    company_options = list(financial_data.keys())
    selected_company = st.selectbox("Select a company", company_options)

    company_data = financial_data[selected_company]

    if "error" in company_data:
        st.error(f"Could not load data for {selected_company}: {company_data['error']}")
    else:
        st.write(
            f"Showing financial data for **{company_data['company_name']}** "
            f"({company_data['ticker']})"
        )

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5, _ = st.columns(2)

        col1.metric(
            "Market Cap",
            f"${company_data['market_cap']:.2f}M" if company_data["market_cap"] is not None else "N/A"
        )
        col2.metric(
            "P/E Ratio",
            f"{company_data['pe_ratio']:.2f}" if company_data["pe_ratio"] is not None else "N/A"
        )
        col3.metric(
            "Revenue Growth (TTM YoY)",
            f"{company_data['revenue_growth']:.2f}%" if company_data["revenue_growth"] is not None else "N/A"
        )
        col4.metric(
            "Net Margin (TTM)",
            f"{company_data['net_margin']:.2f}%" if company_data["net_margin"] is not None else "N/A"
        )
        col5.metric(
            "Debt-to-Equity",
            f"{company_data['debt_to_equity']:.2f}" if company_data["debt_to_equity"] is not None else "N/A"
        )

    st.caption(
        "Numbers obtained at "
        + st.session_state.financial_timestamp.strftime("%d-%m-%Y %H:%M:%S")
    )

    if st.button("Refresh financial data"):
        st.session_state.financial_data = load_financial_data()
        st.session_state.financial_timestamp = datetime.now()
        st.rerun()
