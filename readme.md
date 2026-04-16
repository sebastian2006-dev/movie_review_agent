# movie_review_agent

A multi-agent AI application that fetches movie data and runs a live debate between two LLM models to produce a balanced, calibrated film review — complete with a scored verdict, debate transcript, thematic analysis, and what works vs. what doesn't.

---

## 🧠 How It Works

1. User enters a movie title in the chat input
2. Movie metadata is fetched from the **OMDB API** (plot, cast, genre, director, IMDb rating, poster)
3. Two AI models from **Groq** are assigned opposing critic roles and conduct a **4-round structured debate**
4. A third synthesis pass produces a final verdict with score, themes, and structured pros/cons

---

## 🏗️ Project Structure

```
├── app.py                  # Streamlit UI — layout, theming, rendering
└── agent/
    └── sentiment.py        # Debate engine + synthesis logic
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/movie-review-agent.git
cd movie-review-agent
```

### 2. Install dependencies

```bash
pip install streamlit requests openai
```

### 3. Configure secrets

Create a `.streamlit/secrets.toml` file:

```toml
OMDB_API_KEY = "your_omdb_api_key"
GROQ_API_KEY = "your_groq_api_key"
```

- Get a free OMDB key at [omdbapi.com](https://www.omdbapi.com/apikey.aspx)
- Get a free Groq key at [console.groq.com](https://console.groq.com)

### 4. Run the app

```bash
streamlit run app.py
```

---

## 🤖 AI Models Used

| Role | Model | Provider |
|------|-------|----------|
| Movie Critique Model | `llama-3.3-70b-versatile` | Groq |
| Advocate / Devil's Advocate | `mixtral-8x7b-32768` | Groq |
| Synthesis / Final Verdict | `llama-3.3-70b-versatile` | Groq |

The Advocate model falls back to the Critic model automatically if unavailable.

---

## 🎭 Debate Structure

Each movie triggers a 4-round debate:

| Round | Speaker | Goal |
|-------|---------|------|
| 1 | Critic | Opening analysis — storytelling, direction, pacing, legacy |
| 2 | Advocate | Challenge or defend the Critic's take |
| 3 | Critic | Rebuttal — hold firm or concede ground |
| 4 | Advocate | Closing argument — final nuanced verdict |

The Advocate is **not purely negative** — it defends underrated films when warranted and challenges over-hyped ones equally.

---

## 📊 Scoring Rubric

Scores are calibrated against the full history of cinema, not just popular releases:

| Score | Meaning |
|-------|---------|
| 10/10 | All-time masterpiece (Citizen Kane, 2001, The Godfather) — extremely rare |
| 9–9.9 | Near-masterpiece — outstanding craft, enduring cultural impact |
| 8–8.9 | Excellent — strong, memorable, stands the test of time |
| 7–7.9 | Good — worthwhile with some standout qualities, minor flaws |
| 6–6.9 | Competent but uneven — enjoyable but forgettable |
| 5–5.9 | Mediocre — more misses than hits |
| 4–4.9 | Weak — poor execution or squandered premise |
| ≤ 3 | Bad — fails on most levels |

**Special rules:**
- Genre films (horror, action, comedy, sci-fi) that nail their goals **can score 8+** — they are not penalised for not being prestige dramas
- Underrated / underseen films with genuine craft are scored **higher** than their mainstream reputation suggests
- Hyped blockbusters with shallow writing are scored **honestly**, not given a free pass

---

## 🎨 UI Features

- **Dark / Light mode toggle** via query param (`?_dm=1`)
- Full debate transcript in a collapsible expander with styled chat bubbles
- Structured verdict: Summary · What Works · What Falls Short · Themes · Final Score
- Movie poster, metadata, and plot pulled live from OMDB
- Results are **cached per session** — re-submitting the same title won't re-run the debate

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `OMDB_API_KEY` | API key for Open Movie Database |
| `GROQ_API_KEY` | API key for Groq LLM inference |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | UI framework |
| `requests` | OMDB API calls |
| `openai` | Groq client (OpenAI-compatible SDK) |

---

## 📄 License

MIT License — free to use, modify, and distribute.