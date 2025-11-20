# Code mis à jour pour utiliser l'API OpenAI (GPT-4o mini)
# --------------------------------------------------------
# ⚠️ Remplace "OPENAI_API_KEY" dans secrets.toml
# --------------------------------------------------------

import streamlit as st
import json
import re
from openai import OpenAI
import time

st.set_page_config(page_title="Résolution de problème", layout="wide")

# ----- STYLE GLOBAL -----
st.markdown("""
<style>
body {
    background-color: #f5f7fb;
    color: #1a1a1a;
}

.chat-bubble-user {
    background-color: #dff1ff;
    color: #000000;
    padding: 12px 16px;
    border-radius: 15px;
    margin-bottom: 10px;
    max-width: 80%;
    margin-left: auto;
    border: 1px solid #b7e1ff;
    font-size: 1rem;
}

.chat-bubble-assistant {
    background-color: #eef0f5;
    color: #000000;
    padding: 12px 16px;
    border-radius: 15px;
    margin-bottom: 10px;
    max-width: 80%;
    margin-right: auto;
    border: 1px solid #d4d7dd;
    font-size: 1rem;
}

.chat-container {
    padding: 15px;
    border-radius: 12px;
    background: #ffffff;
    margin-bottom: 20px;
    border: 1px solid #e1e1e1;
}

</style>
""", unsafe_allow_html=True)

st.title("📘 Résolution de problème")

# ========== 1. Upload ==========
# Charger automatiquement un JSON par défaut
with open("Résolution.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.success("JSON d'exemple chargé automatiquement.")
# ========== 2. Chat ==========
st.subheader("💬 Echange avec l'IA")
question = st.text_input("Pose ta question ici 👇")

# ========== 3. API key ==========
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.warning("⚠️ Clé API OpenAI non configurée. Ajoute-la dans .streamlit/secrets.toml avant de continuer.")
    st.stop()

client = OpenAI(api_key=api_key)

# ========== 4. Prompt système ==========

system_prompt = """
Tu es un assistant pédagogique très structuré.
Ton rôle est d’aider un élève à comprendre ET résoudre un exercice de chimie en suivant, autant que possible, les quatre étapes naturelles d’un raisonnement scientifique :
S’APPROPRIER → ANALYSER → RÉALISER → VALIDER.

Tu peux adapter ton rythme en fonction de l’élève, mais tu t’inspires toujours de ces étapes pour structurer ton guidage.

Si l’élève saute une étape, tu acceptes sa réponse mais tu le ramènes doucement vers la structure quand c’est utile pour l’aider à progresser.

Ton objectif : faire progresser l’élève pas à pas, avec clarté, sans jamais lui donner la réponse finale.

RÈGLES DE FORMATION DES FORMULES — OBLIGATOIRES :
=================================================
❗ Tu n'utilises JAMAIS :
- \( ... \)
- \[ ... \]
- $$ ... $$
- \text{}
- \mathrm{}
- les backslashes \
- les syntaxes LaTeX, même partielles
- les exposants LaTeX du type ^{2}

❗ Tu n’entoures JAMAIS une formule avec du LaTeX.

Tu écris TOUTES les formules en TEXTE BRUT, avec indices et exposants Unicode :
- H₂O
- CO₂
- H₃O⁺
- pKa₁
- n = m / M
- K = 10^(pKe − pKa₁)

Tu écris ce que tu DOIS écrire avec :
- ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉ pour les indices
- ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ pour les exposants

Tu écris les équations chimiques avec des égalités et pas des flèches:
- exemple : HPO₄²⁻ + OH⁻ = PO₄³⁻ + H₂O

Tu écris toujours les unités comme :
- 25 °C
- 10 g·mol⁻¹
- 1,0 × 10⁻³ mol·L⁻¹

RÈGLES ABSOLUES :
- tu réponds toujours d'abord à la question de l'élève
- puis tu poses UNE SEULE micro-question (facile, guidée)
- jamais plus d'une question par message
- pas de cours complet
- pas de longues explications
- si l'élève est confus : tu simplifies, tu reformules
- si l'élève change de sujet : tu le ramènes gentiment à l'exercice sans répondre à sa question
- si l'élève propose un lien entre chimie et un autre sujet : tu le ramènes gentiment à l'exercice sans répondre à sa question
- tu n'inventes jamais d'informations qui ne sont pas dans le JSON
- tu ne révèles JAMAIS les solutions numériques du JSON
- tu ne réponds jamais aux questions historiques, géographiques, politiques, culturelles ou générales
- tu ne réponds jamais aux questions sur des personnes, lieux, époques
- tu n'utilises jamais des connaissances extérieures au domaine de la chimie et aux programmes de CPGE
- tu ne donnes jamais la structure globale du raisonnement si l'élève te le demande
- tu ne résumes jamais la démarche de l'élève s'il te le demande

"""

# ========== 5. Mémoire et initialisations ==========

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "correct_streak" not in st.session_state:
    st.session_state.correct_streak = 0

# ========== 6. Interaction ==========

if question:

    q_clean = question.lower().strip()

    # --- Salutations simples ---
    if q_clean in ["bonjour", "salut", "coucou", "hello"]:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "👋 Salut ! Dis-moi ce qui te pose problème dans l'exercice."
        })

    else:

        # Contexte JSON (problématique + docs + aides)
        contexte = {
            "problematique": data.get("problematique", ""),
            "documents": data.get("documents", {}),
            "aides": data.get("aides", {}),
            "resolution_idees": data.get("resolution_idees", {}),
            "reponses_numeriques": data.get("reponses_numeriques", {})
        }

        # Messages envoyés à l'API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.chat_history)
        messages.append({
            "role": "user",
            "content": (
                "Voici le contexte JSON pour répondre :\n"
                f"{json.dumps(contexte, ensure_ascii=False, indent=2)}\n\n"
                f"Question de l'élève : {question}\n\n"
                "Rappelle-toi : réponds d'abord à sa question, puis une seule micro-question."
            )
        })

        # --- Appel API OpenAI avec retry ---
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    st.error(f"❌ Erreur OpenAI : {e}")
                    response = None
                    break

        # --- Traitement réponse ---
        if response:
            answer = response.choices[0].message.content

            # Nettoyage latex léger
            answer = re.sub(r'(?<!\\)mathcal\s*([A-Za-z])', r'\\mathcal{\1}', answer)

            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

# ========== 7. Affichage du chat ==========

if st.session_state.chat_history:

    reversed_history = list(reversed(st.session_state.chat_history))

    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    for msg in reversed_history:
        if msg["role"] == "user":
            st.markdown(
                f"<div class='chat-bubble-user'>👤 <strong>Élève</strong><br>{msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-bubble-assistant'>🤖 <strong>IA</strong><br>{msg['content']}</div>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("✏️ Pose une question pour commencer.")