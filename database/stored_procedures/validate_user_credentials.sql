DELIMITER //

DROP PROCEDURE IF EXISTS ValidateUserCredentials //

CREATE PROCEDURE ValidateUserCredentials(
    IN p_username VARCHAR(50),
    IN p_password VARCHAR(255)
)
BEGIN
    DECLARE v_user_id INT DEFAULT NULL;
    DECLARE v_user_name VARCHAR(30) DEFAULT NULL;
    DECLARE v_stored_password VARCHAR(255) DEFAULT NULL;
    DECLARE v_user_count INT DEFAULT 0;
    
    -- Buscar usuario por username o email
    SELECT COUNT(*), id, name, password 
    INTO v_user_count, v_user_id, v_user_name, v_stored_password
    FROM user 
    WHERE (username = p_username OR email = p_username) 
    AND status = 'active'
    LIMIT 1;
    
    -- Devolver resultados
    SELECT 
        v_user_count > 0 AND v_stored_password IS NOT NULL AS is_valid,
        v_user_id AS user_id,
        v_user_name AS user_name,
        v_stored_password AS stored_password;
        
END //

DELIMITER ;