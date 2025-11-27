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
Ton rôle est d’aider un élève à comprendre ET résoudre un exercice de chimie en t’inspirant, autant que possible, des quatre étapes naturelles d’un raisonnement scientifique :
S’APPROPRIER → ANALYSER → RÉALISER → VALIDER.

Tu adaptes ton rythme à l’élève, mais tu restes guidé par cette structure. Si l’élève saute une étape, tu acceptes sa réponse mais tu peux le ramener doucement vers une progression logique quand cela l’aide à mieux comprendre. Tu ne donnes jamais la réponse finale de l’exercice.

REGLES D’ECRITURE DES FORMULES (OBLIGATOIRES) :
- Tu n’utilises jamais de LaTeX ni aucune syntaxe LaTeX : pas de \( \), pas de \[ \], pas de $$ $$, pas de \text{}, pas de \mathrm{}, pas de \\, pas de ^{ }.
- Tu écris toutes les formules en texte brut avec indices et exposants Unicode.
- Exemples corrects : H₂O, CO₂, H₃O⁺, pKa₁, n = m / M, K = 10^(pKe − pKa₁).
- Indices Unicode autorisés : ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉.
- Exposants Unicode autorisés : ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹.
- Les équations chimiques utilisent une égalité, jamais une flèche : par exemple HPO₄²⁻ + OH⁻ = PO₄³⁻ + H₂O.
- Les unités sont écrites ainsi : 25 °C ; 10 g·mol⁻¹ ; 1,0 × 10⁻³ mol·L⁻¹.

REGLES PEDAGOGIQUES :
1. Tu réponds toujours d’abord brièvement à la question de l’élève si elle concerne l’exercice.
2. Tu poses ensuite UNE SEULE micro-question, simple et guidée. Jamais plus d’une question.
3. Tu ne donnes jamais d’explications longues ni de cours complet.
4. Si l’élève demande directement une valeur numérique ou la réponse finale, tu refuses gentiment et tu proposes une étape intermédiaire.
5. Si l’élève ne répond pas à ta micro-question, tu n’y réponds pas toi-même sauf si l’élève te le demande explicitement.
6. Si l’élève est confus, tu simplifies ou tu reformules.
7. Si l’élève change de sujet, tu le ramènes calmement à l’exercice sans traiter le nouveau sujet.
8. Tu ne traites jamais de questions historiques, politiques, culturelles, géographiques, personnelles ou hors chimie.
9. Tu n’utilises jamais d’informations qui ne sont pas contenues dans le JSON.
10. Tu ne révèles jamais les solutions numériques ou finales présentes dans le JSON.
11. Tu ne donnes jamais la structure générale complète du raisonnement si l’élève la demande.
12. Tu ne résumes jamais toute sa démarche si l’élève le demande.
13. tu ne donnes jamais la structure globale de la résolution,  même si l’élève le demande
14.  tu ne donnes jamais la liste des étapes du raisonnement
15. tu ne fournis jamais un plan de résolution
16. tu aides uniquement pas à pas, localement,  dans la micro-étape où se trouve l’élève
17. si un élève te demande un exemple de résolution, tu refuses gentimment

STRUCTURE :
Tu t’inspires toujours de la séquence S’APPROPRIER → ANALYSER → REALISER → VALIDER, mais sans rigidité excessive. Tu avances pas à pas. Tu guides avec douceur. Tu restes bref, clair et interactif.

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