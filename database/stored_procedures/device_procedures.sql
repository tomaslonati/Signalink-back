DELIMITER //

-- 🔹 Crear dispositivo
DROP PROCEDURE IF EXISTS CreateDevice //
CREATE PROCEDURE CreateDevice(
    IN p_user_id INT,
    IN p_name VARCHAR(100),
    IN p_mac_address VARCHAR(17),
    IN p_manufacturer VARCHAR(100),
    IN p_model VARCHAR(100),
    IN p_firmware_version VARCHAR(50),
    IN p_ble_enabled BOOLEAN
)
BEGIN
    INSERT INTO device (user_id, name, mac_address, manufacturer, model, firmware_version, ble_enabled)
    VALUES (p_user_id, p_name, p_mac_address, p_manufacturer, p_model, p_firmware_version, p_ble_enabled);
    
    SELECT LAST_INSERT_ID() AS device_id;
END //

-- 🔹 Obtener dispositivo por ID
DROP PROCEDURE IF EXISTS GetDeviceById //
CREATE PROCEDURE GetDeviceById(IN p_device_id INT)
BEGIN
    SELECT d.id, d.user_id, d.name, d.mac_address, d.manufacturer, d.model,
           d.firmware_version, d.ble_enabled, d.last_seen, d.created_at,
           u.username, u.name AS user_name, u.surname AS user_surname
    FROM device d
    JOIN user u ON d.user_id = u.id
    WHERE d.id = p_device_id;
END //

-- 🔹 Obtener dispositivos por usuario
DROP PROCEDURE IF EXISTS GetDevicesByUser //
CREATE PROCEDURE GetDevicesByUser(IN p_user_id INT)
BEGIN
    SELECT id, user_id, name, mac_address, manufacturer, model, firmware_version,
           ble_enabled, last_seen, created_at
    FROM device
    WHERE user_id = p_user_id
    ORDER BY created_at DESC;
END //

-- 🔹 Obtener dispositivo por dirección MAC
DROP PROCEDURE IF EXISTS GetDeviceByMac //
CREATE PROCEDURE GetDeviceByMac(IN p_mac_address VARCHAR(17))
BEGIN
    SELECT d.id, d.user_id, d.name, d.mac_address, d.manufacturer, d.model,
           d.firmware_version, d.ble_enabled, d.last_seen, d.created_at,
           u.username, u.name AS user_name, u.surname AS user_surname
    FROM device d
    JOIN user u ON d.user_id = u.id
    WHERE d.mac_address = p_mac_address;
END //

-- 🔹 Actualizar dispositivo
DROP PROCEDURE IF EXISTS UpdateDevice //
CREATE PROCEDURE UpdateDevice(
    IN p_device_id INT,
    IN p_user_id INT,
    IN p_name VARCHAR(100),
    IN p_mac_address VARCHAR(17),
    IN p_manufacturer VARCHAR(100),
    IN p_model VARCHAR(100),
    IN p_firmware_version VARCHAR(50),
    IN p_ble_enabled BOOLEAN,
    IN p_last_seen DATETIME
)
BEGIN
    DECLARE v_is_owner BOOLEAN;
    
    SELECT EXISTS(
        SELECT 1 FROM device 
        WHERE id = p_device_id AND user_id = p_user_id
    ) INTO v_is_owner;
    
    IF NOT v_is_owner THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Device not found or you are not the owner';
    END IF;
    
    UPDATE device
    SET name = COALESCE(p_name, name),
        mac_address = COALESCE(p_mac_address, mac_address),
        manufacturer = COALESCE(p_manufacturer, manufacturer),
        model = COALESCE(p_model, model),
        firmware_version = COALESCE(p_firmware_version, firmware_version),
        ble_enabled = COALESCE(p_ble_enabled, ble_enabled),
        last_seen = COALESCE(p_last_seen, last_seen)
    WHERE id = p_device_id;
    
    SELECT TRUE AS success;
END //

-- 🔹 Eliminar dispositivo
DROP PROCEDURE IF EXISTS DeleteDevice //
CREATE PROCEDURE DeleteDevice(
    IN p_device_id INT,
    IN p_user_id INT
)
BEGIN
    DECLARE v_is_owner BOOLEAN;
    
    SELECT EXISTS(
        SELECT 1 FROM device 
        WHERE id = p_device_id AND user_id = p_user_id
    ) INTO v_is_owner;
    
    IF NOT v_is_owner THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Device not found or you are not the owner';
    END IF;
    
    DELETE FROM device WHERE id = p_device_id;
    
    SELECT TRUE AS success;
END //

-- 🔹 Obtener todos los dispositivos
DROP PROCEDURE IF EXISTS GetAllDevices //
CREATE PROCEDURE GetAllDevices()
BEGIN
    SELECT d.id, d.user_id, d.name, d.mac_address, d.manufacturer, d.model,
           d.firmware_version, d.ble_enabled, d.last_seen, d.created_at,
           u.username, u.name AS user_name, u.surname AS user_surname
    FROM device d
    JOIN user u ON d.user_id = u.id
    ORDER BY d.created_at DESC;
END //

-- 🔹 Verificar si una MAC es única
DROP PROCEDURE IF EXISTS CheckMacUnique //
CREATE PROCEDURE CheckMacUnique(
    IN p_mac_address VARCHAR(17),
    IN p_exclude_device_id INT
)
BEGIN
    IF p_exclude_device_id IS NOT NULL THEN
        SELECT NOT EXISTS(
            SELECT 1 FROM device 
            WHERE mac_address = p_mac_address 
            AND id != p_exclude_device_id
        ) AS is_unique;
    ELSE
        SELECT NOT EXISTS(
            SELECT 1 FROM device 
            WHERE mac_address = p_mac_address
        ) AS is_unique;
    END IF;
END //

DELIMITER ;


-- 🔹 Obtener dispositivos por fabricante
DROP PROCEDURE IF EXISTS GetDevicesByManufacturer //
CREATE PROCEDURE GetDevicesByManufacturer(IN p_manufacturer VARCHAR(100))
BEGIN
    SELECT d.id, d.user_id, d.name, d.mac_address, d.manufacturer, d.model,
           d.firmware_version, d.ble_enabled, d.last_seen, d.created_at,
           u.username, u.name AS user_name, u.surname AS user_surname
    FROM device d
    JOIN user u ON d.user_id = u.id
    WHERE d.manufacturer = p_manufacturer
    ORDER BY d.created_at DESC;
END //

-- 🔹 Obtener dispositivos por modelo
DROP PROCEDURE IF EXISTS GetDevicesByModel //
CREATE PROCEDURE GetDevicesByModel(IN p_model VARCHAR(100))
BEGIN
    SELECT d.id, d.user_id, d.name, d.mac_address, d.manufacturer, d.model,
           d.firmware_version, d.ble_enabled, d.last_seen, d.created_at,
           u.username, u.name AS user_name, u.surname AS user_surname
    FROM device d
    JOIN user u ON d.user_id = u.id
    WHERE d.model = p_model
    ORDER BY d.created_at DESC;
END //

DELIMITER ;