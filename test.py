
import streamlit as st
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import sqlite3
import hashlib

# ------------------ Database Setup ------------------
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    return c.fetchone()

def add_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# ------------------ Session State ------------------
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# ------------------ Authentication UI ------------------
def login_signup_ui():
    tabs = st.tabs(["🔐 Login", "🆕 Signup"])
    
    # Login Tab
    with tabs[0]:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()  # 🔁 Force rerun to update UI
            else:
                st.error("Invalid credentials")

    # Signup Tab
    with tabs[1]:
        st.subheader("Create a New Account")
        new_username = st.text_input("New Username", key="signup_user")
        new_password = st.text_input("New Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            if add_user(new_username, new_password):
                st.success("Account created successfully! You can now log in.")
            else:
                st.error("Username already exists. Please choose another.")

# ------------------ Pest Detection ------------------
def pest_detection_app():
    st.title("🌿 AgriShield")
    st.write(f"Welcome **{st.session_state.username}** 👋")
    st.write("Upload an image of a pest to classify and get recommendations.")

    # Load models
    model2 = load_model('pest_detection_model2_v2.h5')
    model3 = load_model('pest_detection_model3_v2.h5')

    class_names = [
        'Aphids', 'Armyworms', 'Brown Marmorated Stink Bugs', 'Cabbage Loopers',
        'Citrus Canker', 'Colorado Potato Beetles', 'Corn Borers', 'Corn Earworms',
        'Fall Armyworms', 'Fruit Flies', 'Spider Mites', 'Thrips', 'Tomato Hornworms',
        'Western Corn Rootworms'
    ]

    pesticides = {
        "Aphids": "Use neem oil or insecticidal soap.",
        "Armyworms": "Apply Bacillus thuringiensis (Bt) or Spinosad.",
        "Brown Marmorated Stink Bugs": "Use pheromone traps and pyrethroid sprays.",
        "Cabbage Loopers": "Neem oil and Bt-based sprays work well.",
        "Citrus Canker": "Copper-based fungicides and pruning help control spread.",
        "Colorado Potato Beetles": "Use Spinosad or Beauveria bassiana sprays.",
        "Corn Borers": "Bt corn and biological controls like Trichogramma wasps.",
        "Corn Earworms": "Vegetable oils and Bacillus thuringiensis (Bt) help reduce infestation.",
        "Fall Armyworms": "Early detection and use of insecticides like chlorantraniliprole.",
        "Fruit Flies": "Use bait traps and remove overripe fruit.",
        "Spider Mites": "Miticides, neem oil, and predatory mites help.",
        "Thrips": "Insecticidal soap and blue sticky traps work best.",
        "Tomato Hornworms": "Handpicking and Bacillus thuringiensis (Bt) spray.",
        "Western Corn Rootworms": "Crop rotation and soil-applied insecticides are effective."
    }

    uploaded_file = st.file_uploader("📤 Upload Pest Image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image_size = (224, 224)
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        img = img.convert("RGB")
        img = img.resize(image_size)
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Get predictions from individual models
        prediction2 = model2.predict(img_array)
        prediction3 = model3.predict(img_array)

        # Ensemble by averaging predictions
        ensemble_prediction = np.mean([prediction2, prediction3], axis=0)

        if ensemble_prediction.shape[-1] == len(class_names):
            predicted_class = class_names[np.argmax(ensemble_prediction)]
            confidence = np.max(ensemble_prediction) * 100
            st.success(f"🛑 Detected Pest: **{predicted_class}**")
            st.write(f"🛠 **Recommended Treatment:** {pesticides.get(predicted_class)}")
        else:
            st.error(f"⚠️ Model output shape mismatch: {ensemble_prediction.shape}, expected {len(class_names)} classes.")

    st.markdown("---")
    st.write("🚀 Developed as part of **Pest Detection & Classification Project**")

# ------------------ Logout Option ------------------
def logout_button():
    if st.button("🔓 Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

# ------------------ Main App Flow ------------------
if st.session_state.authenticated:
    logout_button()
    pest_detection_app()
else:
    login_signup_ui()
