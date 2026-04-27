from config.database import DatabaseConfig
import mysql.connector

class calibrateService:
    def __init__(self):
        self.db_config = DatabaseConfig()

    def createCalibration(self, device_id, sign_label, sign_type, axis_x, axis_y, axis_z, flex_index, flex_ring, flex_pinky, flex_middle, repetitions, notes):
        """
        Crear una nueva calibración
        """
        try:
            connection = self.db_config.get_connection()
            cursor = connection.cursor()

            # Validar que no exista una calibración con el mismo sign_label para este dispositivo
            check_query = """
                SELECT id FROM glove_calibration 
                WHERE device_id = %s AND sign_label = %s
            """
            cursor.execute(check_query, (device_id, sign_label))
            existing_calibration = cursor.fetchone()

            if existing_calibration:
                return {
                    'error': f'A calibration with sign_label "{sign_label}" already exists for this device'
                }, 409

            insert_query = """
                INSERT INTO glove_calibration (device_id, sign_label, sign_type, axis_x, axis_y, axis_z, flex_index, flex_ring, flex_pinky, flex_middle, repetitions, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                device_id,
                sign_label,
                sign_type,
                axis_x,
                axis_y,
                axis_z,
                flex_index,
                flex_ring,
                flex_pinky,
                flex_middle,
                repetitions,
                notes
            ))
            connection.commit()
            calibration_id = cursor.lastrowid

            return {
                'success': True,
                'message': 'Calibración creada exitosamente',
                'device_id': device_id,
                'sign_label': sign_label,
                'calibration_id': calibration_id
            }, 201

        except mysql.connector.Error as e:
            if connection:
                connection.rollback()
            return {'error': f'Database error: {str(e)}'}, 500
        except Exception as e:
            if connection:
                connection.rollback()
            return {'error': str(e)}, 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                
    def getCalibrationByDeviceId(self, device_id):
        """
        Obtener todas las calibraciones de un dispositivo
        """
        try:
            connection = self.db_config.get_connection()
            cursor = connection.cursor(dictionary=True)

            select_query = """
                SELECT * FROM glove_calibration WHERE device_id = %s
            """
            cursor.execute(select_query, (device_id,))
            calibrations = cursor.fetchall()

            return calibrations

        except mysql.connector.Error as e:
            return {'error': f'Database error: {str(e)}'}, 500
        except Exception as e:
            return {'error': str(e)}, 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                
    def updateCalibration(self, device_id, sign_label, sign_type, axis_x, axis_y, axis_z, flex_index, flex_ring, flex_pinky, flex_middle, repetitions, notes):
        """
        Actualizar una calibración existente
        """
        connection = None
        cursor = None
        try:
            if not sign_label:
                return {'error': 'sign_label is required'}, 400
            
            connection = self.db_config.get_connection()
            cursor = connection.cursor()
            
            # Construir la consulta de actualización dinámicamente
            update_fields = []
            update_values = []
                
            updatable_fields = {
                'sign_type': sign_type,
                'axis_x': axis_x,
                'axis_y': axis_y,
                'axis_z': axis_z,
                'flex_index': flex_index,
                'flex_ring': flex_ring,
                'flex_pinky': flex_pinky,
                'flex_middle': flex_middle,
                'repetitions': repetitions,
                'notes': notes
            }

            for field, value in updatable_fields.items():
                if value is not None:
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)

            if not update_fields:
                return {'error': 'No fields to update'}, 400

            update_values.append(device_id)
            update_values.append(sign_label)

            query = f"""
            UPDATE glove_calibration
            SET {', '.join(update_fields)}
            WHERE device_id = %s AND sign_label = %s
            """

            cursor.execute(query, update_values)
            connection.commit()

            return {
                'success': True,
                'message': 'Calibration updated successfully',
                'device_id': str(device_id),
                'sign_label': sign_label
            }, 200

        except mysql.connector.Error as e:
            if connection:
                print("Error occurred:", e)
                connection.rollback()
            return {'error': f'Database error: {str(e)}'}, 500
        except Exception as e:
            if connection:
                print("Exception occurred:", e)
                connection.rollback()
            return {'error': str(e)}, 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def deleteCalibration(self, device_id, sign_label):
        """
        Eliminar calibraciones de un dispositivo por sign_label
        """
        connection = None
        cursor = None
        try:
            print("Deleting calibration with:", device_id, sign_label)
            if not sign_label:
                return {'error': 'sign_label is required'}, 400

            connection = self.db_config.get_connection()
            cursor = connection.cursor()


            # Eliminar calibraciones con ese sign_label
            query = """
            DELETE FROM glove_calibration
            WHERE device_id = %s AND sign_label = %s
            """

            cursor.execute(query, (device_id, sign_label))
            connection.commit()

            if cursor.rowcount == 0:
                return {'error': f'No calibrations found with sign_label {sign_label}'}, 404

            return {
                'success': True,
                'message': f'Deleted {cursor.rowcount} calibration(s) successfully',
                'device_id': str(device_id),
                'sign_label': sign_label
            }, 200

        except mysql.connector.Error as e:
            if connection:
                connection.rollback()
            return {'error': f'Database error: {str(e)}'}, 500
        except Exception as e:
            if connection:
                connection.rollback()
            return {'error': str(e)}, 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()