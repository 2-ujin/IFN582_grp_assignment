
from flask import Flask 
from flask_mysqldb import MySQL

database = MySQL()

def create_app():
    app = Flask(__name__)
    
    # Debug mode is off so detailed error pages are never shown to users
    app.debug = False

    # Secret key 
    app.secret_key = 'MakeArtsFund-secret-key-A3-project'

    # Register the blueprint that holds all MakeArtsFund routes
    from .views import main
    app.register_blueprint(main)


# ---- @Queenie: This is the place for ur error handlers ------ :) 


    # below is the setup for the database
    # you will need to configure these attributes yourself
    app.config['MYSQL_HOST'] = 'localhost' # dont change
    app.config['MYSQL_USER'] = 'root' # dont change
   
## !IMPORTANT! Change the password before you run the code.  
    app.config['MYSQL_PASSWORD'] = '582Assignment2' # change it to ur local password
    
    
    app.config['MYSQL_DB'] = 'maf' # same schema to database.sql
    
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 

    
    database.init_app(app)
    
    return app
