DELIMITER //

-- Create Group Stored Procedure
DROP PROCEDURE IF EXISTS CreateGroup //
CREATE PROCEDURE CreateGroup(
    IN p_owner_id INT,
    IN p_name VARCHAR(100)
)
BEGIN
    INSERT INTO user_group (owner_id, name)
    VALUES (p_owner_id, p_name);
    
    SELECT LAST_INSERT_ID() as group_id;
END //

-- Get Group By ID Stored Procedure
DROP PROCEDURE IF EXISTS GetGroupById //
CREATE PROCEDURE GetGroupById(IN p_group_id INT)
BEGIN
    SELECT g.id, g.owner_id, g.name, u.username as owner_username
    FROM user_group g
    JOIN user u ON g.owner_id = u.id
    WHERE g.id = p_group_id;
END //

-- Get Groups By Owner Stored Procedure
DROP PROCEDURE IF EXISTS GetGroupsByOwner //
CREATE PROCEDURE GetGroupsByOwner(IN p_owner_id INT)
BEGIN
    SELECT g.id, g.owner_id, g.name, u.username as owner_username
    FROM user_group g
    JOIN user u ON g.owner_id = u.id
    WHERE g.owner_id = p_owner_id
    ORDER BY g.name;
END //

-- Delete Group Stored Procedure
DROP PROCEDURE IF EXISTS DeleteGroup //
CREATE PROCEDURE DeleteGroup(
    IN p_group_id INT,
    IN p_owner_id INT
)
BEGIN
    DECLARE v_is_owner BOOLEAN;
    
    -- Verify ownership
    SELECT EXISTS(
        SELECT 1 FROM user_group 
        WHERE id = p_group_id AND owner_id = p_owner_id
    ) INTO v_is_owner;
    
    IF NOT v_is_owner THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Group not found or you are not the owner';
    END IF;
    
    -- Delete members first
    DELETE FROM user_group_member WHERE group_id = p_group_id;
    
    -- Delete group
    DELETE FROM user_group WHERE id = p_group_id;
    
    SELECT TRUE as success;
END //

-- Add Group Member Stored Procedure
DROP PROCEDURE IF EXISTS AddGroupMember //
CREATE PROCEDURE AddGroupMember(
    IN p_group_id INT,
    IN p_user_id INT
)
BEGIN
    INSERT INTO user_group_member (group_id, user_id)
    VALUES (p_group_id, p_user_id);
    
    SELECT TRUE as success;
END //

-- Remove Group Member Stored Procedure
DROP PROCEDURE IF EXISTS RemoveGroupMember //
CREATE PROCEDURE RemoveGroupMember(
    IN p_group_id INT,
    IN p_user_id INT
)
BEGIN
    DELETE FROM user_group_member 
    WHERE group_id = p_group_id 
    AND user_id = p_user_id;
    
    SELECT ROW_COUNT() as deleted;
END //

-- Get Group Members Stored Procedure
DROP PROCEDURE IF EXISTS GetGroupMembers //
CREATE PROCEDURE GetGroupMembers(IN p_group_id INT)
BEGIN
    SELECT u.id, u.username, u.name, u.surname, u.email
    FROM user_group_member gm
    JOIN user u ON gm.user_id = u.id
    WHERE gm.group_id = p_group_id 
    AND u.status = 'active'
    ORDER BY u.name, u.surname;
END //

-- Get User Groups Stored Procedure
DROP PROCEDURE IF EXISTS GetUserGroups //
CREATE PROCEDURE GetUserGroups(IN p_user_id INT)
BEGIN
    SELECT g.id, g.name, g.owner_id, u.username as owner_username
    FROM user_group_member gm
    JOIN user_group g ON gm.group_id = g.id
    JOIN user u ON g.owner_id = u.id
    WHERE gm.user_id = p_user_id
    ORDER BY g.name;
END //

-- Check Member Status Stored Procedure
DROP PROCEDURE IF EXISTS CheckMemberStatus //
CREATE PROCEDURE CheckMemberStatus(
    IN p_group_id INT,
    IN p_user_id INT
)
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM user_group_member 
        WHERE group_id = p_group_id 
        AND user_id = p_user_id
    ) as is_member;
END //

DELIMITER ;