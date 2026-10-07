import requests
import pandas as pd
import html
import time
import os


# =========================================================
# Configuration
# =========================================================

API_URL = "https://opentdb.com/api.php"
TOKEN_URL = "https://opentdb.com/api_token.php"

OUTPUT_PATH = "bronze/questions_raw.csv"

BATCH_SIZE = 50
WAIT_SECONDS = 5

os.makedirs("bronze", exist_ok=True)


# =========================================================
# Création du token OpenTDB
# =========================================================

def create_token():

    response = requests.get(
        TOKEN_URL,
        params={"command": "request"}
    )

    response.raise_for_status()

    data = response.json()

    if data["response_code"] != 0:
        raise RuntimeError(
            f"Impossible de créer le token : "
            f"{data['response_code']}"
        )

    print("Token OpenTDB obtenu.")

    return data["token"]


# =========================================================
# 1. Création du token
# =========================================================

token = create_token()


# =========================================================
# 2. Récupération des questions
# =========================================================

rows = []

total_requests = 0


while True:

    params = {
        "amount": BATCH_SIZE,
        "token": token
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        total_requests += 1

        # -------------------------------------------------
        # Rate limit
        # -------------------------------------------------

        if response.status_code == 429:

            print(
                "Rate limit atteint."
            )

            print(
                f"Attente de {WAIT_SECONDS} secondes..."
            )

            time.sleep(WAIT_SECONDS)

            continue


        response.raise_for_status()

        data = response.json()

        response_code = data["response_code"]


        # =================================================
        # Code 0 : succès
        # =================================================

        if response_code == 0:

            results = data["results"]

            for item in results:

                rows.append({

                    "category": html.unescape(
                        item["category"]
                    ),

                    "difficulty": item[
                        "difficulty"
                    ],

                    "question": html.unescape(
                        item["question"]
                    ),

                    "correct_answer": html.unescape(
                        item["correct_answer"]
                    ),

                    "incorrect_answers": [
                        html.unescape(answer)
                        for answer in item[
                            "incorrect_answers"
                        ]
                    ],

                    "type": item["type"]
                })


            print(
                f"+ {len(results)} questions"
            )

            print(
                f"Total actuel : {len(rows)}"
            )


            # -------------------------------------------------
            # Sauvegarde intermédiaire
            # -------------------------------------------------

            df_temp = pd.DataFrame(rows)

            df_temp.to_csv(
                OUTPUT_PATH,
                index=False
            )


            # -------------------------------------------------
            # Si moins de BATCH_SIZE questions reçues
            # -------------------------------------------------

            if len(results) < BATCH_SIZE:

                print(
                    "Dernier lot récupéré."
                )

                break


            # -------------------------------------------------
            # On retente un plein lot de 50 au prochain appel
            # -------------------------------------------------

            BATCH_SIZE = 50

            # Respect de la limite OpenTDB

            print(
                f"Attente de {WAIT_SECONDS} secondes..."
            )

            time.sleep(WAIT_SECONDS)


        # =================================================
        # Code 1 : pas assez de questions pour BATCH_SIZE
        # =================================================

        elif response_code == 1:

            if BATCH_SIZE == 1:

                print(
                    "Plus aucune question disponible, "
                    "même pour une seule."
                )

                break

            BATCH_SIZE = max(1, BATCH_SIZE // 2)

            print(
                "Pas assez de questions pour un lot complet."
            )

            print(
                f"Réduction de la taille du lot à {BATCH_SIZE}..."
            )

            print(
                f"Attente de {WAIT_SECONDS} secondes..."
            )

            time.sleep(WAIT_SECONDS)

            continue


        # =================================================
        # Code 3 : token invalide
        # =================================================

        elif response_code == 3:

            print(
                "ERREUR : token invalide."
            )

            break


        # =================================================
        # Code 4 : token épuisé
        # =================================================

        elif response_code == 4:

            print(
                "Token épuisé."
            )

            print(
                "Toutes les questions disponibles "
                "pour cette collecte ont été récupérées."
            )

            break


        # =================================================
        # Autre code
        # =================================================

        else:

            print(
                f"Code OpenTDB inattendu : {response_code}"
            )

            break


    except requests.RequestException as e:

        print(
            f"Erreur HTTP : {e}"
        )

        print(
            f"Nouvelle tentative dans {WAIT_SECONDS} secondes..."
        )

        time.sleep(WAIT_SECONDS)


# =========================================================
# 3. Sauvegarde finale
# =========================================================

df = pd.DataFrame(rows)

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 4. Résumé
# =========================================================

print("\n")
print("==========================================")
print("INGESTION TERMINÉE")
print("==========================================")

print(
    f"Questions récupérées : {len(df)}"
)

print(
    f"Requêtes effectuées : {total_requests}"
)

print(
    f"Fichier : {OUTPUT_PATH}"
)

if not df.empty:

    print("\nRépartition par difficulté :")

    print(
        df["difficulty"].value_counts()
    )

    print("\nRépartition par type :")

    print(
        df["type"].value_counts()
    )

    print("\nNombre de catégories :")

    print(
        df["category"].nunique()
    )

print("==========================================")