"""
Enrichit le dataset Silver avec les réponses du modèle IA — format QCM (A/B/C/D).

Pourquoi ce format :
- Comparer du texte libre ("Leonard de Vinci" vs "Léonard de Vinci") génère des faux
  négatifs (bonne réponse jugée fausse à cause d'une formulation différente).
- En présentant des options lettrées, on élimine cette ambiguïté : soit le modèle
  donne la bonne lettre, soit non. C'est une mesure plus juste du taux de réussite réel.
- Le nombre de lettres s'adapte dynamiquement : 4 options pour les QCM (multiple),
  2 options pour les Vrai/Faux (boolean).
"""
import argparse
import logging
import random
import re
import time
from pathlib import Path

import ollama
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_PATH = Path("silver/questions_clean.parquet")
MODEL_NAME = "gemma2:2b"
LETTERS = ["A", "B", "C", "D"]

PROMPT_TEMPLATES = {
    "v1_simple": "Question : {question}\n{options_text}\nRéponds uniquement par la lettre de la bonne réponse.",
    "v2_strict": (
        "Tu es un expert en culture générale. Réponds UNIQUEMENT par une seule lettre "
        "parmi {letters}, sans phrase, sans ponctuation, sans explication.\n\n"
        "Question : {question}\n{options_text}\nRéponse :"
    ),
}


def build_options(row: pd.Series) -> tuple[dict[str, str], str]:
    """
    Construit les options lettrées pour une question (adapté au type : multiple ou boolean).
    Retourne (options: {lettre: texte}, lettre_correcte).
    Le shuffle est "seedé" par question_id : l'ordre des options est reproductible
    pour une même question, même si on relance le script avec un autre prompt
    (comparaison équitable entre variantes de prompt).
    """
    candidates = [("correct", row["correct_answer"])]

    for i in range(1, 4):
        col = f"incorrect_answer_{i}"
        if col in row and pd.notna(row[col]):
            candidates.append(("incorrect", row[col]))

    rng = random.Random(int(row["question_id"]))
    rng.shuffle(candidates)

    options = {}
    correct_letter = None
    for letter, (kind, text) in zip(LETTERS, candidates):
        options[letter] = text
        if kind == "correct":
            correct_letter = letter

    return options, correct_letter


def format_options_text(options: dict[str, str]) -> str:
    return "\n".join(f"{letter}. {text}" for letter, text in options.items())


def extract_letter(model_response: str, valid_letters: list[str]) -> str | None:
    """Extrait la première lettre valide (A/B/C/D) trouvée dans la réponse du modèle."""
    match = re.search(rf"\b([{''.join(valid_letters)}])\b", model_response.upper())
    return match.group(1) if match else None


def ask_model(question: str, options_text: str, letters: list[str], prompt_version: str, model: str = MODEL_NAME) -> tuple[str, float]:
    template = PROMPT_TEMPLATES[prompt_version]
    prompt = template.format(
        question=question,
        options_text=options_text,
        letters="/".join(letters),
    )
    start = time.perf_counter()
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    elapsed = time.perf_counter() - start
    return response["message"]["content"].strip(), elapsed


def enrich_dataset(df: pd.DataFrame, prompt_version: str) -> pd.DataFrame:
    results = []

    total = len(df)
    for idx, row in df.iterrows():
        options, correct_letter = build_options(row)
        letters = list(options.keys())
        options_text = format_options_text(options)

        try:
            raw_answer, elapsed = ask_model(row["question"], options_text, letters, prompt_version)
            ai_letter = extract_letter(raw_answer, letters)
        except Exception as e:
            logger.error(f"Erreur sur la question {idx}: {e}")
            raw_answer, ai_letter, elapsed = "", None, None

        results.append({
            "question_id": row["question_id"],
            "ai_answer_raw": raw_answer,
            "ai_answer_letter": ai_letter,
            "correct_letter": correct_letter,
            "ai_correct": ai_letter == correct_letter,
            "parse_error": ai_letter is None,
            "response_time": elapsed,
            "model_name": MODEL_NAME,
            "prompt_version": prompt_version,
            "num_options": len(options),
        })

        if len(results) % 20 == 0:
            logger.info(f"[{prompt_version}] Progression : {len(results)}/{total}")

    return df.merge(pd.DataFrame(results), on="question_id", how="left")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-version", choices=list(PROMPT_TEMPLATES.keys()), default="v2_strict")
    parser.add_argument("--sample", type=int, default=None)
    args = parser.parse_args()

    df = pd.read_parquet(INPUT_PATH)
    logger.info(f"{len(df)} questions chargées depuis {INPUT_PATH}")

    if args.sample:
        df = df.sample(args.sample, random_state=42)
        logger.info(f"Échantillon réduit à {len(df)} questions pour ce run")

    enriched = enrich_dataset(df, args.prompt_version)

    output_path = Path(f"silver/questions_enriched_{args.prompt_version}.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(output_path, index=False)

    taux_reussite = enriched["ai_correct"].mean() * 100
    taux_erreur_parsing = enriched["parse_error"].mean() * 100
    logger.info(f"Sauvegardé : {output_path}")
    logger.info(f"[{args.prompt_version}] Taux de bonnes réponses : {taux_reussite:.1f}%")
    logger.info(f"[{args.prompt_version}] Taux d'erreurs de parsing : {taux_erreur_parsing:.1f}%")


if __name__ == "__main__": 
    main()