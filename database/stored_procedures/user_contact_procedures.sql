DELIMITER //

-- Add Contact Stored Procedure
DROP PROCEDURE IF EXISTS AddContact //
CREATE PROCEDURE AddContact(
    IN p_user_id INT,
    IN p_contact_id INT
)
BEGIN
    DECLARE v_active_users INT;
    
    -- Verify both users exist and are active
    SELECT COUNT(*) INTO v_active_users
    FROM user 
    WHERE id IN (p_user_id, p_contact_id) 
    AND status = 'active';
    
    IF v_active_users != 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'One or both users not found or inactive';
    END IF;
    
    INSERT INTO user_contact (user_id, contact_id)
    VALUES (p_user_id, p_contact_id);
    
    SELECT TRUE as success;
END //

-- Remove Contact Stored Procedure
DROP PROCEDURE IF EXISTS RemoveContact //
CREATE PROCEDURE RemoveContact(
    IN p_user_id INT,
    IN p_contact_id INT
)
BEGIN
    DELETE FROM user_contact 
    WHERE user_id = p_user_id 
    AND contact_id = p_contact_id;
    
    SELECT ROW_COUNT() as deleted;
END //

-- Get User Contacts Stored Procedure
DROP PROCEDURE IF EXISTS GetUserContacts //
CREATE PROCEDURE GetUserContacts(IN p_user_id INT)
BEGIN
    SELECT u.id, u.username, u.name, u.surname, u.email, u.created_at,
           uc.created_at as contact_added_at
    FROM user_contact uc
    JOIN user u ON uc.contact_id = u.id
    WHERE uc.user_id = p_user_id 
    AND u.status = 'active'
    ORDER BY u.name, u.surname;
END //

-- Get Users Who Have Contact Stored Procedure
DROP PROCEDURE IF EXISTS GetUsersWhoHaveContact //
CREATE PROCEDURE GetUsersWhoHaveContact(IN p_contact_id INT)
BEGIN
    SELECT u.id, u.username, u.name, u.surname, u.email, u.created_at,
           uc.created_at as contact_added_at
    FROM user_contact uc
    JOIN user u ON uc.user_id = u.id
    WHERE uc.contact_id = p_contact_id 
    AND u.status = 'active'
    ORDER BY u.name, u.surname;
END //

-- Check Contact Status Stored Procedure
DROP PROCEDURE IF EXISTS CheckContactStatus //
CREATE PROCEDURE CheckContactStatus(
    IN p_user_id INT,
    IN p_contact_id INT
)
BEGIN
    SELECT 
        EXISTS(
            SELECT 1 FROM user_contact 
            WHERE user_id = p_user_id AND contact_id = p_contact_id
        ) as is_contact,
        EXISTS(
            SELECT 1 FROM user_contact 
            WHERE (user_id = p_user_id AND contact_id = p_contact_id)
            OR (user_id = p_contact_id AND contact_id = p_user_id)
            HAVING COUNT(*) = 2
        ) as is_mutual;
END //

-- Get Mutual Contacts Stored Procedure
DROP PROCEDURE IF EXISTS GetMutualContacts //
CREATE PROCEDURE GetMutualContacts(IN p_user_id INT)
BEGIN
    SELECT u.id, u.username, u.name, u.surname, u.email,
           uc1.created_at as added_by_user,
           uc2.created_at as added_by_contact
    FROM user_contact uc1
    JOIN user_contact uc2 ON uc1.user_id = uc2.contact_id 
    AND uc1.contact_id = uc2.user_id
    JOIN user u ON uc1.contact_id = u.id
    WHERE uc1.user_id = p_user_id 
    AND u.status = 'active'
    ORDER BY u.name, u.surname;
END //

-- Search Contacts Stored Procedure
DROP PROCEDURE IF EXISTS SearchContacts //
CREATE PROCEDURE SearchContacts(
    IN p_user_id INT,
    IN p_search_term VARCHAR(100)
)
BEGIN
    SET @search_pattern = CONCAT('%', p_search_term, '%');
    
    SELECT u.id, u.username, u.name, u.surname, u.email,
           uc.created_at as contact_added_at
    FROM user_contact uc
    JOIN user u ON uc.contact_id = u.id
    WHERE uc.user_id = p_user_id 
    AND u.status = 'active'
    AND (u.name LIKE @search_pattern 
         OR u.surname LIKE @search_pattern 
         OR u.username LIKE @search_pattern
         OR u.email LIKE @search_pattern)
    ORDER BY u.name, u.surname;
END //

-- Get Contact Count Stored Procedure
DROP PROCEDURE IF EXISTS GetContactCount //
CREATE PROCEDURE GetContactCount(IN p_user_id INT)
BEGIN
    SELECT COUNT(*) as count
    FROM user_contact uc
    JOIN user u ON uc.contact_id = u.id
    WHERE uc.user_id = p_user_id 
    AND u.status = 'active';
END //

DELIMITER ;