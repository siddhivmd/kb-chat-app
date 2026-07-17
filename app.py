import streamlit as st
import os
from store import store_pdf
from query import answer_question

st.set_page_config(page_title="Knowledge Base Chat", layout="wide")
st.title("📄 Knowledge Base Chat")
st.caption("Upload PDFs and ask questions — answers are grounded only in your documents.")

# --- Session state setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# --- Sidebar: Upload & Process ---
with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF file(s)", type="pdf", accept_multiple_files=True
    )

    if st.button("Process Documents", type="primary"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF first.")
        else:
            with st.spinner("Processing documents..."):
                for file in uploaded_files:
                    if file.name in st.session_state.processed_files:
                        continue  # skip already-processed files
                    try:
                        # Save uploaded file to disk temporarily so extract.py can read it
                        temp_path = f"temp_{file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())

                        store_pdf(temp_path, file.name)
                        st.session_state.processed_files.append(file.name)

                        os.remove(temp_path)  # clean up temp file
                    except Exception as e:
                        st.error(f"Failed to process {file.name}: {e}")

            if st.session_state.processed_files:
                st.success(f"Processed: {', '.join(st.session_state.processed_files)}")

    if st.session_state.processed_files:
        st.markdown("**Documents in knowledge base:**")
        for name in st.session_state.processed_files:
            st.markdown(f"- {name}")

# --- Main chat area ---
if not st.session_state.processed_files:
    st.info("👈 Upload and process at least one PDF to start asking questions.")
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"Sources · Confidence: {msg['confidence']}% ({msg['confidence_label']})"):
                    for src in msg["sources"]:
                        st.markdown(f"- **{src['source']}**, Page {src['page']}")
            elif msg["role"] == "assistant":
                st.caption(f"Confidence: {msg['confidence']}% ({msg['confidence_label']})")

    # Chat input
    question = st.chat_input("Ask a question about your documents...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = answer_question(question)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander(f"Sources · Confidence: {result['confidence']}% ({result['confidence_label']})"):
                    for src in result["sources"]:
                        st.markdown(f"- **{src['source']}**, Page {src['page']}")
            else:
                st.caption(f"Confidence: {result['confidence']}% ({result['confidence_label']})")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"],
            "confidence_label": result["confidence_label"]
        })