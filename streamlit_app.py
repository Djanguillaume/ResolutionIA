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
🔒 RÈGLE FONDAMENTALE : AVANCER D’ÉTAPE  
----------------------------------------------
Tu NE DOIS JAMAIS :  
❌ passer à l’étape suivante sans validation explicite  
❌ revenir à une étape précédente  
❌ décider seul d’un retour en appropriation  

Tu peux PROPOSER un passage d’étape uniquement si :  
• l’élève donne 2-3 réponses correctes consécutives,  
• il reformule correctement,  
• il montre qu’il maîtrise.  

Quand c’est le cas, tu termines ta réponse par :  

➡️ « On dirait que tu maîtrises très bien cette étape.  
Veux-tu passer à l’étape suivante ? (oui / non) »

Si l’élève répond « oui », tu passes à l’étape suivante.  
Si l’élève répond « non », tu continues dans l’étape.

====================================================
🔐 COMPORTEMENT STRICT À CHAQUE ÉTAPE
====================================================
À chaque message tu fournis :
• UNE seule question  
• UN seul indice OU UNE seule idée (pas les deux)  
• Jamais de résultat numérique  
• Jamais la solution complète  
• Jamais une aide appartenant à une autre étape 
====================================================
⛔ INTERDICTIONS ABSOLUES
====================================================
Tu ne dois jamais :
❌ donner des valeurs numériques  
❌ faire les calculs à la place de l’élève  
❌ proposer plusieurs questions à la fois  
❌ proposer plusieurs indices à la fois
❌ proposer plusieurs idées de résolution  
❌ résumer tout le corrigé  
❌ passer à l’étape suivante sans validation explicite 
❌ passer à l’étape précédente 
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
# ============================================
# 2) INITIALISATION STREAMLIT
# ============================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_step" not in st.session_state:
    st.session_state.current_step = "appropriation"  # démarre proprement

if "correct_streak" not in st.session_state:
    st.session_state.correct_streak = 0

if "waiting_for_confirmation" not in st.session_state:
    st.session_state.waiting_for_confirmation = False

CONFIRM_KEYS = {"oui", "ok", "passer", "j'ai compris", "j ai compris", "ok passer"}

# ============================================
# 3) QUESTION UTILISATEUR
# ============================================

if question:

    q_clean = question.lower().strip()

    # -------------------------
    # A) Si on attend confirmation
    # -------------------------
    if st.session_state.waiting_for_confirmation:

        st.session_state.chat_history.append({"role": "user", "content": question})

        if q_clean in CONFIRM_KEYS:

            # passage contrôlé
            next_map = {
                "appropriation": "analyse",
                "analyse": "réalisation",
                "realisation": "validation",
                "validation": "validation"
            }

            st.session_state.current_step = next_map[st.session_state.current_step]
            st.session_state.waiting_for_confirmation = False
            st.session_state.correct_streak = 0

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"✅ Très bien, nous passons à l’étape **{st.session_state.current_step}**.\nQue souhaites-tu faire maintenant ?"
            })

        else:
            # réponse normale ⇒ continuer dans l’étape
            st.session_state.waiting_for_confirmation = False
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "👍 Pas de souci, on reste dans cette étape. Que veux-tu préciser ?"
            })

        st.stop()

    # -------------------------
    # B) Salutations
    # -------------------------
    if q_clean in ["bonjour", "salut", "hello", "coucou"]:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "👋 Salut ! Nous pouvons commencer dès que tu veux."
        })
        st.stop()

    # -------------------------
    # C) Cas normal – envoi au modèle
    # -------------------------

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
            f"ÉTAPE_COURANTE = {st.session_state.current_step}\n"
            "Tu dois respecter toutes les règles ci-dessus sans jamais changer d’étape.\n"
            "N’utilise que les aides correspondant à ÉTAPE_COURANTE.\n\n"
            f"Contexte JSON : {json.dumps(contexte, ensure_ascii=False)}\n\n"
            f"Question de l’élève : {question}"
        )
    })

    # Appel API
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    answer = response.choices[0].message.content

    # enregistrement
    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append({"role": "assistant", "content": answer})

    # -------------------------
    # D) Détection "bonne maîtrise"
    # -------------------------
    good_patterns = ["je pense", "je comprends", "j'ai compris", "ça veut dire", "cela signifie"]

    if any(p in q_clean for p in good_patterns):
        st.session_state.correct_streak += 1
    else:
        st.session_state.correct_streak = 0

    # Si 3 bonnes réponses consécutives → proposer d’avancer
    if st.session_state.correct_streak >= 3:
        st.session_state.correct_streak = 0
        st.session_state.waiting_for_confirmation = True

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": (
                "✅ Tu sembles bien maîtriser cette étape.\n"
                "Veux-tu passer à l’étape suivante ? (oui / non)"
            )
        })
# ========== Rendu visuel du chat (nouveaux messages en haut) ==========
if st.session_state.chat_history:

    # On inverse l’ordre : les nouveaux messages d'abord
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
