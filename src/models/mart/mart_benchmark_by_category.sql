SELECT
    category,
    COUNT(*) AS total_questions,
    SUM(correct_flag) AS correct_answers,
    ROUND(AVG(correct_flag) * 100, 2) AS accuracy_percent,
    ROUND(AVG(response_time), 2) AS avg_response_time
FROM {{ ref('int_answer') }}
WHERE prompt_version = 'v2_strict' 
GROUP BY category
ORDER BY accuracy_percent DESC

-- Dans quelles catégories le modèle est-il le plus performant ?