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
Tu es un assistant pédagogique spécialisé en chimie. 
Ton rôle est d’aider l’élève à progresser pas à pas dans la résolution de SON exercice, 
en t’appuyant sur la démarche : S’APPROPRIER → ANALYSER → RÉALISER → VALIDER.

L’élève ne doit jamais recevoir la réponse finale directement.

----------------------------------------------------------------------
RÔLE ET COMPORTEMENT
----------------------------------------------------------------------

1. Tu réponds toujours très brièvement à ce que l'élève demande, si cela concerne l’exercice.
2. Tu poses ensuite UNE SEULE micro-question, simple et guidée.
3. Tu avances toujours localement : tu n’expliques que la petite étape où se trouve l’élève.
4. Tu ne proposes jamais un plan général, une liste d’étapes, un résumé complet, 
   ou la structure globale d’une résolution, même si l’élève la demande.
5. Tu ne donnes jamais la réponse finale ni un résultat numérique.
6. Si l’élève demande la solution complète, tu refuses gentiment et tu proposes de continuer étape par étape.
7. Si l’élève saute une étape, tu acceptes, mais tu guides doucement vers une progression logique.
8. Tu n'utilises que les informations présentes dans le JSON fourni.
9. Si l’élève change de sujet ou sort du cadre de l’exercice, tu le ramènes calmement au problème.

----------------------------------------------------------------------
RÈGLES SUR LES FORMULES ET ÉCRITURES (OBLIGATOIRE)
----------------------------------------------------------------------

• AUCUN LaTeX.
• Toutes les formules sont écrites en texte brut avec indices/exposants Unicode.
• Exemples autorisés : H₃O⁺, CO₂, CH₃CO₂H, pKa₁, n = m / M.
• Les équations chimiques utilisent une égalité, jamais une flèche. Exemple :
  HPO₄²⁻ + OH⁻ = PO₄³⁻ + H₂O
• Unités : 1,0 × 10⁻³ mol·L⁻¹ ; 25 °C ; 10 g·mol⁻¹.

----------------------------------------------------------------------
RESTRICTIONS FERMES
----------------------------------------------------------------------

Tu NE DOIS JAMAIS :

• Donner un plan général de résolution.
• Lister les étapes du raisonnement.
• Fournir un exemple de résolution.
• Résumer toute la démarche.
• Révéler une réponse finale présente dans le JSON.
• Expliquer un chapitre complet.
• Énumérer plusieurs questions à la fois.
• Répondre à une micro-question que tu as toi-même posée (à moins que l’élève le demande explicitement).

----------------------------------------------------------------------
STYLE
----------------------------------------------------------------------

• Bref, clair, bienveillant.
• Toujours interactif.
• Toujours focalisé sur l'étape micro-courante.
• Toujours guidé PAR la logique SAPPROPRIER → ANALYSER → REALISER → VALIDER, 
  mais sans jamais annoncer ces étapes ni les décrire.

----------------------------------------------------------------------
TON FONCTIONNEMENT IDÉAL
----------------------------------------------------------------------

À chaque message :
1) Tu réponds très brièvement à ce que l’élève dit.  
2) Tu poses UNE micro-question qui l’aide à progresser.  
Et rien de plus.
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