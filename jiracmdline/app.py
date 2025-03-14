import datetime
import flask
import flask_login
import libweb
import os
import secrets
import user
import logging

import pprint

logfmt = '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s'
loglvl = logging.INFO
# loglvl = logging.DEBUG
logging.basicConfig( level=loglvl, format=logfmt )
logging.getLogger( 'libjira' ).setLevel( loglvl )
logging.getLogger( 'jira.JIRA' ).setLevel( loglvl )

app = flask.Flask( __name__ )
app.secret_key = secrets.token_hex()
if loglvl == logging.DEBUG:
    app.debug = True
# Tell flask_login to put "next" in the session, instead of, in the args to GET
app.config['USE_SESSION_FOR_NEXT'] = True
login_manager = flask_login.LoginManager( app=app )
login_manager.login_view = "login"


# reload the user object from the user ID stored in the session
# https://flask-login.readthedocs.io/en/latest/
@login_manager.user_loader
def load_user( user_id ):
    return user.User( user_id )


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
        try:
            u = user.User( user_id=sanitized_parts['token'] )
        except:
            flask.abort( 401 )
        print( f"login:POST login to jira succeeded'" )
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
        return flask.render_template( 'login.html' )


@app.route( '/logout' )
@flask_login.login_required
def logout():
    # user.User( flask.session['_user_id'] ).logout() #delete jira connection
    flask_login.logout_user() #delete cookie
    return flask.redirect( flask.url_for('index') )


@app.route( '/sprint_relatives' )
@flask_login.login_required
def do_sprint_relatives():
    import sprint_relatives
    session_update()
    valid_params=[ 'project' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = sprint_relatives.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    else:
        data['errors'] = [ "missing 'Project'" ]
    return flask.render_template(
        'sprint_relatives.html',
        **data,
    )


@app.route( '/lost_children' )
@flask_login.login_required
def do_lost_children():
    import lost_children
    session_update()
    valid_params=[ 'project' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = lost_children.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    else:
        data['errors'] = [ "missing 'Project'" ]
    return flask.render_template(
        'lost_children.html',
        **data,
    )


@app.route( '/service_list' )
@flask_login.login_required
def do_service_list():
    import service_list
    session_update()
    valid_params=[ 'project' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = service_list.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    else:
        data['errors'] = [ "missing 'Project'" ]
    return flask.render_template(
        'service_list.html',
        **data,
    )


@app.route( '/service_overview' )
@flask_login.login_required
def do_service_overview():
    import service_overview
    session_update()
    valid_params=[ 'project', 'service_name' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = service_overview.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    else:
        data['errors'] = [ f"missing one or more of {','.join(valid_params)}" ]
    return flask.render_template(
        'service_overview.html',
        **data,
    )


@app.route( '/tasks_from_description' )
@flask_login.login_required
def do_tasks_from_description():
    import tasks_from_description
    session_update()
    valid_params=[ 'ticket_ids' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = tasks_from_description.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    else:
        data['errors'] = [ 'missing "Ticket IDs"' ]
    return flask.render_template(
        'tasks_from_description.html',
        **data,
    )


@app.route( '/add_children', methods=['POST', 'GET'] )
@flask_login.login_required
def do_add_children():
    import add_children
    session_update()
    valid_params=[ 'parent', 'new_child_text' ]
    params = {}
    data = {}
    if flask.request.method == 'POST':
        try:
            params = { k:flask.request.form[k] for k in valid_params }
        except KeyError:
            params = {}
        if params:
            params['current_user'] = flask_login.current_user
            try:
                data = add_children.run( **params )
            except UserWarning as e:
                data['errors'] = [ str( e ) ]
        else:
            names = [ s.replace('_', ' ').title() for s in valid_params ]
            data['errors'] = [ f"missing one or more of {','.join(names)}" ]
    return flask.render_template(
        'add_children.html',
        **data,
    )


@app.route( '/summary' )
@flask_login.login_required
def do_summary():
    import summary
    session_update()
    valid_params=[ 'ticket_ids' ]
    params = {}
    data = {}
    try:
        params = { k:flask.request.args[k] for k in valid_params }
    except KeyError:
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = summary.run( **params )
        except UserWarning as e:
            data['errors'] = [ str( e ) ]
    return flask.render_template(
        'summary.html',
        **data,
    )


@app.route( '/task_reporting' )
@flask_login.login_required
def do_task_tracking():
    import task_report
    session_update()
    valid_params=[ 'group', 'timeframe', 'start', 'end' ]
    params = {}
    data = {}
    try:
        for k in valid_params:
            if k in flask.request.args:
                params[k] = flask.request.args[k]
        # params = { k:flask.request.args[k] for k in valid_params }
        # pprint.pprint( params )
    except KeyError as e:
        raise e
        params = {}
    if params:
        params['current_user'] = flask_login.current_user
        try:
            data = task_report.run( **params )
        except UserWarning as e:
            data[ 'errors' ] = e.args
    return flask.render_template(
        'task_reporting.html',
        **data,
    )


@app.route( '/mywork' )
@flask_login.login_required
def do_mywork():
    import mywork
    session_update()
    valid_params = []
    params = {}
    data = {}
    params['current_user'] = flask_login.current_user
    try:
        data = mywork.run( **params )
    except UserWarning as e:
        data[ 'errors' ] = e.args
    return flask.render_template(
        'mywork.html',
        **data,
    )


if __name__ == '__main__':
    app.run()
