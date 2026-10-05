"""
Frontend: Streamlit RAG UI  (STARTER)
=======================================
Run with (local dev):
    BACKEND_URL=http://localhost:8000 streamlit run app.py

Inside Docker it reads BACKEND_URL from the environment automatically.

Your goal: build a Streamlit UI that talks to the FastAPI RAG backend.

Required features:
    1. Sidebar:
       - Health status indicator (call GET /health on load)
         Show "Backend: connected ✓" or "Backend: unreachable ✗"
       - "Re-index Documents" button (calls POST /ingest)
         Show success message with chunk count
    2. Main area:
       - Page title and brief description
       - Text input for the question
       - "Ask" button (or use st.chat_input)
       - Answer display with:
           - Confidence badge (high / medium / low)
           - Answer text
           - Source list (document names)
    3. Error handling:
       - Backend unreachable → show st.error() with instructions
       - Empty answer → show a "No answer returned" message

Key concepts:
    Read backend URL from env:
        import os
        BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

    Calling the backend:
        response = requests.post(f"{BACKEND_URL}/ask",
                                 json={"question": question})
        data = response.json()
        # data["answer"], data["sources"], data["confidence"]

    Confidence colours:
        colours = {"high": "green", "medium": "orange", "low": "red"}
        st.markdown(f":{colour}[Confidence: {confidence}]")
"""

import streamlit as st
import requests
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Assistant", 
    page_icon="🔍", 
    layout="centered")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
#   - Fetch GET /health and show backend status
#   - "Re-index Documents" button → POST /ingest → show result

    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=3).json()
        st.success(f"API: Connected")
        st.write(f"Ollama: {health.get('ollama', 'unknown')}")
        st.metric("Documents", health.get('documents', 0))
    except requests.exceptions.RequestException:
        st.error("Backend: unreachable ✗")
        st.caption(
            "Make sure the FastAPI backend is running "
            "and BACKEND_URL is correct."
        )

    if st.button("🔄 Re-index Documents"):
        try:
            with st.spinner("Indexing documents..."):
                response = requests.post(
                    f"{BACKEND_URL}/ingest",
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()

            st.success(
                result.get("message", "Indexing completed.")
            )

            # Display chunk count if provided by the API
            chunk_count = result.get(
                "chunks",
                result.get("chunk_count")
            )

            if chunk_count is not None:
                st.write(f"Chunks indexed: {chunk_count}")

            st.rerun()

        except requests.exceptions.RequestException as error:
            st.error(f"Document indexing failed: {error}")
        except ValueError:
            st.error("The backend returned an invalid response.")


# ── Main area ──────────────────────────────────────────────────────────────
# TODO: st.title("RAG Assistant")
# TODO: st.caption("Ask questions grounded in your documents.")

# TODO: question = st.text_input("Your question") or st.chat_input(...)

# TODO: if question:
#   - POST /ask with {"question": question}
#   - Display confidence badge
#   - Display answer
#   - Display sources (st.expander or bullet list)
#   - Handle requests.exceptions.ConnectionError with st.error()

st.title("🔍 RAG Assistant")

st.caption(
    "Ask questions and get answers grounded in your documents."
)

st.write(
    "Enter a question below. The assistant will retrieve "
    "relevant document sections to help answer it."
)

# Question input
with st.form("question_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g., What are the benefits of recycling?"
    )

    ask_button = st.form_submit_button("Ask")

# Ask the backend
if ask_button:
    if not question.strip():
        st.warning("Please enter a question first.")

    else:
        try:
            with st.spinner("Searching documents and generating an answer..."):
                response = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"question": question.strip()},
                    timeout=180
                )
                response.raise_for_status()
                data = response.json()

            answer = data.get("answer", "")
            confidence = str(
                data.get("confidence", "low")
            ).lower()
            sources = data.get("sources", [])

            # Confidence badge
            colors = {
                "high": "green",
                "medium": "orange",
                "low": "red"
            }

            color = colors.get(confidence, "red")

            st.subheader("Answer")
            st.markdown(
                f":{color}[Confidence: {confidence}]"
            )

            # Answer text
            if answer and answer.strip():
                st.write(answer)
            else:
                st.info("No answer returned.")

            # Source documents
            st.subheader("Sources")

            if sources:
                for source in sources:
                    if isinstance(source, dict):
                        source_name = source.get(
                            "source",
                            source.get("name", str(source))
                        )
                    else:
                        source_name = str(source)

                    st.markdown(f"- {source_name}")
            else:
                st.write("No sources returned.")

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to the backend. "
                "Start the FastAPI service and check BACKEND_URL."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. The backend or LLM "
                "may need more time to respond."
            )

        except requests.exceptions.HTTPError as error:
            st.error(f"The backend returned an HTTP error: {error}")

        except requests.exceptions.RequestException as error:
            st.error(f"Request failed: {error}")

        except ValueError:
            st.error("The backend returned an invalid JSON response.")