import app as a

# This is used when running under Apache. It looks like WSGI needs
# a module object named "app" which is the Flask application, but
# not yet running.
app = a.create_app()
