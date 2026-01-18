from src import create_app

# Crea la aplicación usando tu fábrica
app = create_app(env='development')

if __name__ == "__main__":
    # Esto permite correrlo con "python app.py"
    app.run(host="0.0.0.0", port=5000, debug=True)