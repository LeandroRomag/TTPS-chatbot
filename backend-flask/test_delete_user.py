#!/usr/bin/env python3
"""
Script para probar la eliminación de usuarios vía endpoint DELETE.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Primero, hacer login para obtener session cookie
print("1. Haciendo login...")
session = requests.Session()
login_data = {
    "email": "admin@gmail.com",
    "password": "admin123"
}
login_response = session.post(f"{BASE_URL}/auth/login", data=login_data)
print(f"   Status: {login_response.status_code}")

# Obtener lista de usuarios
print("\n2. Obteniendo lista de usuarios...")
users_response = session.get(f"{BASE_URL}/user/")
print(f"   Status: {users_response.status_code}")

# Probar eliminar al superadmin (debería fallar)
print("\n3. Intentando eliminar al superadmin (debería fallar)...")
delete_response = session.delete(
    f"{BASE_URL}/user/1",
    headers={"Content-Type": "application/json"}
)
print(f"   Status: {delete_response.status_code}")
print(f"   Response: {json.dumps(delete_response.json(), indent=2)}")

# Crear un nuevo usuario para eliminarlo
print("\n4. Creando un nuevo usuario para eliminar...")
create_data = {
    "nombre": "Test",
    "apellido": "Delete",
    "email": "test.delete@example.com",
    "password": "TestPassword123",
    "confirm_password": "TestPassword123"
}
create_response = session.post(f"{BASE_URL}/user/create", data=create_data)
print(f"   Status: {create_response.status_code}")

# Obtener el ID del nuevo usuario
print("\n5. Obteniendo lista de usuarios (para encontrar el nuevo)...")
users_response = session.get(f"{BASE_URL}/user/")
print(f"   Status: {users_response.status_code}")

# Buscar el usuario creado
from bs4 import BeautifulSoup
soup = BeautifulSoup(users_response.text, 'html.parser')
# Buscar en los data-user-id de los botones delete
delete_btns = soup.find_all(class_='delete-user-btn')
new_user_id = None
for btn in delete_btns:
    if btn.get('data-user-name') == 'Test Delete':
        new_user_id = btn.get('data-user-id')
        break

if new_user_id:
    print(f"   ID del nuevo usuario encontrado: {new_user_id}")
    
    # Intentar eliminar al nuevo usuario
    print(f"\n6. Eliminando al usuario {new_user_id}...")
    delete_response = session.delete(
        f"{BASE_URL}/user/{new_user_id}",
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {delete_response.status_code}")
    print(f"   Response: {json.dumps(delete_response.json(), indent=2)}")
else:
    print("   No se encontró el usuario creado")

print("\nPrueba completada.")
