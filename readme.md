# 🎬 Movie Review Agent

> *A Critic and an Advocate debate any film across four rounds — then deliver a calibrated verdict.*

---

## Overview

An AI-powered movie review agent built with Streamlit. Search any film or series, and two AI models (a Critic and an Advocate) engage in a structured 4-round debate — analysing craft, vision, pacing, and cultural legacy — before converging on a final score. Each result includes the official trailer, cast & crew info, IMDb and Rotten Tomatoes ratings, and a full debate transcript.

---

## Features

- 🔍 **Smart Movie Search** — Combines exact-match and fuzzy search via OMDB for accurate results
- 🤖 **AI Debate Engine** — Two Groq-powered models argue opposing positions across 4 structured rounds
- 🎥 **In-App Trailer Playback** — Official YouTube trailers embedded directly in the UI (no redirects)
- ⭐ **Multi-Source Ratings** — AI verdict, IMDb, and Rotten Tomatoes scores displayed as animated rings
- 🎭 **Debate Transcript** — Full round-by-round conversation between the Critic and Advocate models
- 🏷️ **Core Themes** — AI-extracted thematic tags for each film
- 📊 **Scoring Methodology** — Transparent breakdown of how the AI verdict is calculated
- 🌑 **Dark Velvet Cinema UI** — Custom-designed cinematic interface with Playfair Display typography

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web app framework & UI |
| [OMDB API](https://www.omdbapi.com) | Movie metadata, ratings, posters |
| [Groq API](https://groq.com) | LLM inference for the debate engine |
| [YouTube Data API v3](https://developers.google.com/youtube/v3) | Fetching & embedding official trailers |
| Python `requests` | HTTP calls to all external APIs |

---

## Project Structure

```
movie_review_agent/
├── app.py                  # Main Streamlit app (UI + API calls)
├── agent/
│   └── sentiment.py        # Groq debate engine (Critic & Advocate models)
├── .streamlit/
│   └── secrets.toml        # API keys (not committed to git)
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/movie_review_agent.git
cd movie_review_agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up API keys

Create a `.streamlit/secrets.toml` file in the project root:

```toml
OMDB_API_KEY     = "your_omdb_api_key"
GROQ_API_KEY     = "your_groq_api_key"
YOUTUBE_API_KEY  = "your_youtube_api_key"
```

> ⚠️ Never commit `secrets.toml` to version control. Add it to `.gitignore`.

### 4. Run the app

```bash
streamlit run app.py
```

---

## API Key Setup

### OMDB API
1. Go to [omdbapi.com](https://www.omdbapi.com/apikey.aspx)
2. Sign up for a free key (1,000 requests/day)
3. Verify your email and paste the key into `secrets.toml`

### Groq API
1. Go to [console.groq.com](https://console.groq.com)
2. Create an account and navigate to **API Keys**
3. Generate a new key and paste it into `secrets.toml`

### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Navigate to **APIs & Services → Library**, search for **YouTube Data API v3**, and enable it
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. (Recommended) Restrict the key to YouTube Data API v3 only
6. Paste the key into `secrets.toml`

> Free quota: ~10,000 units/day. Each trailer search costs ~100 units.

---

## How the Debate Works

Each film analysis runs through four structured rounds:

| Round | Focus |
|---|---|
| 01 · Opening Statements | Initial critical take vs. contrarian defence of the film's premise |
| 02 · Craft & Vision | Cinematography, direction, character arcs, score, and technical artistry |
| 03 · Rebuttals | Pacing, narrative coherence, thematic depth, cultural legacy |
| 04 · Final Synthesis | Calibrated convergence on a 10-point cinematic quality score |

The **Critic model** argues from a rigorous analytical standpoint. The **Advocate model** defends the film's intent and artistic merit. A neutral synthesis produces the final score.

---

## Deploying to Streamlit Cloud

1. Push your project to a GitHub repository (ensure `secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Under **Advanced Settings → Secrets**, paste the contents of your `secrets.toml`
4. Deploy — Streamlit Cloud handles the rest

---

## Environment Variables Reference

| Key | Description |
|---|---|
| `OMDB_API_KEY` | OMDB API key for movie metadata |
| `GROQ_API_KEY` | Groq API key for LLM debate engine |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key for trailer search |

---

## License

MIT License — feel free to fork, modify, and build on this project.

---

## Acknowledgements

- [OMDB API](https://www.omdbapi.com) for comprehensive movie data
- [Groq](https://groq.com) for blazing-fast LLM inference
- [YouTube Data API](https://developers.google.com/youtube/v3) for trailer embedding
- [Streamlit](https://streamlit.io) for making Python apps delightful to build