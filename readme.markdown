This is an asset reference browser for the game of Riven. The purpose
of this application is to easily browse the images and movies from the
outstanding game of [Riven](http://cyan.com/games/riven/).

**Note**: This repository does not, and never will, contain actual Riven
assets. To run this browser one must first buy the DVD or CD, and
extract the game assets.

# Prerequisites

For hosting the reference browser:

    pip install flask
    pip install flask-sqlalchemy
    pip install flask-login
    pip install flask-wtf
    pip3 install Pillow
    pip3 install graphviz

**Note**: The program to make the database (makedb.py) is written in Python3, but the
web application is written in Python2 - you will need to install the first two Python
packages into both Pythons (i.e. pip and pip3).

For creating the database:

1. Install sqlite3.
1. Install ffmpeg.
1. Install ImageMagick.
1. Install graphviz.

# Creating the database.

1. Put the extracted game data in the protected/DVD folder.
2. Run `make`. If you don't have make installed then `./makedb.py`
   or `python3 makedb.py`.

This takes a while (> 10 minutes on most systems), mostly because
the movie transcoding process is CPU intensive. When finished the
database ("riven.sqlite") will exist as well as many new images
in the protected folder. To delete these newly created images just:

    make cleanall

# Running the Web Application.

First set the configuration options (see below).

For development purposes run it as so:

    python app.py

### Browser Configuration File

The browser will load a configuration file to read app settings.
This file is named "config.json".

    {
      "secret": "<random characters>",
      "db_url": "sqlite:////path/to/database/riven.sqlite",
      "test_pwd": "HardCodedPassword (temp for development)",
      "host": "0.0.0.0 - or IP",
      "debug": "true/false"
    }

**Note**: This application does not currently support multiple users, and
the one hard-coded user "admin" has a hard-coded test password specified above.
