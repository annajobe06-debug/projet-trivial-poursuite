SELECT
    difficulty,
    COUNT(*) AS total_questions,
    SUM(correct_flag) AS correct_answers,
    ROUND(AVG(correct_flag) * 100, 2) AS accuracy_percent,
    ROUND(AVG(response_time), 2) AS avg_response_time
FROM {{ ref('int_answer') }}
WHERE prompt_version = 'v2_strict' 
GROUP BY difficulty
ORDER BY accuracy_percent DESC

-- La difficulté des questions influence-t-elle les performances et le temps de réponse ?