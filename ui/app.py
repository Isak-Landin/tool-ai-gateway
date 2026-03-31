from webapp import create_app

"""
The origin of all bugs is ui and js interactions.
We are currently running in to some 405s which are cause by poor js requests.

Currently js is expection to request directly from api. This behavior is straight suicide.
We absolutely do not have a need to request directly from api when the ui backend is fully capable
of communication with the api in place of the js attempting to directly fetch information from it.
"""

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config["UI_HOST"],
        port=app.config["UI_PORT"],
        debug=False,
        use_reloader=app.config["DEBUG"],
    )
