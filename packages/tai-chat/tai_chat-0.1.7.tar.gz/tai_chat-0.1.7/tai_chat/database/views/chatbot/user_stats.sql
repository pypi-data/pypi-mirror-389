-- Vista para estadísticas de usuarios
SELECT 
    u.username,
    u.email,
    COUNT(DISTINCT c.id) as total_chats,
    COUNT(DISTINCT CASE WHEN c.is_active = true THEN c.id END) as active_chats,
    COUNT(DISTINCT m.id) as total_messages,
    u.created_at,
    MAX(m.timestamp) as last_activity
FROM usuario u
LEFT JOIN chat c ON u.username = c.username
LEFT JOIN mensaje m ON c.id = m.chat_id
GROUP BY u.username, u.email, u.created_at
ORDER BY last_activity DESC NULLS LAST;