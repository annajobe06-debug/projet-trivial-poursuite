SELECT
    type,
    COUNT(*) AS total_questions,
    SUM(correct_flag) AS correct_answers,
    ROUND(AVG(correct_flag) * 100, 2) AS accuracy_percent,
    ROUND(AVG(response_time), 2) AS avg_response_time
FROM {{ ref('int_answer') }}
WHERE prompt_version = 'v2_strict' 
GROUP BY type
ORDER BY accuracy_percent DESC

-- Le type de question (Boolean ou Multiple Choice) influence-t-il les performances et le temps de réponse ?