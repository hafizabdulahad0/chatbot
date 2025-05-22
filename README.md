


# Custom Chatbot Backend

An end-to-end Retrieval-Augmented Generation (RAG) chatbot service using FastAPI, ChromaDB, and OpenAI.


* **What it is:**

  * A one-line summary that appears at the top of your GitHub repo.
  * Conveys the core tech: **RAG** (combining retrieval from a vector store with LLM generation), **FastAPI** for the API server, **ChromaDB** for the vector database, and **OpenAI** for embeddings & completions.

* **Why it matters:**

  * Immediately orients readers on what problem you’re solving and which major libraries/frameworks you’re using.

---

## 2. Features

```markdown
## 🚀 Features

- **Offline Ingestion Pipeline**  
  Scrape, parse, chunk, and validate web page content into structured JSON  
- **Vectorstore Builder**  
  Embed content via OpenAI’s embedding API and store in ChromaDB  
- **RAG API**  
  FastAPI endpoint (`/chat/`) for answering questions with grounded citations  
- **One-click Pipeline**  
  `run_pipeline.py` wraps extraction, scraping, parsing, chunking, validation, and vectorstore build  
- **CLI & Front-End**  
  - `chat_cli.py`: simple terminal chat interface  
  - `frontend/index.html`: minimal browser UI (served by FastAPI)
```

* **Offline Ingestion Pipeline:**

  * Lives under `services/data_ingestion/`.
  * Transforms raw HTML or other inputs into validated, chunked JSON.

* **Vectorstore Builder:**

  * `services/vectorstore_builder/build_vectorstore.py`.
  * Takes those JSON chunks, calls OpenAI to embed them, and upserts to a local Chroma store.

* **RAG API:**

  * `app/api/chat.py` + `app/core/rag_pipeline.py`.
  * Receives user questions, retrieves relevant chunks, and uses OpenAI’s Chat API to generate answers.

* **One-click Pipeline:**

  * `run_pipeline.py` glues all ingestion and vectorstore steps into one script—so you don’t have to run four or five separate commands.

* **CLI & Front-End:**

  * `chat_cli.py` lets you chat from your terminal.
  * `frontend/index.html` gives a quick browser-based UI for manual testing.

---

## 3. Project Structure

```markdown
## 📂 Project Structure

.
├── .env                         Environment variables
├── README.md                    This file
├── requirements.txt             Python dependencies
├── run_pipeline.py              One-click ingestion + vectorstore build
├── chat_cli.py                  Command-line chat client
├── app.py                       (If using Flask) main server entrypoint
├── app/                         FastAPI app package
│   ├── main.py                  FastAPI server & CORS/static setup
│   ├── api/
│   │   └── chat.py              `/chat/` endpoint
│   ├── core/
│   │   ├── llm_client.py        OpenAI ChatCompletion wrapper
│   │   └── rag_pipeline.py      RAG logic with few-shot prompt
│   ├── db/
│   ├── ingestion/               Runtime helpers (PDF loader, splitter, embedder, vector store)
├── services/
│   ├── data_ingestion/          Offline ETL (scraper, parser, transformer, loader)
│   └── vectorstore_builder/     ChromaDB build script & config
├── scripts/
│   └── extract_urls.py          Extract URLs from JSON manifests
├── raw_data/                    Scraped HTML (by company)
├── processed_data/              Structured & chunked JSON (by company)
├── vectorstores/                ChromaDB files (by company)
└── frontend/
    └── index.html               Static test UI
```

* **Why it’s here:**

  * Provides a visual overview of every folder and key file.
  * Helps a newcomer find where each piece of functionality lives.

* **Key nodes:**

  * **`.env`**—where you store API keys & config.
  * **`run_pipeline.py`**—the single entry point for content ingestion.
  * **`app/`**—your FastAPI application code.
  * **`services/`**—offline, batch-style ETL and vectorstore building.
  * **`frontend/`** and **`chat_cli.py`**—two easy ways to test the chatbot.

---

## 4. Setup

````markdown
## ⚙️ Setup

1. **Clone** the repo  
   ```bash
   git clone https://github.com/hafizabdulahad0/chatbot.git
   cd chatbot
````

2. **Create & activate** a virtualenv

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   .\venv\Scripts\activate    # Windows
   ```

3. **Install** dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure** `.env` in project root:

   ```dotenv
   OPENAI_API_KEY=sk-...
   COMPANY_NAME=my_company
   VECTORSTORE_PATH=vectorstores/my_company/chroma.sqlite3
   MONGO_URI=mongodb://localhost:27017
   ```

````

- **Step-by-step** commands ensure anyone can get the project running in minutes.
- **Virtualenv** instructions cover both Unix and Windows.
- **`.env`** snippet reminds the user which keys/configs are required and their formats.

---

## 5. Running the Ingestion & Build

```markdown
## 🏗️ Running the Ingestion & Build

```bash
python run_pipeline.py
````

*Writes to→*

* `raw_data/<company>/`
* `processed_data/<company>/`
* `vectorstores/<company>/chroma.sqlite3`

````

- **`run_pipeline.py`** automates the entire offline pipeline.  
- After it finishes, you’ll see your scraped HTML, processed JSON, and the binary Chroma DB all in their respective folders.

---

## 6. Launching the API

```markdown
## 🖥️ Launching the API

```bash
uvicorn app.main:app --reload
````

* **Health check:** `GET http://127.0.0.1:8000/health`
* **Chat UI:**     `http://127.0.0.1:8000/frontend/index.html`
* **Swagger:**     `http://127.0.0.1:8000/docs`

````

- **`uvicorn`** command runs the FastAPI server with auto-reload on code changes.  
- Lists three easy ways to interact: a simple JSON health check, the static front-end, and the built-in Swagger docs.

---

## 7. Chat Examples

```markdown
## 🤖 Chat Examples

```bash
# CLI
python chat_cli.py

# curl
curl -X POST http://127.0.0.1:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"What is included in the 5-Day Hunza Tour?"}'
````

````

- **Multiple interfaces**:  
  - **CLI** for quick terminal hits.  
  - **`curl`** for raw HTTP testing.  
- Shows exactly what JSON to send and what command to use.

---

## 8. Customization & Tips

```markdown
## 🛠️ Customization & Tips

- Adjust **`run_rag`** few-shot prompt in `app/core/rag_pipeline.py` for better accuracy  
- Tune **`RAG_TOP_K`**, embedding model, or completion model via environment variables  
- Add retries, logging, and async support for production readiness  
````

* **Why it’s here:**

  * Encourages future improvements and gives pointers on where to look.
* **Areas to tweak:**

  * **Prompt engineering**, **model parameters**, **error handling**, and **performance**.

---

## 9. License

```markdown
## License

MIT © [Hafiz Abdul Ahad]
```


