import traceback
import io
import pandas as pd
import wrds

from flask import (
    Flask,
    request,
    render_template,
    abort,
    send_file,
    make_response
)

N_DAYS = 20
output = None

app = Flask(__name__)
conn = wrds.Connection()

@app.errorhandler(404)
def internal_server_error(e):
    return render_template('404.jinja'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.jinja'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    global output

    try:
        if request.method == 'POST':
            # print(request.form)

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

            df = conn.raw_sql(
                f"select returns.date, returns.vol as volume, returns.ret as return \
                from crsp.dsenames as meta, crsp.dsf as returns \
                where returns.date >= '{start_date}' and returns.date < '{end_date}' \
                and returns.date >= meta.namedt and returns.date < meta.nameendt \
                and meta.ticker = '{ticker}' and meta.permno = returns.permno", date_cols=['date']
            )

            # print(df)

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
            output = pd.DataFrame(output, columns=['date', 'return'])

            # print(output)
    
    except:
        traceback.print_exc()
        abort(500)
    
    return render_template('index.jinja', output=output.to_html() if output is not None else None)

@app.route('/download', methods=['GET'])
def download():
    global output

    try:
        csv_buffer = io.BytesIO()
        output.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return send_file(csv_buffer, mimetype='text/csv', as_attachment=True, download_name='output.csv')
    
    except:
        traceback.print_exc()
        abort(500)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
