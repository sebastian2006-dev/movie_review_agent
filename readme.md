# 🎬 AI Movie Review Analyzer (OMDb Edition)

An AI-powered movie & TV show analysis app that combines real-world data with intelligent critique to generate detailed, multi-perspective reviews.

Built using **Streamlit**, **OMDb API**, and **Ollama (local LLM)**.

---

## 🚀 Features

* 🎬 **Clean UI**

  * Poster + movie details
  * Simple, focused interface

* ⭐ **Dual Rating System**

  * IMDb Rating (via OMDb)
  * AI-generated rating

* 🧠 **AI-Powered Review System**

  * 🎬 Veteran Critic (20+ years experience)
  * 😈 Devil’s Advocate (critical perspective)
  * 👥 Audience Perspective

* 🎯 **Structured Analysis**

  * Themes extraction
  * Critics vs Audience comparison

* 📝 **Detailed Verdict**

  * Overview
  * What Works ✅
  * What Fails ❌
  * Final Score ⭐

---

## 🛠 Tech Stack

* **Frontend/UI**: Streamlit
* **Backend**: Python
* **Movie Data API**: OMDb API
* **AI Model**: Ollama (LLaMA 3)
* **Env Management**: python-dotenv

---

## 📁 Project Structure

```id="omdb_struct"
movie_review_agent/
│
├── app.py                # Main Streamlit UI
├── tools.py              # OMDb API integration
├── README.md             # Documentation
│
└── agent/
    └── sentiment.py      # AI analysis logic
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash id="omdb_clone"
git clone <your-repo-url>
cd movie_review_agent
```

---

### 2️⃣ Create virtual environment

```bash id="omdb_venv"
python -m venv .venv
```

Activate:

* Windows:

```bash id="omdb_activate"
.\.venv\Scripts\activate
```

---

### 3️⃣ Install dependencies

```bash id="omdb_install"
pip install -r requirements.txt
```

---

### 4️⃣ Setup OMDb API

* Go to: http://www.omdbapi.com/apikey.aspx
* Generate your free API key

Create a `.env` file:

```id="omdb_env"
OMDB_API_KEY=your_api_key_here
```

---

### 5️⃣ Setup Ollama

Install Ollama from: https://ollama.com

Pull model:

```bash id="omdb_model"
ollama pull llama3
```

Make sure Ollama is running locally.

---

### 6️⃣ Run the app

```bash id="omdb_run"
streamlit run app.py
```

---

## 🧠 How It Works

1. User enters a movie/show title

2. OMDb API fetches:

   * Title
   * Plot
   * Poster
   * IMDb rating

3. Data is passed to the AI model (Ollama)

4. AI generates:

   * Expert critic analysis
   * Devil’s advocate critique
   * Audience sentiment
   * Final verdict & score

---

## 🎯 Example Output

* 🎬 Veteran Critic → deep storytelling analysis
* 😈 Devil’s Advocate → critical counterpoints
* 👥 Audience → emotional reaction
* ⭐ Final Score → AI rating

---

## ⚠️ Limitations

* Requires **local Ollama setup**
* OMDb provides limited metadata (no trailers/backdrops)
* AI output depends on model quality

---

## 🔮 Future Improvements

* 🎥 Trailer integration (YouTube / TMDb)
* 🎬 Enhanced UI (Netflix-style)
* 💬 Chat-based interface
* 🌐 Cloud deployment

---

## 👨‍💻 Author

Developed as part of an academic project focusing on AI prompting, critique systems, and intelligent analysis workflows.

---

## 📜 License

For educational use only.
