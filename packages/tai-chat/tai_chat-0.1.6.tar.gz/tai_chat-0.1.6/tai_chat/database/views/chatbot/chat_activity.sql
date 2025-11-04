-- Vista para actividad de chats
SELECT 
    c.id as chat_id,
    c.title as chat_title,
    u.username,
    COUNT(m.id) as message_count,
    MAX(m.timestamp) as last_message_timestamp,
    COALESCE(SUM(tu.total_tokens), 0) as total_tokens_consumed,
    c.is_active
FROM chat c
INNER JOIN usuario u ON c.username = u.username
LEFT JOIN mensaje m ON c.id = m.chat_id
LEFT JOIN token_usage tu ON m.id = tu.message_id
GROUP BY c.id, c.title, u.username, c.is_active
ORDER BY last_message_timestamp DESC NULLS LAST;
