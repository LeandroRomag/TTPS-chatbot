# Guia de Diagnostico - Problema de Encoding PostgreSQL

## Instrucciones

1. Tu compañero debe ejecutar: `python diagnose_encoding.py`
2. Copiar la salida completa
3. Comparar con los resultados de tu maquina (abajo)

---

## TU MAQUINA (FUNCIONA)

```
INFORMACION DEL SISTEMA
- Sistema Operativo: Windows 11
- Version OS: 10.0.26200
- Arquitectura: AMD64

INFORMACION DE PYTHON
- Version Python: 3.12.3
- Default Encoding: utf-8
- Filesystem Encoding: utf-8
- Stdout Encoding: cp1252
- Locale preferido: cp1252
- Locale actual: ('Spanish_Argentina', '1252')

VERSIONES DE PAQUETES
- psycopg2: 2.9.11
- SQLAlchemy: 2.0.44
- Flask: 3.1.2
- flask-sqlalchemy-lite: 0.2.1
- python-dotenv: 1.1.1

POSTGRESQL
- PostgreSQL Version: 17.7
- Server Encoding: UTF8
- Client Encoding: UTF8

TESTS DE CONEXION
- psycopg2 directo: OK
- SQLAlchemy sin client_encoding: OK
- SQLAlchemy con client_encoding: OK
```

---

## QUE COMPARAR

| Caracteristica | Tu maquina | Compañero |
|----------------|------------|-----------|
| Python version | 3.12.3 | ? |
| psycopg2 | 2.9.11 | ? |
| SQLAlchemy | 2.0.44 | ? |
| PostgreSQL | 17.7 | ? |
| Server Encoding | UTF8 | ? |
| Client Encoding | UTF8 | ? |
| Locale | cp1252 | ? |

---

## POSIBLES CAUSAS DEL ERROR

### 1. Version de Python diferente
Tu compañero usa Python 3.14 (segun errores anteriores).
**Solucion**: Usar Python 3.12 o 3.13.

### 2. PostgreSQL con encoding diferente
Si Server Encoding no es UTF8, hay problema.
**Verificar en PostgreSQL**:
```sql
SHOW server_encoding;
SHOW client_encoding;
```

### 3. Variable PGCLIENTENCODING definida
Si esta variable existe con valor incorrecto, causa problemas.
**Verificar**: `echo %PGCLIENTENCODING%`

### 4. Archivo .env con encoding incorrecto
El archivo .env podria estar guardado con encoding Latin-1.
**Solucion**: Abrir con Notepad, guardar como UTF-8.

### 5. Contrasena de PostgreSQL con caracteres especiales
Si la contrasena tiene acentos (ó, ñ, á), puede fallar.
**Solucion**: Cambiar contrasena a solo ASCII.

---

## SOLUCION ALTERNATIVA

Si nada funciona, agregar esta variable de entorno ANTES de ejecutar:

```powershell
$env:PGCLIENTENCODING = "UTF8"
python -m flask --app app reset-db
```

O permanentemente en Windows:
1. Buscar "Variables de entorno" en Windows
2. Agregar variable de usuario: PGCLIENTENCODING = UTF8
