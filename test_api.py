#!/usr/bin/env python3
"""
Script para probar la API de Signalink
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def test_swagger():
    """Probar que Swagger está disponible"""
    print("Testing Swagger Documentation...")
    response = requests.get(f"{BASE_URL}/docs/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Swagger está disponible en /docs/")
    print("-" * 50)

def test_health():
    """Probar endpoint de health"""
    print("Testing Health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_auth_health():
    """Probar endpoint de health del módulo auth"""
    print("Testing Auth Health endpoint...")
    response = requests.get(f"{BASE_URL}/api/auth/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_login_invalid():
    """Probar login con credenciales inválidas"""
    print("Testing Login with invalid credentials...")
    data = {
        "username": "test_user",
        "password": "wrong_password"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_register():
    """Probar registro de usuario"""
    print("Testing User Registration...")
    data = {
        "name": "Test",
        "surname": "User",
        "username": "testuser123",
        "email": "test@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_home():
    """Probar endpoint principal"""
    print("Testing Home endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

if __name__ == "__main__":
    print("=== TESTING SIGNALINK API ===")
    print()
    
    try:
        test_home()
        test_swagger()
        test_health()
        test_auth_health()
        test_login_invalid()
        test_register()
        
        print("\n🎉 ¡Todos los tests completados!")
        print(f"📚 Documentación Swagger disponible en: {BASE_URL}/docs/")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar a la API. ¿Está ejecutándose en localhost:8080?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")