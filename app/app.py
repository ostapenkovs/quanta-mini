import traceback
import os, io
from dotenv import load_dotenv
import pandas as pd
import wrds

from flask import (
    Flask,
    request,
    session,
    render_template,
    abort,
    send_file,
    url_for,
    redirect
)

from util import get_data

N_DAYS = 20

app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')

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
    try:
        if request.method == 'POST':
            ticker = request.form.get('ticker', None)
            ticker = ticker.upper()

            start_date = request.form.get('start_date', None)
            end_date = request.form.get('end_date', None)
            volume_breakout_thresh = request.form.get('volume_breakout_thresh', None)
            volume_breakout_thresh = float(volume_breakout_thresh) / 100

            change_thresh = request.form.get('change_thresh', None)
            change_thresh = float(change_thresh) / 100

            holding_period = request.form.get('holding_period', None)
            holding_period = int(holding_period)

            c = get_conn()
            df = get_data(conn=c, ticker=ticker, start_date=start_date, end_date=end_date)

            df['signal'] = (
                (df['volume'] > (1+volume_breakout_thresh) * df['volume'].rolling(window=N_DAYS).mean()) & \
                (df['return'] > change_thresh)
            ).astype(int)

            df = df.iloc[N_DAYS-1:]

            output = list()
            for idx in df[df['signal'] == 1].index:
                date = df.loc[idx, 'date']
                ret = (1 + df.loc[idx+1: idx+holding_period, 'return']).cumprod().iloc[-1] - 1
                output.append((date, ret))
            session['output'] = pd.DataFrame(output, columns=['date', 'return']).to_json()
    
    except:
        traceback.print_exc()
        abort(500)
    
    return render_template('index.jinja', output='output' in session)

@app.route('/download', methods=['GET'])
def download():
    try:
        if 'output' in session:
            csv_buffer = io.BytesIO()
            pd.read_json(io.StringIO(session['output'])).to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            return send_file(csv_buffer, mimetype='text/csv', as_attachment=True, download_name='output.csv')

        return redirect(url_for('index'))
    
    except:
        traceback.print_exc()
        abort(500)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
