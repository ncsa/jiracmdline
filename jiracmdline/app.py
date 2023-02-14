import datetime
import flask
import flask_login
import libjira
import libweb
import os
import secrets
import user

app = flask.Flask( __name__ )
app.secret_key = secrets.token_hex()
# Tell flask_login to put "next" in the session instead of GET args
app.config['USE_SESSION_FOR_NEXT'] = True
login_manager = flask_login.LoginManager( app=app )
login_manager.login_view = "login"


# reload the user object from the user ID stored in the session
# https://flask-login.readthedocs.io/en/latest/
@login_manager.user_loader
def load_user( user_id ):
    u = user.User( user_id )
    if not u.is_authenticated():
        u = None
    return u


# def session_init( session ):
def session_init():
    if 'jira_project' not in flask.session:
        flask.session['jira_project'] = os.environ['JIRA_PROJECT']


def session_update():
    ''' Update the session with anything relevant.
        Just the things we care about.
    '''
    # initialize for first run
    session_init()
    # get appropriate params based on request type
    if flask.request.method == 'POST':
        params = dict( **flask.request.form )
    elif flask.request.method == 'GET':
        params = dict( **flask.request.args )
    # update any "valid" session keys that are present
    valid_keys = [ 'jira_project' ]
    for key in valid_keys:
        if key in params:
            session[ key ] = params[ key ]


@app.route( '/' )
def index():
    session_update()
    return flask.render_template(
        'index.html',
        timestamp=datetime.datetime.now(),
        message='Welcome',
    )


@app.route( '/login', methods=['POST', 'GET'] )
def login():
    print( f'start login, method={flask.request.method}' )
    if flask.request.method == 'POST':
        sanitized_parts = libweb.sanitize_dict( flask.request.form )
        uid = libjira.jira_login( **sanitized_parts )
        print( f"login:POST (uid from jira)='{uid}'" )
        if uid:
            u = user.User( uid )
            flask_login.login_user( u )
            flask.flash('Logged in successfully.')
            try:
                next = flask.session['next']
                print( f"login:POST next='{next}'" )
            except KeyError:
                next = flask.url_for('index')
                print( f"login:POST next=KeyError; using index instead" )
            return flask.redirect( next )
        else:
            flask.abort( 401 )
    else:
        return flask.render_template( 'login.html' )


@app.route( '/logout' )
@flask_login.login_required
def logout():
    user.User( flask.session['_user_id'] ).logout() #delete jira connection
    flask_login.logout_user() #delete cookie
    return flask.redirect( flask.url_for('index') )


@app.route( '/sprint_relatives', methods=['POST', 'GET'] )
@flask_login.login_required
def do_sprint_relatives():
    import sprint_relatives
    session_update()
    params = dict( jira_session_id=flask.session['_user_id'] )
    if flask.request.method == 'POST':
        params |= flask.request.form
    else:
        params |= flask.request.args
    data = sprint_relatives.run( **params )
    return flask.render_template(
        'sprint_relatives.html',
        **data,
    )


@app.route( '/lost_children', methods=['POST', 'GET'] )
@flask_login.login_required
def do_lost_children():
    import lost_children
    session_update()
    params = dict( jira_session_id=flask.session['_user_id'] )
    if flask.request.method == 'POST':
        params |= flask.request.form
    else:
        params |= flask.request.args
    data = lost_children.run( **params )
    return flask.render_template(
        'lost_children.html',
        **data,
    )


@app.route( '/tasks_from_description', methods=['POST', 'GET'] )
@flask_login.login_required
def do_tasks_from_description():
    import tasks_from_description
    session_update()
    params = dict( jira_session_id=flask.session['_user_id'] )
    data = {}
    if flask.request.method == 'POST':
        params |= flask.request.form
        data = tasks_from_description.run( **params )
    return flask.render_template(
        'tasks_from_description.html',
        **data,
    )


@app.route( '/add_children', methods=['POST', 'GET'] )
@flask_login.login_required
def do_add_children():
    import add_children
    session_update()
    params = dict( jira_session_id=flask.session['_user_id'] )
    data = {}
    if flask.request.method == 'POST':
        params |= flask.request.form
        try:
            data = add_children.run( **params )
        except UserWarning as e:
            data['errors'] = str( e )
    return flask.render_template(
        'add_children.html',
        **data,
    )


@app.route( '/summary', methods=['POST', 'GET'] )
@flask_login.login_required
def do_summary():
    import summary
    session_update()
    params = dict( jira_session_id=flask.session['_user_id'] )
    data = {}
    if flask.request.method == 'POST':
        params |= flask.request.form
        try:
            data = summary.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    return flask.render_template(
        'summary.html',
        **data,
    )


if __name__ == '__main__':
    app.run()
