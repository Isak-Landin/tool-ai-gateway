from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["UI_HOST"], port=app.config["UI_PORT"], debug=app.config["DEBUG"])
