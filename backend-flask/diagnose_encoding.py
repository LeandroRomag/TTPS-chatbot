#!/usr/bin/env python
"""
SCRIPT DE DIAGNOSTICO - TTPS Chatbot
=====================================
Ejecutar este script y compartir la salida para comparar configuraciones.

Uso: python diagnose_encoding.py
"""

import sys
import os
import locale
import platform

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def main():
    print_section("INFORMACION DEL SISTEMA")
    print(f"Sistema Operativo: {platform.system()} {platform.release()}")
    print(f"Version OS: {platform.version()}")
    print(f"Arquitectura: {platform.machine()}")
    print(f"Nombre del equipo: {platform.node()}")
    
    print_section("INFORMACION DE PYTHON")
    print(f"Version Python: {sys.version}")
    print(f"Ejecutable: {sys.executable}")
    print(f"Default Encoding: {sys.getdefaultencoding()}")
    print(f"Filesystem Encoding: {sys.getfilesystemencoding()}")
    print(f"Stdout Encoding: {sys.stdout.encoding}")
    print(f"Locale preferido: {locale.getpreferredencoding()}")
    print(f"Locale actual: {locale.getlocale()}")
    
    print_section("VARIABLES DE ENTORNO RELEVANTES")
    env_vars = ['LANG', 'LC_ALL', 'LC_CTYPE', 'PYTHONIOENCODING', 
                'PGCLIENTENCODING', 'PGHOST', 'PGPORT', 'PGDATABASE', 
                'PGUSER', 'PGPASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 
                'DB_USER', 'DB_PASSWORD']
    for var in env_vars:
        value = os.getenv(var)
        if var in ['PGPASSWORD', 'DB_PASSWORD'] and value:
            value = '***OCULTO***'
        print(f"{var}: {value or '(no definida)'}")
    
    print_section("VERSIONES DE PAQUETES")
    packages_to_check = [
        ('psycopg2', 'psycopg2'),
        ('SQLAlchemy', 'sqlalchemy'),
    ]
    for name, import_name in packages_to_check:
        try:
            mod = __import__(import_name)
            version = getattr(mod, '__version__', 'instalado')
            print(f"{name}: {version}")
        except ImportError:
            print(f"{name}: NO INSTALADO")
    
    # Flask y otros con importlib
    try:
        from importlib.metadata import version as get_version
        print(f"Flask: {get_version('flask')}")
        print(f"flask-sqlalchemy-lite: {get_version('flask-sqlalchemy-lite')}")
        print(f"python-dotenv: {get_version('python-dotenv')}")
    except Exception as e:
        print(f"Error obteniendo versiones: {e}")
    
    print_section("INFORMACION DE POSTGRESQL")
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'chatbot_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        
        print(f"Conectando a: {host}:{port}/{dbname} como {user}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        print("[OK] Conexion directa con psycopg2: EXITOSA")
        
        # Verificar encoding del servidor
        cur = conn.cursor()
        cur.execute("SHOW server_encoding;")
        server_enc = cur.fetchone()[0]
        cur.execute("SHOW client_encoding;")
        client_enc = cur.fetchone()[0]
        cur.execute("SELECT version();")
        pg_version = cur.fetchone()[0]
        
        print(f"PostgreSQL Version: {pg_version}")
        print(f"Server Encoding: {server_enc}")
        print(f"Client Encoding: {client_enc}")
        
        conn.close()
    except Exception as e:
        print(f"[ERROR] Conexion psycopg2: {type(e).__name__}: {e}")
    
    print_section("TEST SQLALCHEMY SIN client_encoding")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL
        from dotenv import load_dotenv
        load_dotenv()
        
        url = URL.create(
            drivername="postgresql",
            username=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'chatbot_db')
        )
        
        engine = create_engine(url)
        with engine.connect() as conn:
            print("[OK] Conexion SQLAlchemy SIN client_encoding: EXITOSA")
    except Exception as e:
        print(f"[ERROR] SQLAlchemy SIN client_encoding: {type(e).__name__}: {e}")
    
    print_section("TEST SQLALCHEMY CON client_encoding=utf8")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL
        from dotenv import load_dotenv
        load_dotenv()
        
        url = URL.create(
            drivername="postgresql",
            username=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'chatbot_db')
        )
        
        engine = create_engine(url, client_encoding='utf8')
        with engine.connect() as conn:
            print("[OK] Conexion SQLAlchemy CON client_encoding: EXITOSA")
    except Exception as e:
        print(f"[ERROR] SQLAlchemy CON client_encoding: {type(e).__name__}: {e}")
    
    print_section("TEST FLASK-SQLALCHEMY-LITE")
    try:
        from app import app
        with app.app_context():
            from src.core.database import db
            engine = db.get_engine()
            print(f"Engine URL: {engine.url}")
            with engine.connect() as conn:
                print("[OK] Conexion Flask-SQLAlchemy-Lite: EXITOSA")
    except Exception as e:
        print(f"[ERROR] Flask-SQLAlchemy-Lite: {type(e).__name__}: {e}")
    
    print("\n" + "="*60)
    print(" FIN DEL DIAGNOSTICO")
    print("="*60)
    print("\nCopia toda esta salida y compartela para comparar.")

if __name__ == "__main__":
    main()
