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
from streamlit_mic_recorder import mic_recorder 


genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


st.set_page_config(page_title="AI Chatbot", layout="wide")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("chatbot.png", caption="AI Chatbot Logo", width=300)

st.title("Bruno Chatbot")


msgs = StreamlitChatMessageHistory(key="chat_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")


memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=msgs,
    return_messages=True
)


menu = st.sidebar.radio("Navigation", ["Chat", "Voice", "File", "Image Upload"])

user_input = None
image_input = None
image_question = None
uploaded_image = None
uploaded_file = None


if menu == "Chat":
    user_input = st.text_input("Type your message here...")


elif menu == "Voice":
    st.write("Click 'Record' to start, and 'Stop' when finished. The audio will then be processed.")
    
    
    audio_data_dict = mic_recorder(
        start_prompt="Record", 
        stop_prompt="Stop",
        key='mic_recorder',
        format="wav" 
    )

    if audio_data_dict:
        
        if 'last_audio_data' not in st.session_state or st.session_state.get('last_audio_data') != audio_data_dict:
            st.session_state['last_audio_data'] = audio_data_dict
            
            
            audio_bytes = audio_data_dict.get('bytes') 
            
            with st.spinner("Processing speech..."):
                
                recognized_text = speech_to_text_from_mic(audio_bytes) 
            
            st.success(f"Recognized Speech: {recognized_text}")
            
            
            st.session_state['voice_input'] = recognized_text
            st.rerun()


elif menu == "File":
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt", "py", "xlsx", "docx", "pptx"])
    if uploaded_file:
        with st.spinner("Processing file..."):
            file_text = extract_text_from_file(uploaded_file)

        with st.expander("Show File Content"):
            st.write(file_text[:500] + "...")

        user_input = st.text_area("Ask a question about the file content:", key="file_question")
        if user_input:
            user_input = f"Context: {file_text}\n\nQuestion: {user_input}"


elif menu == "Image Upload":
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image_input = Image.open(uploaded_image)
        st.image(image_input, caption="Uploaded Image", use_container_width=True)
        image_question = st.text_input("What do you want to know about this image?", key="image_question")

        if st.button("Submit"):
            user_input = image_question



if 'voice_input' in st.session_state and st.session_state['voice_input']:
    user_input = st.session_state.pop('voice_input')



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



for msg in msgs.messages:
    if msg.type == "human":
        st.markdown(f"**You:** {msg.content}")
    else:
        st.markdown(
            f'**<span style="color: #4CAF50;">Bruno:</span>** {msg.content}',
            unsafe_allow_html=True
        )
        

        speak_text(msg.content)

