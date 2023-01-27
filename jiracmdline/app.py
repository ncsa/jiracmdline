import flask
import datetime
import secrets
import os

app = flask.Flask( __name__ )
app.secret_key = secrets.token_hex()


def session_init( session ):
    if 'jira_project' not in session:
        session['jira_project'] = os.environ['JIRA_PROJECT']


@app.route( '/' )
def do_index():
    session_init( flask.session )
    return flask.render_template(
        'index.html',
        timestamp=datetime.datetime.now(),
        message='Welcome',
    )


@app.route( '/sprint-relatives', methods=['POST','GET'] )
def do_sprint_relatives():
    import sprint_relatives
    session_init( flask.session )
    if flask.request.method == 'POST':
        data = sprint_relatives.run( **flask.request.form )
    elif flask.request.method == 'GET':
        data = sprint_relatives.run( **flask.request.args )
    return flask.render_template(
        'sprint_relatives.html',
        **data,
    )


@app.route( '/lost-children', methods=['POST', 'GET'] )
def do_lost_children():
    import lost_children
    session_init( flask.session )
    if flask.request.method == 'POST':
        data = lost_children.run( **flask.request.form )
    elif flask.request.method == 'GET':
        data = lost_children.run( **flask.request.args )
    return flask.render_template(
        'lost_children.html',
        **data,
    )


@app.route( '/tasks_from_description', methods=['POST', 'GET'] )
def do_tasks_from_description():
    import tasks_from_description
    session_init( flask.session )
    data = {}
    if flask.request.method == 'POST':
        data = tasks_from_description.run( **flask.request.form )
    return flask.render_template(
        'tasks_from_description.html',
        **data,
    )


@app.route( '/convert-subtasks', methods=['POST','GET'] )
def do_convert_subtasks():
    session_init( flask.session )
    debug = None
    data = {}
    if flask.request.method == 'POST':
        import mk_children_from_subtasks
        data = mk_children_from_subtasks.run( **flask.request.form )
        # debug = ( 'This is the data from convert_subtasks()\n'
        #     f'{data}'
        # )
    return flask.render_template( 
        'convert_subtasks.html',
        debug=debug,
        **data,
    )


if __name__ == '__main__':
    app.run()
