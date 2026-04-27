DELIMITER //

-- Create User Stored Procedure
DROP PROCEDURE IF EXISTS CreateUser //
CREATE PROCEDURE CreateUser(
    IN p_name VARCHAR(30),
    IN p_surname VARCHAR(30),
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_password VARCHAR(255)
)
BEGIN
    INSERT INTO user (name, surname, username, email, password, status)
    VALUES (p_name, p_surname, p_username, p_email, p_password, 'active');
    
    SELECT LAST_INSERT_ID() as user_id;
END //

-- Get User By ID Stored Procedure
DROP PROCEDURE IF EXISTS GetUserById //
CREATE PROCEDURE GetUserById(IN p_user_id INT)
BEGIN
    SELECT id, name, surname, username, email, status, created_at
    FROM user 
    WHERE id = p_user_id AND status = 'active';
END //

-- Get User By Username or Email Stored Procedure
DROP PROCEDURE IF EXISTS GetUserByUsernameOrEmail //
CREATE PROCEDURE GetUserByUsernameOrEmail(IN p_identifier VARCHAR(100))
BEGIN
    SELECT id, name, surname, username, email, status, created_at
    FROM user 
    WHERE (username = p_identifier OR email = p_identifier) 
    AND status = 'active';
END //

-- Update User Stored Procedure
DROP PROCEDURE IF EXISTS UpdateUser //
CREATE PROCEDURE UpdateUser(
    IN p_user_id INT,
    IN p_name VARCHAR(30),
    IN p_surname VARCHAR(30),
    IN p_email VARCHAR(100)
)
BEGIN
    UPDATE user 
    SET name = p_name,
        surname = p_surname,
        email = p_email
    WHERE id = p_user_id;
    
    SELECT ROW_COUNT() as updated;
END //

-- Delete User (Soft Delete) Stored Procedure
DROP PROCEDURE IF EXISTS DeleteUser //
CREATE PROCEDURE DeleteUser(IN p_user_id INT)
BEGIN
    UPDATE user 
    SET status = 'inactive'
    WHERE id = p_user_id;
    
    SELECT ROW_COUNT() as deleted;
END //

DELIMITER ;