"""Streamlit UI for the Academic FAQ Chatbot."""

from __future__ import annotations

import time

import streamlit as st

from chatbot import AcademicFAQChatbot


# Configure Streamlit page
st.set_page_config(
    page_title="Academic FAQ Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_chatbot() -> AcademicFAQChatbot:
    """Load and cache the chatbot instance."""
    return AcademicFAQChatbot()


def main() -> None:
    """Run the Streamlit chatbot interface."""
    # Header
    st.markdown('<h1 class="main-header">🎓 Academic FAQ Chatbot</h1>', unsafe_allow_html=True)
    st.markdown(
        "Ask me anything about academic policies, deadlines, course registration, and university procedures!"
    )

    chatbot = load_chatbot()

    # Sidebar information
    with st.sidebar:
        st.header("📊 Chatbot Status")

        if chatbot.is_trained:
            st.success("✅ Knowledge Base Loaded")
            st.info(chatbot.get_stats())
        else:
            st.error("❌ Knowledge Base Not Found")
            st.warning("Please run `python knowledge_base_builder.py` first!")

        st.header("💡 Tips for Better Results")
        st.markdown(
            """
        - Ask specific questions about academic policies
        - Use keywords like "registration", "deadline", "requirements"
        - Be clear and concise in your questions
        - Try rephrasing if you don't get good results
        """
        )

        st.header("🔧 Quick Actions")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm your Academic FAQ Assistant. I can help you with questions about academic policies, "
                    "deadlines, course registration, and university procedures. What would you like to know?"
                ),
            }
        )

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your academic question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Searching through academic documents..."):
                start_time = time.time()
                response = chatbot.generate_response(prompt)
                response_time = time.time() - start_time

            st.markdown(response)

            with st.sidebar:
                st.metric("⏱️ Last Response Time", f"{response_time:.2f}s")

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.markdown("---")
    st.markdown("💡 **Need help?** Try asking about course registration, academic deadlines, or university policies!")


if __name__ == "__main__":
    main()
