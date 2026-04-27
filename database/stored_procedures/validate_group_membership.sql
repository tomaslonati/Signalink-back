DELIMITER //

CREATE PROCEDURE sp_validate_group_membership(
    IN p_group_id INT,
    IN p_user_id INT
)
BEGIN
    SELECT 
        CASE 
            WHEN g.id IS NOT NULL AND ugm.is_active = 1 THEN 1
            ELSE 0
        END as is_member
    FROM user_group g
    INNER JOIN user_group_member ugm ON g.id = ugm.group_id
    WHERE g.id = p_group_id 
    AND ugm.user_id = p_user_id
    AND ugm.is_active = 1
    LIMIT 1;
END //

DELIMITER ;