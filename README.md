# Custom Chatbot Backend

## Setup
1. `pip install -r requirements.txt`
2. Set `OPENAI_API_KEY` and `MONGO_URI`

## Ingestion
```bash
python services/data_ingestion/scraper.py   # edit URLs list
python -c "from services.data_ingestion.parser import HtmlParser; HtmlParser(...).parse_all()"
python -c "from services.data_ingestion.transformer import Transformer; Transformer(...).transform_all()"
python -c "from services.data_ingestion.loader import Loader; Loader(...).validate_all()"
```

## Build Vector Store

```bash
python services/vectorstore_builder/build_vectorstore.py
```

## Run API

```bash
uvicorn app.main:app --reload
``` 