SELECT
    question_id,
    category,
    difficulty,
    type,
    model_name,
    prompt_version,
    ai_correct,
    response_time,
    CASE
        WHEN ai_correct THEN 1
        ELSE 0
    END AS correct_flag
FROM {{ ref('stg_questions') }}