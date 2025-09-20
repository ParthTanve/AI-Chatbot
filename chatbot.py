import streamlit as st
import google.generativeai as genai
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.memory import ConversationBufferMemory
from PIL import Image
from functions import (
    speak_text,
    speech_to_text_from_mic,
    extract_text_from_file,
    handle_command,
    ask_gemini
)
from API import GENAI_API_KEY
import os

# --- Configure Google Gemini ---
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Streamlit UI ---
st.set_page_config(page_title="AI Chatbot", layout="wide")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("chatbot.png", caption="AI Chatbot Logo", width=300)

st.title("Bruno Chatbot")

# --- Chat History ---
msgs = StreamlitChatMessageHistory(key="chat_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

# ✅ Memory wrapper for LangChain integration
memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=msgs,
    return_messages=True
)

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Chat", "Voice", "File", "Image Upload"])

user_input = None
image_input = None
image_question = None

# --- Chat Mode ---
if menu == "Chat":
    user_input = st.text_input("Type your message here...")

# --- Voice Mode ---
elif menu == "Voice":
    if st.button("Speak"):
        with st.spinner("Listening..."):
            user_input = speech_to_text_from_mic()
        st.success(f"Recognized Speech: {user_input}")

# --- File Mode ---
elif menu == "File":
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt", "py", "xlsx", "docx", "pptx"])
    if uploaded_file:
        with st.spinner("Processing file..."):
            file_text = extract_text_from_file(uploaded_file)

        with st.expander("Show File Content"):
            st.write(file_text[:500] + "...")

        user_input = st.text_area("Ask a question about the file content:", "")
        if user_input:
            user_input = f"Context: {file_text}\n\nQuestion: {user_input}"

# --- Image Mode ---
elif menu == "Image Upload":
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image_input = Image.open(uploaded_image)
        st.image(image_input, caption="Uploaded Image", use_container_width=True)
        image_question = st.text_input("What do you want to know about this image?")

        if st.button("Submit"):
            user_input = image_question

# --- Handle Input ---
if user_input or image_input:
    if menu == "Image Upload" and uploaded_image and image_question:
        msgs.add_user_message(image_question)
        with st.spinner("Generating response..."):
            bot_reply = ask_gemini(
                image_question,
                model=model,
                image=image_input,
                chat_history=msgs.messages
            )
        msgs.add_ai_message(bot_reply)
    else:
        command_response = handle_command(user_input if user_input else "")

        if command_response:
            msgs.add_ai_message(command_response)
        else:
            msgs.add_user_message(user_input if user_input else "Sent an Image")
            with st.spinner("Thinking..."):
                bot_reply = ask_gemini(
                    user_input if user_input else "Describe this image",
                    model=model,
                    image=image_input,
                    chat_history=msgs.messages
                )
            msgs.add_ai_message(bot_reply)

# --- Display Chat ---
for msg in msgs.messages:
    if msg.type == "human":
        st.markdown(f"**You:** {msg.content}")
    else:
        st.markdown(
            f'**<span style="color: #4CAF50;">Bruno:</span>** {msg.content}',
            unsafe_allow_html=True
        )
        speak_text(msg.content)
