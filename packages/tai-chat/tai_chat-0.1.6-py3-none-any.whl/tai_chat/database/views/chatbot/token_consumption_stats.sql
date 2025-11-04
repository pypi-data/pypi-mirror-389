-- Vista para estadísticas de consumo de tokens por usuario y fecha
SELECT 
    u.username,
    DATE(tu.timestamp) as date,
    SUM(tu.prompt_tokens) as total_prompt_tokens,
    SUM(tu.completion_tokens) as total_completion_tokens,
    SUM(tu.total_tokens) as total_tokens,
    SUM(tu.cost_usd) as total_cost_usd,
    COUNT(DISTINCT m.chat_id) as chat_count,
    MODE() WITHIN GROUP (ORDER BY tu.model_name) as most_used_model,
    MODE() WITHIN GROUP (ORDER BY tu.provider) as most_used_provider
FROM usuario u
LEFT JOIN chat c ON u.username = c.username
LEFT JOIN mensaje m ON c.id = m.chat_id
LEFT JOIN token_usage tu ON m.id = tu.message_id
WHERE tu.timestamp IS NOT NULL
GROUP BY u.username, DATE(tu.timestamp)
ORDER BY date DESC, total_tokens DESC;
