import streamlit as st

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
with tab_financials:
    st.subheader("Basic Financial Data")
    st.info("Hook up a financial data source here — e.g. yfinance, Alpha Vantage, or your own data.")

    ticker = st.text_input("Enter a ticker symbol", value="AAPL")

    if ticker:
        # TODO: replace with real data fetch
        st.write(f"Showing placeholder data for **{ticker.upper()}**")
        st.metric("Market Cap", "$2.8T", delta="+1.2%")
        st.metric("P/E Ratio", "28.4")
        st.metric("Revenue (TTM)", "$385B", delta="+5.3%")
