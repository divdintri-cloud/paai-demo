# PAAI Demo

PAAI is a personal AI assistant demo with:

- Book photo detection and library help
- Grocery photo analysis
- Activity log
- Demo mode for safe sharing

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment variable

Create a `.env` file locally:

```text
OPENAI_API_KEY=your_api_key_here
```

For Streamlit Cloud, add `OPENAI_API_KEY` in app secrets.

## Demo mode

Demo mode uses the `demo_data/` folder and hides private/payment/unfinished agents.
