import streamlit as st
from openai import OpenAI


def get_openai_client():
    return OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


def improve_technical_procedure(text, instruction):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI asistent pre kontrolné a skúšobné plány (KSP)
v stavebníctve.

Tvojou úlohou je technologicky posudzovať a upravovať
pracovné postupy, kontroly a skúšky.

Pravidlá:
- zachovaj stavebnú a technickú terminológiu,
- nevymýšľaj normy ani požiadavky, ktoré nie sú v podkladoch,
- ak niečo chýba alebo si nie si istý, označ to ako OVERIŤ,
- upozorni na chýbajúce kontroly a skúšky,
- navrhuj logické poradie technologických krokov,
- odpovedaj po slovensky,
- výsledok píš prehľadne a prakticky.
""",
        input=f"""
PÔVODNÝ POSTUP:
{text}

POŽIADAVKA POUŽÍVATEĽA:
{instruction}
"""
    )

    return response.output_text
