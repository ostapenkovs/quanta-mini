import traceback

from flask import (
    Flask,
    request,
    render_template,
    abort,
    send_file,
    make_response
)

app = Flask(__name__)

@app.errorhandler(404)
def internal_server_error(e):
    return render_template('404.jinja'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.jinja'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        pass
    
    except:
        traceback.print_exc()
        abort(500)
    
    return render_template('index.jinja')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
