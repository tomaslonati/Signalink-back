import re

def validate_email(email):
    """
    Valida que el email tenga un formato correcto
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_password(password):
    """
    Valida que la contraseña cumpla con los requisitos mínimos
    """
    if not password:
        return False
    
    # Mínimo 6 caracteres
    if len(password) < 6:
        return False
    
    return True

def validate_username(username):
    """
    Valida que el username sea válido
    """
    if not username:
        return False
    
    # Entre 3 y 50 caracteres, solo letras, números y guión bajo
    if len(username) < 3 or len(username) > 50:
        return False
    
    username_pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(username_pattern, username) is not None

def validate_name(name):
    """
    Valida que el nombre sea válido
    """
    if not name:
        return False
    
    # Entre 2 y 30 caracteres, solo letras y espacios
    if len(name) < 2 or len(name) > 30:
        return False
    
    name_pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
    return re.match(name_pattern, name) is not None

# Funciones legacy para compatibilidad
def is_valid_email(email):
    return validate_email(email)

def is_strong_password(password):
    return (len(password) >= 8 and 
            any(char.isdigit() for char in password) and 
            any(char.isupper() for char in password) and 
            any(char.islower() for char in password) and 
            any(char in '!@#$%^&*()_+' for char in password))

def validate_user_input(email, password):
    if not is_valid_email(email):
        return False, "Invalid email format."
    if not is_strong_password(password):
        return False, "Password must be at least 8 characters long, contain uppercase and lowercase letters, a number, and a special character."
    return True, "Valid input."