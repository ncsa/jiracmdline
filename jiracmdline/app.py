import flask
import datetime

app = flask.Flask( __name__ )


@app.route( '/' )
def do_index():
    return flask.render_template(
        'index.html',
        timestamp=datetime.datetime.now(),
        message='Welcome',
    )


@app.route( '/sprint-relatives' )
def do_sprint_relatives():
    import sprint_relatives
    data = sprint_relatives.run()
    return flask.render_template(
        'sprint_relatives.html',
        headers=data['headers'],
        data=data['data'],
        info=data['info'],
    )

@app.route( '/convert-subtasks', methods=['POST','GET'] )
def do_convert_subtasks():
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
