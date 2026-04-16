import os
import pandas as pd
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


api_key=os.getenv("OPENROUTER_API_KEY")
endpoint='https://openrouter.ai/api/v1'

# chat client
client = OpenAI(api_key=api_key, 
                    base_url=endpoint)


def search_matching_data(query, collection, n_results=5):
    #chroma_client = chromadb.PersistentClient(path="./chroma_db")
    #collection = chroma_client.get_or_create_collection(name="esg")
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0]


def get_contextual_query(history, latest_input):
    """Rewrites the user input into a standalone search query."""
    system_prompt = """You are a Query Rewriter. Your goal is to turn conversational input into a single search string by identifying the user's final intent.
    - Resolve pronouns (it, they, that company) using the History.
    - Absolute Source of Truth (MANDATORY OVERWRITE): The most recent User Input is the absolute Source of Truth.
    - If the user changes the brand or topic, prioritize the LATEST input.
    - Output ONLY the search string. No explanations.
    - Ensure the output is a single string that captures the user's final, most up-to-date intent."""

    # History should be a list of strings: ["User: msg", "Assistant: msg"]
    conversation_context = "\n".join(history) if history else ""
    
    response = client.chat.completions.create(
        model="microsoft/phi-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"History:\n{conversation_context}\n\nInput: {latest_input}"}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()



def get_chat_response_hist(user_query, collection, history_list):
    # 1. Transform history list for the rewriter
    # history_list is st.session_state.messages (list of dicts)
    formatted_history = [f"{m['role'].capitalize()}: {m['content']}" for m in history_list]

    # 2. Rewrite the query!
    search_query = get_contextual_query(formatted_history, user_query)
    
    # 3. Search using the REWRITTEN query, not the raw input
    relevant_data = search_matching_data(search_query, collection)
    context_text = "\n\n".join(f"- {item}" for item in relevant_data)
    
    # 4. Generate the final answer
    system_prompt = f""" 
I. ROLE: You are an ESG analyst assistant. You help users find information related to their queries.

II. CRITICAL RULES
- STRICT RAG GROUNDING: You can answer questions ONLY using the context below. You must not invent or "fill in" any details. If a piece of information is missing, do not guess and simply state the information is not listed. 
- THE "NO MATCH" RULE : If the user's request is entirely outside the scope of the context and there are no remotely similar alternatives, clearly state so.
- STYLE: Keep responses professional, informative and clearly formatted.

Context:
{context_text}
"""
    # Construct standard chat history for the final LLM call
    messages = [{"role": "system", "content": system_prompt}] + history_list
    
    resp = client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=messages,
        temperature=0
    )
    return resp.choices[0].message.content




""" with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("How can I help?"):
        
        # 1. Show and store user message
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 2. Slice history to the last 6 messages
        # This keeps the 6 most recent entries (e.g., 3 user prompts + 3 assistant replies)
        recent_history = st.session_state.messages[-6:]

        # 3. Get response using only the sliced history
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = get_chat_response_hist(user_input, collection, recent_history)
                st.markdown(response)

        # 4. Store assistant response
        st.session_state.messages.append({"role": "assistant", "content": response}) """
        
        
        
""" with tab_chat:

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("How can I help?")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        recent_history = st.session_state.messages[-6:]
        response = get_chat_response_hist(user_input, collection, recent_history)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun() """