import streamlit as st
from datetime import datetime
import random
from nlp_model import model, tokenizer, pad_sequences, X, lbl_enc, df
import re
import emoji
import os


# Function to set Streamlit page configuration
def setup_page():
    st.set_page_config(page_title="Chatbot for Depression Support", page_icon="💬")


# Function to generate response
def generate_answer(user_input):
    pattern = user_input
    if pattern.lower() == 'quit':
        return "Goodbye!"

    text = []
    txt = re.sub('[^a-zA-Z\']', ' ', pattern)
    txt = txt.lower()
    txt = txt.split()
    txt = " ".join(txt)
    text.append(txt)

    x_test = tokenizer.texts_to_sequences(text)
    x_test = pad_sequences(x_test, padding='post', maxlen=X.shape[1])

    y_pred = model.predict(x_test)
    y_pred = y_pred.argmax()

    tag = lbl_enc.inverse_transform([y_pred])[0]
    responses = df[df['tag'] == tag]['responses'].values[0]
    return random.choice(responses)


# Function to generate and add messages to chat history
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})


# Function to save current chat session and clear messages
def save_and_clear_chat():
    session_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chat_sessions.append({"name": session_name, "messages": st.session_state.messages.copy()})
    st.session_state.messages = []


# Function to refresh chat to a new page
def refresh_chat():
    session_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chat_sessions.append({"name": session_name, "messages": st.session_state.messages.copy()})
    st.session_state.messages = []
    st.rerun()


# Function to display previous chat sessions
def display_previous_chats():
    st.sidebar.header("Previous Chats")
    for i, session in enumerate(st.session_state.chat_sessions):
        if st.sidebar.button(f"Chat from {session['name']}", key=f"chat_{i}"):
            st.session_state.messages = session["messages"]
            st.rerun()


# Initialize Streamlit page configuration
setup_page()

# Initialize chat history and sessions in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []
if "emoji_selected" not in st.session_state:
    st.session_state.emoji_selected = False
if "depression_test_started" not in st.session_state:
    st.session_state.depression_test_started = False
if "depression_test_completed" not in st.session_state:
    st.session_state.depression_test_completed = False
if "depression_score" not in st.session_state:
    st.session_state.depression_score = 0
if "motivation_selected" not in st.session_state:
    st.session_state.motivation_selected = False

# Display chat messages
st.title("Chatbot for Depression Support")
st.subheader("Chat with the bot")

# Actions buttons at the top-left
if st.sidebar.button("Refresh Chat", key="refresh_chat"):
    refresh_chat()


# Motivation options


# Display previous chat sessions (in the left sidebar)
display_previous_chats()

# Scrollable chat container
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<p style="color: yellow;">👤You:</p> {message["content"]}', unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="color: orange;">🤖 Bot:</p> {message["content"]}', unsafe_allow_html=True)


# Function to handle emoji input
def handle_emoji(emoji_label):
    emoji_responses = {
        "very_happy": "I'm so happy to hear that you're feeling great! Keep shining!",
        "happy": "I'm glad to hear you're feeling happy! Keep up the positive vibes!",
        "neutral": "It's perfectly okay to feel neutral. How can I assist you today?",
        "slightly_sad": "I'm sorry you're feeling a bit down. I'm here to support you.",
        "sad": "I'm sorry you're feeling sad. Remember, it's okay to feel this way. I'm here for you.",
        "very_sad": "I'm really sorry you're feeling very sad. I'm here for you. Let's talk about it."
    }
    add_message("user", emoji_label)
    response = emoji_responses.get(emoji_label, "How can I assist you today?")
    add_message("bot", response)
    st.session_state.emoji_selected = True
    st.rerun()


# Function to handle depression test
def handle_depression_test():
    st.session_state.depression_test_started = True
    st.session_state.depression_test_completed = False
    st.rerun()


# Function to calculate depression score
def calculate_depression_score(responses):
    score = sum(responses)
    return score


# Display emoji selection initially
if not st.session_state.emoji_selected:
    st.markdown("### How are you feeling today? Select an emoji that represents your mood:")
    emojis = ["😁", "😊", "😐", "😟", "😢", "😭"]
    emoji_labels = ["very_happy", "happy", "neutral", "slightly_sad", "sad", "very_sad"]
    emoji_cols = st.columns(len(emojis))
    for i, emoji_char in enumerate(emojis):
        if emoji_cols[i].button(emoji.emojize(emoji_char)):
            handle_emoji(emoji_labels[i])

# Depression score button
st.sidebar.markdown("### Your Depression Score")
score_display = st.sidebar.button(f"Score: {st.session_state.depression_score}")

# Display depression test form
if st.session_state.depression_test_started and not st.session_state.depression_test_completed:
    st.markdown("### Depression Test")
    st.markdown("Please answer the following questions based on how you have felt over the past two weeks:")

    questions = [
        "How often have you felt little interest or pleasure in doing things?",
        "How often have you felt down, depressed, or hopeless?",
        "How often have you had trouble falling asleep, staying asleep, or sleeping too much?",
        "How often have you felt tired or had little energy?",
        "How often have you had a poor appetite or overeating?",
        "How often have you felt bad about yourself or that you are a failure or have let yourself or your family down?",
        "How often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
        "How often have you moved or spoken so slowly that other people could have noticed? Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual?",
        "How often have you had thoughts that you would be better off dead or of hurting yourself in some way?"
    ]

    options = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
    option_values = [0, 1, 2, 3]

    responses = []
    for question in questions:
        response = st.selectbox(question, options, key=question)
        responses.append(option_values[options.index(response)])

    if st.button("Submit Test"):
        score = calculate_depression_score(responses)
        st.session_state.depression_score = score
        st.session_state.depression_test_completed = True
        st.session_state.depression_test_started = False
        st.rerun()

# Display depression test results and advice
if st.session_state.depression_test_completed:
    score = st.session_state.depression_score
    st.markdown(f"Your depression score is: {score}/27")

    if score <= 4:
        severity = "Minimal depression"
        advice = [
            "You're doing great! Keep maintaining a positive outlook.",
            "Continue engaging in activities that make you happy.",
            "Keep in touch with friends and loved ones."
        ]
    elif 5 <= score <= 9:
        severity = "Mild depression"
        advice = [
            "Try to stay active and exercise regularly.",
            "Keep a journal to track your thoughts and feelings.",
            "Reach out to friends and family for support."
        ]
    elif 10 <= score <= 14:
        severity = "Moderate depression"
        advice = [
            "Consider talking to a therapist or counselor.",
            "Make time for activities you enjoy.",
            "Practice relaxation techniques such as deep breathing or meditation."
        ]
    elif 15 <= score <= 19:
        severity = "Moderately severe depression"
        advice = [
            "It's important to seek help from a mental health professional.",
            "Try to establish a routine to help manage your day-to-day activities.",
            "Stay connected with supportive friends and family."
        ]
    else:
        severity = "Severe depression"
        advice = [
            "Please seek immediate help from a mental health professional.",
            "Consider reaching out to a crisis hotline or support group.",
            "Remember that you don't have to go through this alone; support is available."
        ]

    st.markdown(f"Severity: **{severity}**")
    st.markdown("### Here is some advice for you:")
    for tip in advice:
        st.markdown(f"- {tip}")

    st.session_state.depression_test_completed = False



# # # Function to handle motivation options
# def handle_motivation(option):
#     motivation_responses = {
#         "stories": "Here's a motivational story for you...",
#         "quotes": "Here's a motivational quote for you...",
#         "podcast": "Here's a motivational podcast for you..."
#     }
#     add_message("user", option)
#     response = motivation_responses.get(option, "How can I assist you today?")
#     add_message("bot", response)
#     st.session_state.motivation_selected = True
#     st.rerun()


# User input handling
def submit_message():
    user_input = st.session_state.user_input
    add_message("user", user_input)
    response = generate_answer(user_input)
    add_message("bot", response)
    st.session_state.user_input = ""
    st.rerun()


# Fixed position user input at the bottom, only if emoji is selected and depression test is not active
if st.session_state.emoji_selected and not st.session_state.depression_test_started and not st.session_state.depression_test_completed:
    st.markdown("---")
    input_container = st.empty()
    with input_container:
        user_input = st.text_input("Type your message here...", key="user_input", on_change=submit_message)


# Actions buttons
st.markdown("---")

# Create two columns for the buttons
col1, col2 = st.columns(2)

# Clear chat history button in the first column
with col1:
    if st.button("Clear Chat History"):
        save_and_clear_chat()

# Depression test button in the second column
with col2:
    if st.button("Take Depression Test"):
        handle_depression_test()


# Predefined questions asked by depressed people
st.markdown("### Common Questions Asked by Depressed People")

# Questions as buttons in columns
col1, col2, col3 = st.columns(3)
questions = [
    "How can I get help for my depression?",
    "How can I cope with my anxiety?",
    "What are some tips for managing stress?",
    "How can I improve my sleep?",
    "Why do I feel so tired all the time?",
    "What are the side effects of antidepressants?",
    "How do I know if I need to see a therapist?",
    "What causes depression?",
    "How does exercise affect depression?",
    "What are the signs of a mental health crisis?"
]

# Function to handle question button clicks
def submit_question(question):
    add_message("user", question)
    response = generate_answer(question)
    add_message("bot", response)
    st.experimental_rerun()

# Display questions as buttons in columns
for i, question in enumerate(questions):
    if i % 3 == 0:
        button_col = col1
    elif i % 3 == 1:
        button_col = col2
    else:
        button_col = col3

    if button_col.button(question):
        submit_question(question)

