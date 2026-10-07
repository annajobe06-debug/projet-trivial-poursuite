# Jouons au Trivial Poursuite — Benchmark IA

Projet réalisé dans le cadre du M1 Data Engineering.

L'objectif est d'évaluer les performances d'un modèle d'IA sur des questions de culture générale en construisant un pipeline complet de data engineering.

## Objectifs

- Récupérer les questions depuis l'API Open Trivia Database (OpenTDB).
- Nettoyer et normaliser les données.
- Interroger un modèle d'IA local avec Ollama.
- Mesurer les réponses correctes et le temps de réponse.
- Tester différentes versions de prompt.
- Analyser les performances du modèle.
- Présenter les résultats avec un dashboard Streamlit.

## Architecture

Le projet suit une architecture en médaillon :

**Bronze → Silver → Gold**

- **Bronze** : données brutes OpenTDB au format CSV.
- **Silver** : données nettoyées et enrichies avec les réponses du modèle au format Parquet.
- **Gold** : indicateurs analytiques stockés dans DuckDB.

Les transformations entre les couches analytiques sont réalisées avec dbt selon l'organisation :

**Staging → Intermediate → Mart**

## Technologies

- Python
- OpenTDB API
- Ollama
- Gemma 2B
- Pandas
- Parquet
- dbt
- DuckDB
- Streamlit

## Benchmark

Le benchmark final porte sur **5 246 questions** avec le modèle **Gemma 2B** et le prompt `v2_strict`.

Résultats principaux :

- Accuracy : **60,0 %**
- Parse errors : **0 %**
- Easy : **68,08 %**
- Medium : **57,17 %**
- Hard : **53,06 %**

Deux versions de prompt ont été testées. La version `v1_simple` a été utilisée sur un échantillon de 20 questions, tandis que `v2_strict` a été utilisée pour le benchmark complet.

## Dashboard

Un dashboard interactif a été développé avec Streamlit afin de visualiser les performances :

- par catégorie ;
- par difficulté ;
- par type de question ;
- selon le temps de réponse.

Pour lancer le dashboard :

```bash
python -m streamlit run dashboard/app.py