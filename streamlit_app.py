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

# --- Nouveau système d'étapes robuste ---
if "step_index" not in st.session_state:
    st.session_state.step_index = 0  # 0 = appropriation

STEPS = ["appropriation", "analyse", "realisation", "validation"]

def get_current_step():
    return STEPS[st.session_state.step_index]


# Historique
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# compteur de bonnes réponses consécutives
if "correct_streak" not in st.session_state:
    st.session_state.correct_streak = 0

# l'IA attend confirmation pour passer à l'étape suivante
if "waiting_for_confirmation" not in st.session_state:
    st.session_state.waiting_for_confirmation = False

# valeurs acceptées pour confirmer le passage d'étape
CONFIRM_KEYS = {
    "j'ai compris — passer", "j'ai compris - passer",
    "j'ai compris", "passer", "oui", "ok passer", "ok, passer"
}


# ========== 6. Interaction ==========

if question:

    q_clean = question.lower().strip()
    current_step = get_current_step()

    # --- 1) Si on attend une confirmation pour changer d'étape ---
    if st.session_state.waiting_for_confirmation:

        if q_clean in CONFIRM_KEYS:

            # --- Nouveau système : on incrémente simplement l’index ---
            if st.session_state.step_index < len(STEPS) - 1:
                st.session_state.step_index += 1

            new_step = get_current_step()
            st.session_state.waiting_for_confirmation = False
            st.session_state.correct_streak = 0

            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": (
                    f"✅ Très bien — on passe à l'étape **{new_step}**. "
                    f"Que veux-tu travailler en **{new_step}** ?"
                )
            })

        else:
            # pas une confirmation -> réponse normale
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "👍 Pas de souci — on reste sur cette étape. Qu’est-ce qui bloque ?"
            })


    # --- 2) Salutations ---
    elif q_clean in ["bonjour", "salut", "coucou", "hello"]:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "👋 Salut ! On commence ? Pose-moi ta première question."
        })


    # --- 3) Cas normal : envoi au modèle ---
    else:

        # Contexte JSON transmis au modèle
        contexte = {
            "problematique": data.get("problematique", ""),
            "documents": data.get("documents", {}),
            "aides": data.get("aides", {}),
            "resolution_idees": data.get("resolution_idees", {}),
            "reponses_numeriques": data.get("reponses_numeriques", {})
        }

        # messages envoyés
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.chat_history)

        messages.append({
            "role": "user",
            "content": (
                f"ÉTAPE_COURANTE = {current_step}\n"
                "Tu dois respecter STRICTEMENT les règles suivantes :\n"
                "\n"
                "🚫 IMPORTANT : Même si la question de l’élève est floue ou hors sujet,\n"
                "TU NE DOIS JAMAIS revenir spontanément à une étape précédente.\n"
                "Tu RESTES strictement dans ÉTAPE_COURANTE.\n"
                "\n"
                "1️⃣ Si l’élève pose une question :\n"
                "- commence par répondre à SA question\n"
                "- puis pose UNE seule micro-question si nécessaire\n"
                "\n"
                "2️⃣ Si l’élève ne pose pas de question :\n"
                "- propose UNE seule micro-question guidée pour avancer\n"
                "\n"
                "3️⃣ Interdictions :\n"
                "- jamais plus d’une question\n"
                "- pas de cours, pas de longs textes\n"
                "- pas de sauts d’étape\n"
                "- pas de retour à une étape précédente\n"
                "\n"
                f"Contexte JSON : {json.dumps(contexte, ensure_ascii=False)}\n\n"
                f"Question de l'élève : {question}"
            )
        })

        # Appel API avec retry
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
                    st.warning(f"⚠️ Serveur saturé. Nouvel essai dans {wait}s...")
                    time.sleep(wait)
                else:
                    st.error(f"❌ Erreur API OpenAI : {e}")
                    response = None
                    break

        # Traitement de la réponse
        if response:
            answer = response.choices[0].message.content

            # nettoyage
            answer = re.sub(r'(?<!\\)mathcal\s*([A-Za-z])', r'\\mathcal{\1}', answer)
            answer = answer.replace("\\ ", "\\")

            # on enregistre l'échange
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # logique d’avancement
            good_patterns = ["je pense que", "cela signifie", "je comprends", "c'est parce que", "j'ai compris"]
            if any(p in question.lower() for p in good_patterns):
                st.session_state.correct_streak += 1
            else:
                st.session_state.correct_streak = 0

            # l’IA propose de passer après maîtrise
            if st.session_state.correct_streak >= 3:
                st.session_state.correct_streak = 0
                st.session_state.waiting_for_confirmation = True

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": (
                        "✅ Tu sembles bien maîtriser cette étape.\n"
                        "Pour passer à l'étape suivante, écris : `J'ai compris — passer`.\n"
                        "Sinon, dis-moi ce que tu veux approfondir."
                    )
                })


# ========== Rendu visuel du chat (nouveaux messages en haut) ==========

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
    st.info("✏️ Entre une question pour commencer la résolution.")