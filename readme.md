# 🎬 Movie Review Agent 

> *Two AI models walk into a cinema. One hates everything. One defends everything. You get the truth.*

**Movie Review Agent** is a Streamlit-powered web application that allows users to search for any film and witness a high-stakes intellectual debate between two specialized AI agents: a harsh **Critic** and a loyal **Advocate**. 

Driven by the **Groq API** for near-instant inference, the system processes movie metadata, runs a 4-round structured debate, and converges on a final calibrated score. All of this is presented in a premium **Dark Velvet Cinema** interface.

---

## ✦ Features

| Feature | Description |
|---|---|
| 🔍 **Smart Search** | Exact + fuzzy OMDb search, deduped, with high-quality poster results. |
| 🎭 **Groq-Powered Debate** | 4-round logic battle between Llama-3.3-70b (Critic) and Mixtral-8x7b (Advocate). |
| 🏆 **Score Ring Charts** | Custom animated SVG rings comparing AI verdicts with IMDb and Rotten Tomatoes. |
| 🎨 **Dark Velvet UI** | A cinematic aesthetic featuring molten copper accents and Playfair Display typography. |
| 🏷️ **AI Theme Extraction** | Automatic identification of genre and thematic "chips" per film. |
| ⚖️ **Scoring Basis** | Transparent methodology explaining how the final AI score was derived. |

---

## 🏗 Architecture

The system follows a modular layered architecture:

1.  **Presentation Layer:** Streamlit (app.py) handles the Dark Velvet UI and state management.
2.  **Service Layer:** Integration with **OMDb API** for real-time movie data and posters.
3.  **Agent Engine:** A custom debate orchestrator (`agent/sentiment.py`) using **Groq API**.
4.  **Inference Layer:** High-speed processing using **Llama-3.3-70b** and **Mixtral-8x7b**.

### Data Flow
```text
User Search ──► OMDb API ──► Movie Metadata ──► Groq Agent Engine ──► UI Pipeline