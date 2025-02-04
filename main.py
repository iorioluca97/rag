import json
import os

import openai
import streamlit as st

from config.cfg import FAQ
from config.logger import logger
from core.database import MongoDb
from core.text_extractor import TextExtractor
from core.util_functions import (
    call_llm_for_question,
    call_llm_for_toc,
    create_required_folders,
    laod_env,
    process_question,
)

create_required_folders()

OPENAI_API_KEY, MONGODB_ATLAS_CLUSTER_URI = laod_env()

# CREATE CLIENT
client = openai.Client()
db = MongoDb(MONGODB_ATLAS_CLUSTER_URI)


# Inizialize the session state
def initialize_session_state():
    if "local_file_path" not in st.session_state:
        st.session_state.local_file_path = None
    if "messages" not in st.session_state:
        st.session_state.messages = [] 
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "top_p" not in st.session_state:
        st.session_state.top_p = 0.9
    if "top_k" not in st.session_state:
        st.session_state.top_k = 10
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 4096
    if "model" not in st.session_state:
        st.session_state.model = "gpt-4o"
    if "user_type" not in st.session_state:
        st.session_state.user_type = "PM"
    if "message_ratings" not in st.session_state:
        st.session_state.message_ratings = {}


# Cache the extracted text, TOC, and keywords
@st.cache_data
def process_pdf():
    text_extract = TextExtractor(path=st.session_state.local_file_path)
    full_text = text_extract.extract_full_text()
    logger.info("Extracting TOC and keywords manually...")
    toc, pages = text_extract.generate_toc()

    if len(pages) == 0 or len(toc) == 0:
        logger.info("TOC not found. Using LLM to generate TOC...")
        toc, pages = call_llm_for_toc(
            path=st.session_state.local_file_path, client=client
        )

    keywords = text_extract.extract_keywords(pages=pages)
    return toc, full_text, keywords


@st.cache_data
def save_vectors():
    # Check if the collection exists
    if not db.collection_exists(collection_name=st.session_state.collection_name):
        logger.info(
            f"Collection {st.session_state.collection_name} does not exist. Creating it..."
        )
        db.process_and_store_pages(
            path=st.session_state.local_file_path, keywords=st.session_state.keywords
        )

    else:
        # Set up MongoDB with the collection name
        db.change_collection(collection_name=st.session_state.collection_name)
        logger.info(f"Collection in use: {st.session_state.collection_name}.")
        st.session_state.db = db


def query_db(user_question):
    logger.info("Database not found. Creating a new instance...")
    db.change_collection(collection_name=st.session_state.collection_name)
    st.session_state.db = db

    return db.query_with_keyword_filter(
        query_text=process_question(text=user_question),
        top_k=st.session_state.top_k,
        keyword_filter=user_question.split(" "),
    )


def create_sidebar_configuration():
    # File Upload Section
    with st.sidebar:
        with st.expander("📄 File", expanded=True):
            uploaded_file = st.file_uploader("", type="pdf")
            if uploaded_file:
                os.makedirs("./tmp/", exist_ok=True)
                file_path = f"./tmp/{uploaded_file.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.local_file_path = file_path
                st.success(f"🚀 {uploaded_file.name} uploaded!")

                collection_name = (
                    st.session_state.local_file_path.split("/")[-1]
                    .lower()
                    .replace(".pdf", "")
                )
                st.session_state.collection_name = collection_name

        # RENDERING PDF MOLTO PESANTE
        # if uploaded_file:
        #     # Leggi i contenuti binari del PDF
        #     pdf_bytes = uploaded_file.read()

        #     # Converti i contenuti binari in base64
        #     base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

        #     # Mostra il PDF usando un iframe
        #     pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="350" height="500" type="application/pdf"></iframe>'
        #     st.markdown("### 📄 Rendering")
        #     st.markdown(pdf_display, unsafe_allow_html=True)

        # User Type Configuration
        with st.expander("🛠️ User Config", expanded=False):
            st.session_state.user_type = st.radio(
                "Choose your user type: ",
                ["PM", "TECH"],
                index=["PM", "TECH"].index(st.session_state.get("user_type", "PM")),
            )

        # Model Parameters
        with st.expander("⚙️ Model Params", expanded=False):
            st.session_state.model = st.selectbox(
                "Choose a model: ",
                options=["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"],
                index=["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"].index(
                    st.session_state.get("model", "gpt-4o")
                ),
            )
            st.session_state.temperature = st.slider(
                "Temperature:",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.1,
            )
            st.session_state.top_p = st.slider(
                "Top-p:",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.top_p,
                step=0.1,
            )

            st.session_state.max_tokens = st.slider(
                "Max Tokens:",
                min_value=256,
                max_value=8192,
                value=st.session_state.max_tokens,
                step=256,
            )

    create_faq_section()


def create_faq_section():
    if st.session_state.get("collection_name") in FAQ:
        with st.sidebar.expander("❓ FAQ", expanded=True):
            st.markdown(f"### {st.session_state.collection_name}")

            # Create buttons for each question
            for question in FAQ[st.session_state.get("collection_name")]:
                if st.button(question, key=f"btn_{question}"):

                    if not st.session_state.get("collection_name"):
                        st.warning(
                            "⚠️ Upload a PDF file to start the conversation."
                        )
                        return
                    # Simulate chat input when button is clicked
                    st.session_state.messages.append(
                        {"role": "user", "content": question}
                    )
                    # Get response
                    results = query_db(question)
                    display_vector_results(results, question)

                    message_history = st.session_state.messages.copy()

                    # Generate assistant response
                    streamed_text = ""
                    for chunk in call_llm_for_question(
                        path=st.session_state.local_file_path,
                        question=question,
                        external_knowledge=results,
                        client=client,
                        model=st.session_state.model,
                        temperature=st.session_state.temperature,
                        top_p=st.session_state.top_p,
                        max_tokens=st.session_state.max_tokens,
                        user_type=st.session_state.user_type,
                        history=message_history,
                    ):
                        streamed_text += chunk

                    st.session_state.messages.append(
                        {"role": "assistant", "content": streamed_text}
                    )
                    # Force a rerun to update the chat
                    st.rerun()


def display_feedback_section():
    with st.sidebar.expander("💬 Feedback", expanded=True):
        if not st.session_state.messages:
            st.write("No messages to provide feedback on.")
            return

        data_to_save = {}

        for idx, msg in enumerate(st.session_state.messages):
            # Consider only assistant messages
            if msg["role"] == "assistant":
                # Get the user question
                user_question = (
                    st.session_state.messages[idx - 1]["content"]
                    if idx > 0
                    else "Question not found"
                )

                # Show the question
                st.markdown(f"**Question:** {user_question}")

                # Get the current rating
                current_rating = st.session_state.message_ratings.get(idx, None)

                # Define feedback options
                options = {
                    "❌": "The answer is incorrect.",
                    "⚠️": "The answer is partially correct.",
                    "✅": "The answer is correct.",
                }

                # Update the rating
                def update_rating(selected_emoji, message_index):
                    if (
                        st.session_state.message_ratings.get(message_index)
                        != selected_emoji
                    ):
                        st.session_state.message_ratings[message_index] = selected_emoji

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("❌", key=f"wrong_{idx}"):
                        update_rating("❌", idx)
                with col2:
                    if st.button("⚠️", key=f"partial_{idx}"):
                        update_rating("⚠️", idx)
                with col3:
                    if st.button("✅", key=f"correct_{idx}"):
                        update_rating("✅", idx)


                st.markdown(
                    f"**Feedback:** {options[current_rating] if current_rating else 'No feedback'}"
                )


                if current_rating:
                    rating_str = (
                        current_rating.replace("❌", "wrong")
                        .replace("⚠️", "partial")
                        .replace("✅", "correct")
                    )
                    data_to_save[idx] = {
                        "question": user_question,
                        "answer": msg["content"],
                        "rating": rating_str,
                        "user_type": st.session_state.user_type,
                        "model_params": {
                            "temperature": st.session_state.temperature,
                            "top_p": st.session_state.top_p,
                            "max_tokens": st.session_state.max_tokens,
                            "model": st.session_state.model,
                        },
                    }

                st.divider()

        # Salva il feedback in un file JSON
        feedback_file_path = "./chatbot_output/feedback.json"
        with open(feedback_file_path, "w") as f:
            json.dump(data_to_save, f, indent=4)

        # Aggiungi un pulsante per scaricare il JSON
        st.download_button(
            label="📥 Download the feedbacks",
            data=json.dumps(data_to_save, indent=4),
            file_name="feedback.json",
            mime="application/json",
        )


def display_vector_results(results: list, question: str):
    with st.sidebar:
        with st.expander("🔍 Vector Search Results", expanded=True):
            st.markdown("### {}".format(question))
            for i, result in enumerate(results, 1):
                st.markdown(
                    f"""
                **Result {i}**
                - 📄 Page: {result['page']}
                - 🎯 Score: {result['score']:.4f}
                ---
                """
                )


def display_chat():
    if "collection_name" not in st.session_state:
        st.warning("⚠️ Upload a PDF file to start the conversation.")
        return

    if st.session_state.get("toc"):
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {"role": "assistant", "content": "How can I help you?"}
            ]

        # Create a container for chat messages
        chat_container = st.container()

        with chat_container:
            for idx, msg in enumerate(st.session_state.messages):
                st.chat_message(msg["role"]).write(msg["content"])

        # Handle new messages
        if question := st.chat_input():
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            st.chat_message("user").write(question)

            # Process response
            with st.spinner("Analizying the question..."):
                results = query_db(question)
                # Display vector search results in sidebar
                display_vector_results(results, question)

            message_history = st.session_state.messages.copy()

            # Generate and display assistant response
            streamed_text = ""
            for chunk in call_llm_for_question(
                path=st.session_state.local_file_path,
                question=question,
                external_knowledge=results,
                client=client,
                model=st.session_state.model,
                temperature=st.session_state.temperature,
                top_p=st.session_state.top_p,
                max_tokens=st.session_state.max_tokens,
                user_type=st.session_state.user_type,
                history=message_history,
            ):
                streamed_text += chunk

            st.session_state.messages.append(
                {"role": "assistant", "content": streamed_text}
            )
            st.rerun()


def main():
    initialize_session_state()
    st.set_page_config(page_title="Streamlit RAG Chatbot", layout="wide")
    st.title("Streamlit RAG - Chatbot")

    # Create sidebar
    create_sidebar_configuration()

    # Handle file processing
    if st.session_state.local_file_path:

        with st.spinner("Generating TOC and keywords..."):
            toc, full_text, keywords = process_pdf()
            st.session_state.toc = toc
            st.session_state.full_text = full_text
            st.session_state.keywords = keywords

        with st.spinner("Saving vectors to the database..."):
            save_vectors()
            db.change_collection(collection_name=st.session_state.collection_name)
            st.session_state.db = db

        with st.sidebar.expander("📚 Summary", expanded=True):
            formatted_toc = "\n".join(
                [
                    f"- **{item.get('title', 'No Title')}** (Pagina: {item.get('page', 'N/A')})"
                    for item in toc
                ]
            )
            st.markdown(f"### {st.session_state.collection_name}\n{formatted_toc}")

    display_chat()

    display_feedback_section()


if __name__ == "__main__":
    main()
