from bookshare import create_app, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully.")
    app.run(host="0.0.0.0", port=5000)
