from project import create_app

if __name__ == '__main__':
    # create_app() sets up configuration, database access, login, and routes.
    app = create_app()
    # The assessment README uses port 8888 for local demonstration.
    app.run(debug=False, port=8888)
