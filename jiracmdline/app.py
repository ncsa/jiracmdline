import flask
import pprint

app = flask.Flask( __name__ )

@app.route( '/' )
def base():
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
