import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        return api_key

    try:
        import streamlit as st

        return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return None


api_key = get_openai_api_key()

client = OpenAI(api_key=api_key)


def call_model(system_prompt, user_prompt, model="gpt-4.1-mini"):
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text
