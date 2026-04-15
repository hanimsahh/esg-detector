from datetime import datetime
import streamlit as st

# Import the function to get financial data
from functions.fin_api import get_esg_company_financials

st.set_page_config(layout="wide", page_title="ESG Dashboard", page_icon="🌱")

st.title("🌱 ESG Dashboard")
st.caption("Powered by WikiRate & Looker Studio")
st.divider()

tab_dashboard, tab_chat, tab_news, tab_financials = st.tabs([
    "📊 Dashboard",
    "🤖 Chatbot",
    "📰 ESG News",
    "💹 Financials",
])

# ---------------------------------------------------------------------------
# Tab 1 — Looker Studio embed
# ---------------------------------------------------------------------------
with tab_dashboard:
    LOOKER_URL = "https://datastudio.google.com/embed/reporting/b295d785-ed80-45b4-8261-24c14c6e357e/page/p_j76if3pr2d"
    st.components.v1.iframe(LOOKER_URL, height=850, scrolling=True)

# ---------------------------------------------------------------------------
# Tab 2 — Chatbot (stub)
# ---------------------------------------------------------------------------
with tab_chat:
    st.subheader("ESG Document Chatbot")
    st.info("Connect your document store here — e.g. LangChain + your ESG files.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask a question about your ESG documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # TODO: replace this with your actual LLM/RAG call
        response = f"(stub) You asked: {prompt}"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)

# ---------------------------------------------------------------------------
# Tab 3 — ESG News (stub)
# ---------------------------------------------------------------------------
with tab_news:
    st.subheader("Recent ESG News")
    st.info("Hook up a news API here — e.g. NewsAPI, GNews, or an RSS feed filtered by ESG keywords.")

    # TODO: fetch and display real articles
    placeholder_articles = [
        {"title": "EU tightens CSRD reporting rules", "source": "Reuters", "url": "#"},
        {"title": "Apple hits 100% renewable energy target", "source": "FT", "url": "#"},
        {"title": "SEC climate disclosure rules update", "source": "Bloomberg", "url": "#"},
    ]
    for article in placeholder_articles:
        st.markdown(f"**[{article['title']}]({article['url']})** — {article['source']}")
        st.divider()

# ---------------------------------------------------------------------------
# Tab 4 — Financials (stub)
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
