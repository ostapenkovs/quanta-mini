import traceback
import os, io
from dotenv import load_dotenv
import pandas as pd
import wrds

from flask import (
    Flask,
    request,
    render_template,
    abort,
    redirect,
    url_for,
    send_file,
    send_from_directory
)

from util import get_data

N_DAYS = 20
UPLOAD_FOLDER = './data'
OUTPUT_NAME = 'output.csv'

load_dotenv()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

conn = None
def get_conn():
    global conn
    if conn is None:
        conn = wrds.Connection()
    return conn

@app.errorhandler(404)
def internal_server_error(e):
    return render_template('404.jinja'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.jinja'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    output = None

    try:
        if request.method == 'POST':
            ticker = request.form.get('ticker')
            ticker = ticker.upper()

            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            volume_breakout_thresh = request.form.get('volume_breakout_thresh')
            volume_breakout_thresh = float(volume_breakout_thresh) / 100

            change_thresh = request.form.get('change_thresh')
            change_thresh = float(change_thresh) / 100

            holding_period = request.form.get('holding_period')
            holding_period = int(holding_period)

            c = get_conn()
            df = get_data(conn=c, ticker=ticker, start_date=start_date, end_date=end_date)

            ### SIGNAL ###
            df['signal'] = (
                (df['volume'] > (1+volume_breakout_thresh) * df['volume'].rolling(window=N_DAYS).mean()) & \
                (df['return'] > change_thresh)
            ).astype(int)

            df = df.iloc[N_DAYS-1:]
            ### SIGNAL ###

            ### STRATEGY ###
            output = list()
            for idx in df[df['signal'] == 1].index:
                date = df.loc[idx, 'date']
                ret = (1 + df.loc[idx+1: idx+holding_period, 'return']).cumprod().iloc[-1] - 1
                output.append((date, ret))
            output = pd.DataFrame(output, columns=['date', 'return'])
            output.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], OUTPUT_NAME), index=False)
            output = output.to_html()
            ### STRATEGY ###
    
    except:
        traceback.print_exc()
        abort(500)
    
    return render_template('index.jinja', output=output)

@app.route('/download', methods=['GET'])
def download():
    try:
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], OUTPUT_NAME)):
            return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=OUTPUT_NAME)

        return redirect(url_for('index'))
    
    except:
        traceback.print_exc()
        abort(500)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
