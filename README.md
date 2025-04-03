# 🍿 MovieQueue

A personalized movie recommendation system powered by Streamlit and Neo4j.

## 🎥 About

MovieQueue helps you:
- 🎯 Get movie recommendations tailored to your taste
- ⭐ Rate and keep track of your favorite movies
- 📊 View analytics about your viewing habits
- 🔐 Register and securely login

---

## 🚀 Features

- Streamlit multipage app
- Neo4j-powered recommendations
- Secure login & registration (bcrypt)
- User-friendly interface
- Track ratings & analytics

---

## ⚙️ Setup

1. Clone the repo:
    ```bash
    git clone https://github.com/ryanjuricic26/MovieQueue.git
    cd MovieQueue
    ```

2. Setup environment:
    ```bash
    ./setup.sh
    ```

3. Create a `.env` file:
    ```bash
    cp .env.example .env
    # fill in your Neo4j credentials
    ```

4. Run the app:
    ```bash
    streamlit run MovieQueue.py
    ```

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Neo4j
- bcrypt
- python-dotenv

---

## 📄 License

MIT License

## 🙏 Credits

Made by Ryan Juricic