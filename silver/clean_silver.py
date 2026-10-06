"""
Nettoie les données brutes OpenTDB (bronze) et produit un fichier Silver en Parquet.

Transformations :
1. Parsing de incorrect_answers (stocké comme texte "['a', 'b', 'c']" dans le CSV)
   et dépliage en colonnes séparées incorrect_answer_1/2/3.
2. Suppression des doublons et vérification des valeurs manquantes.
3. Ajout d'un identifiant unique par question (question_id), utile pour relier
   proprement ce fichier aux réponses du modèle IA à l'étape suivante.
"""
import ast
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_PATH = Path("bronze/questions_raw.csv")
OUTPUT_PATH = Path("silver/questions_clean.parquet")


def parse_incorrect_answers(raw_value: str) -> list[str]:
    """Convertit la chaîne "['a', 'b', 'c']" en vraie liste Python."""
    try:
        return ast.literal_eval(raw_value)
    except (ValueError, SyntaxError):
        logger.warning(f"Impossible de parser : {raw_value}")
        return []


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Supprimer les doublons exacts sur la question
    before = len(df)
    df.drop_duplicates(subset=["question"], inplace=True)
    logger.info(f"Doublons supprimés : {before - len(df)}")

    # 2. Vérifier les valeurs manquantes
    missing = df.isnull().sum()
    if missing.any():
        logger.warning(f"Valeurs manquantes détectées :\n{missing[missing > 0]}")

    # 3. Parser incorrect_answers (texte -> vraie liste)
    df["incorrect_answers_list"] = df["incorrect_answers"].apply(parse_incorrect_answers)

    # 4. Déplier la liste en colonnes séparées (max 3 réponses incorrectes en multiple,
    #    1 seule en boolean -> les colonnes vides restent NaN, ce qui est normal)
    max_incorrect = df["incorrect_answers_list"].apply(len).max()
    for i in range(max_incorrect):
        df[f"incorrect_answer_{i + 1}"] = df["incorrect_answers_list"].apply(
            lambda lst, idx=i: lst[idx] if idx < len(lst) else None
        )

    df.drop(columns=["incorrect_answers", "incorrect_answers_list"], inplace=True)

    # 5. Identifiant unique par question (utile pour relier silver <-> réponses IA)
    df.reset_index(drop=True, inplace=True)
    df.insert(0, "question_id", df.index)

    return df


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    logger.info(f"{len(df)} questions chargées depuis {INPUT_PATH}")

    df_clean = clean_dataset(df)
    df_clean.to_parquet(OUTPUT_PATH, index=False)

    logger.info(f"Sauvegardé : {OUTPUT_PATH} ({len(df_clean)} questions)")
    logger.info(f"Colonnes finales : {df_clean.columns.tolist()}")


if __name__ == "__main__":
    main()