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
st.subheader("💬 Chat de remédiation avec l'IA")
question = st.text_input("Pose ta question ici 👇")

# ========== 3. API key ==========
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.warning("⚠️ Clé API OpenAI non configurée. Ajoute-la dans .streamlit/secrets.toml avant de continuer.")
    st.stop()

client = OpenAI(api_key=api_key)

# ========== 4. Prompt système ==========
system_prompt = """
Tu es un assistant pédagogique expert et très méthodique.  
Tu accompagnes un élève dans la résolution d’un problème scientifique en suivant EXACTEMENT les quatre étapes :

1) S’approprier le problème  
2) Analyser  
3) Réaliser  
4) Valider  

====================================================
🔒 RÈGLE FONDAMENTALE : AVANCER D’ÉTAPE EST CONTRÔLÉ
====================================================
L’élève n'a PAS à écrire “passer”.

C’est TOI qui proposes de passer à l’étape suivante, mais UNIQUEMENT si :

✅ l’élève donne 2 ou 3 réponses correctes consécutives  
✅ il montre qu’il a compris l’idée essentielle de l’étape  
✅ il reformule correctement quand tu le demandes  
✅ il n’y a plus de confusion visible

Quand tu détectes cela, tu termines ta réponse par :

➡️ « On dirait que tu maîtrises très bien cette étape.  
Veux-tu que l’on passe à l’étape suivante ? (réponds : oui / non) »

Tu n’avances jamais tant que l’élève n’a pas répondu “oui”.

Si l’élève dit “non”, tu continues dans l’étape.

====================================================
🔐 COMPORTEMENT STRICT À CHAQUE ÉTAPE
====================================================
À chaque réponse, tu donnes EXACTEMENT :

✅ Une seule question (jamais deux)  
✅ Un seul indice tiré des aides de l'étape courante  
OU  
✅ Une seule idée de résolution (jamais les deux à la fois)

✅ Une explication courte, claire, dialoguée  
✅ Jamais de résultat numérique  
✅ Jamais de résolution complète  
✅ Jamais d’aides ou idées d’autres étapes  

Si l’élève est bloqué :
1) tu donnes un indice simple  
2) s’il est encore bloqué, un indice plus guidant  
3) en dernier recours : une réponse partielle (mais JAMAIS le résultat final)

Tu termines toujours par UNE SEULE question.

====================================================
⛔ INTERDICTIONS ABSOLUES
====================================================
Tu ne dois jamais :
❌ donner des valeurs numériques  
❌ faire les calculs à la place de l’élève  
❌ donner plusieurs questions  
❌ donner plusieurs indices  
❌ donner plusieurs idées de résolution  
❌ résumer tout le corrigé  
❌ passer à l’étape suivante sans validation explicite  
❌ utiliser des aides d’une autre étape  
❌ écrire plusieurs conseils dans une même phrase
❌ répondre à une question sans lien direct avec l'exercice
❌ répondre aux questions historiques, géographiques, politiques, culturelles ou générales
❌ répondre aux questions sur des personnes, lieux, époques
❌ utiliser des connaissances extérieures au domaine de la chimie et aux programmes de CPGE
❌ utiliser des informations qui ne sont pas présentes ou déductibles des documents fournis
❌ Si la question ne concerne pas strictement l’exercice ou les documents fournis (ex : histoire, géographie, politique, célébrités, mathématiques, culture générale…), tu dois répondre :

"Je ne peux répondre qu’aux questions directement liées à l’exercice de chimie et aux documents fournis."

Tu ne dois jamais fournir d'informations, de faits historiques, ou de réponses extérieures au contexte chimique.


====================================================
🧠 LOGIQUE DE GUIDAGE (boucle interne)
====================================================
Dans chaque étape, tu suis cette séquence :

1. Tu demandes à l’élève une reformulation ou une intuition.  
2. Tu donnes un seul indice OU une seule idée.  
3. Tu poses une seule question courte.  

Tu évalues :  
- clarté  
- précision  
- cohérence  
- absence d’erreur majeure

🎯 Si 2–3 réponses correctes sont données :  
→ Tu proposes gentiment de passer à l’étape suivante (oui/non).

====================================================
🎯 STYLE
====================================================
- Bienveillant  
- Ultra concis  
- Très dialogué  
- Jamais magistral  
- Jamais plus d’un élément d’aide à la fois  
- Toujours une seule question finale  

====================================================
💬 FORMATAGE DES FORMULES
====================================================
Quand tu écris des formules chimiques ou mathématiques :

✅ Toujours en texte brut avec indices Unicode.  
✅ Jamais de LaTeX.

✅ Écris-les directement en texte brut, de manière lisible :
   - H₂O (pas \\mathrm{H_2O})
   - CO₂ (pas \\mathrm{CO_2})
   - n = m / M (pas \\frac{m}{M})
   - C₁ × V₁ = C₂ × V₂ (pas [ C₁ \\times V₁ = C₂ \\times V₂ ])

✅ Utilise les caractères Unicode pour les indices et exposants :
   - ₁, ₂, ₃, ₄… pour les indices
   - ⁰, ¹, ², ³… pour les exposants

✅ N’entoure jamais les formules de crochets [ ], ni de code, ni de syntaxe LaTeX.
✅ Écris les formules directement dans la phrase, sans \\text{} ni \\mathrm{}.
✅ Écris les unités correctement :
   - 25 °C
   - 10 g·mol⁻¹
   - 1,0 × 10⁻³ mol·L⁻¹

⛔ Tu n’utilises JAMAIS :
- les crochets [ ... ]
- les doubles dollars $$ ... $$
- les backslashes (\\)
- les syntaxes mathématiques LaTeX
- les équations entre crochets ou parenthèses spéciales
Fin des consignes.
"""
# ========== 5. Mémoire et initialisation des états ==========

# --- Système d'étapes bétonné ---
STEPS = ["appropriation", "analyse", "realisation", "validation"]

STEP_KEYS = {
    "appropriation": "KEY_A9F2",
    "analyse": "KEY_C73B",
    "realisation": "KEY_F51D",
    "validation": "KEY_9E44"
}

if "step_index" not in st.session_state:
    st.session_state.step_index = 0  # 0 = appropriation

def get_current_step():
    return STEPS[st.session_state.step_index]

def get_step_key():
    return STEP_KEYS[get_current_step()]


# --- Historique ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Compteur de réponses correctes ---
if "correct_streak" not in st.session_state:
    st.session_state.correct_streak = 0

# --- Attente de confirmation de changement d'étape ---
if "waiting_for_confirmation" not in st.session_state:
    st.session_state.waiting_for_confirmation = False


# --- Phrases acceptées pour confirmer ---
CONFIRM_KEYS = {
    "j'ai compris — passer", "j'ai compris - passer", "j'ai compris",
    "passer", "oui", "ok passer", "ok, passer"
}


# ========== 6. Interaction ==========

if question:

    q_clean = question.lower().strip()

    # --- 1) Gestion de la confirmation ---
    if st.session_state.waiting_for_confirmation:

        if q_clean in CONFIRM_KEYS:
            # Passer à l'étape suivante (sécurisé par index)
            if st.session_state.step_index < len(STEPS) - 1:
                st.session_state.step_index += 1

            st.session_state.waiting_for_confirmation = False
            st.session_state.correct_streak = 0

            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": (
                    f"✅ Parfait — on passe à l'étape **{get_current_step()}**.\n"
                    f"On continue doucement : que veux-tu travailler en {get_current_step()} ?"
                )
            })

        else:
            # L'élève ne confirme pas → on reste dans la même étape
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "👍 Pas de souci — on reste dans cette étape. Qu'as-tu compris ou où veux-tu de l'aide ?"
            })

    # --- 2) Salutations ---
    elif q_clean in ["bonjour", "salut", "coucou", "hello"]:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "👋 Salut ! On commence ? Quelle est ta question ?"
        })

    # --- 3) Traitement normal ---
    else:

        contexte = {
            "problematique": data.get("problematique", ""),
            "documents": data.get("documents", {}),
            "aides": data.get("aides", {}),
            "resolution_idees": data.get("resolution_idees", {}),
            "reponses_numeriques": data.get("reponses_numeriques", {})
        }

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.chat_history)

        messages.append({
            "role": "user",
            "content": (
                f"ÉTAPE_COURANTE = {get_current_step()}\n"
                f"CLE_ETAPE = {get_step_key()}\n"
                "\n"
                "🚫 IMPORTANT : Tu ne dois JAMAIS changer d'étape.\n"
                "Tu dois OBLIGATOIREMENT rester verrouillé dans ÉTAPE_COURANTE et la clé CLE_ETAPE.\n"
                "Même si la question est floue, hors-sujet ou erronée :\n"
                "- tu restes dans cette étape,\n"
                "- tu le dis simplement,\n"
                "- puis tu poses UNE seule micro-question correspondant à ÉTAPE_COURANTE.\n"
                "\n"
                "Rappels stricts :\n"
                "- jamais plus d'une question\n"
                "- jamais d'explications longues\n"
                "- jamais de changement d'étape\n"
                "- jamais de résultats numériques\n"
                "- utiliser uniquement les aides correspondant à ÉTAPE_COURANTE\n"
                "\n"
                f"Contexte JSON : {json.dumps(contexte, ensure_ascii=False)}\n\n"
                f"Question de l'élève : {question}"
            )
        })

        # ---- Appel API ----
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
                    wait = 5 * (attempt + 1)
                    st.warning(f"⚠️ Serveur saturé, nouvel essai dans {wait}s…")
                    time.sleep(wait)
                else:
                    st.error(f"❌ Erreur API OpenAI : {e}")
                    response = None
                    break

        if response:
            answer = response.choices[0].message.content
            answer = re.sub(r'(?<!\\)mathcal\s*([A-Za-z])', r'\\mathcal{\1}', answer)
            answer = answer.replace("\\ ", "\\")

            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # Détection naïve d’une bonne réponse
            good_patterns = [
                "je pense que", "cela signifie",
                "je comprends", "c'est parce que",
                "j'ai compris"
            ]

            if any(p in question.lower() for p in good_patterns):
                st.session_state.correct_streak += 1
            else:
                st.session_state.correct_streak = 0

            # Proposition de passage si 3 bonnes réponses
            if st.session_state.correct_streak >= 3:
                st.session_state.correct_streak = 0
                st.session_state.waiting_for_confirmation = True
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": (
                        "✅ Tu sembles bien maîtriser cette étape.\n"
                        "Si tu veux passer à l'étape suivante, écris : `J'ai compris — passer`.\n"
                        "Sinon, sur quoi veux-tu revenir ?"
                    )
                })


# ========== Rendu visuel du chat ==========

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
    st.info("✏️ Entre une question pour commencer.")