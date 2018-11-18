This is an asset reference browser for the game of Riven. The purpose
of this application is to easily browse the images and movies from the
outstanding game of [Riven](http://cyan.com/games/riven/).

**Note**: This repository does not, and never will, contain actual Riven
assets. To run this browser one must first buy the DVD or CD, and
extract the game assets.

# Prerequisites

## Web app prerequisites

For hosting the reference browser, you will need both Python 2 and Python 3 dependencies. This is because the program to make the database (makedb.py) is written in Python3, but the web application is written in Python2.

    # python 2 dependencies:
    pip install flask
    pip install flask-sqlalchemy
    pip install flask-login
    pip install flask-wtf
    
    # python 3 dependencies:
    pip3 install Pillow
    pip3 install graphviz

## Database prerequisites

For creating the database:

1. Install sqlite3.
1. Install ffmpeg.
1. Install ImageMagick.
1. Install graphviz.

# Creating the database.

1. Put the extracted game data in the browser/protected/DVD folder.
2. Run `make`. If you don't have make installed then `./makedb.py`
   or `python3 makedb.py`.

This takes a while (> 10 minutes on most systems), mostly because
the movie transcoding process is CPU intensive. When finished the
database ("riven.sqlite") will exist as well as many new images
in the protected folder. To delete these newly created images just:

    make cleanall

# Running the Web Application.

#### Step 1: App configuration

The reference browser first reads it's configuration data from `config.py`. This
configuration is then overridden by `instance/config.py`. Since `instance/config.py`
is not under version control, it should be the one that you update.

The following keys must be specified:

1. `SQLALCHEMY_DATABASE_URI`
2. `SECRET_KEY`

For more information see [Flask Configuration](http://flask.pocoo.org/docs/0.12/config/).

One password is used for authentication, and it is read from `instance/password.txt`.

**Note**: This application does not currently support multiple users, and
the one hard-coded user "admin" has a hard-coded test password specified above.

#### Step 2: Running Flask for development

For development purposes, the app can be run as so:

    python app.py