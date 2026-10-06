SELECT
    question_id,
    question,
    category,
    difficulty,
    type,                   -- 'multiple' ou 'boolean'
    correct_letter,
    ai_answer_letter,
    ai_correct,
    response_time,
    parse_error,
    model_name,
    prompt_version
FROM {{ source('silver', 'questions_enriched') }}