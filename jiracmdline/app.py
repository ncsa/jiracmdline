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


@app.route( '/sprint_relatives' )
def do_sprint_relatives():
    import sprint_relatives
    data = sprint_relatives.run()
    return flask.render_template(
        "sprint_relatives.html",
        headers=data['headers'],
        data=data['data'],
        info=data['info'],
    )

if __name__ == '__main__':
    app.run()
