from flask import Flask, request, render_template, abort
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from redis import Redis
import rq
import time

load_dotenv()

app = Flask(__name__)
app.redis = Redis.from_url(os.getenv('REDIS_URL'))
app.tasks = rq.Queue('emailer-tasks', connection=app.redis)

@app.route('/')
def status_page():
    return(render_template('main.html', content='The <strong>emailer</strong> microservice is running.'))

@app.route('/api/v1/form', methods=['GET','POST'])
def api_v1_form():
    if request.method == 'GET':
        return render_template('main.html', content='<strong>Access denied.</strong><br /><br />Your IP address has been logged and this incident has been reported to the authorities.')
    if not request.json and 'sourceForm' not in request.json:
        abort(400);
    if not request.headers.get('Authorization') == ('Bearer ' + os.getenv('AUTH')):
        abort(403);

    utc_now =  datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    html_content = _generate_email_message(request.json)
    sheets_job = app.tasks.enqueue(_add_row_to_sheet, 'Form Submissions', request.json, utc_now)
    email_job = app.tasks.enqueue(_send_email, html_content, utc_now, request.json)

    print(sheets_job.get_id())
    print(email_job.get_id())

    return '200'

# PRIVATE FUNCTIONS #

def _generate_email_message(data):
    if data['sourceForm'] == 'Contact':
        return(
            '<p>You should reach out to them as soon as possible. Here is their message and contact information:</p>' +
            '<p>Name: ' + data["formName"] + '<br />Email: ' + data["formEmail"] + '<br />Message: ' + data['formMessage']
        )
    elif data['sourceForm'] == 'Team' or data['sourceForm'] == 'Serve':
        return(
            '<p>You should reach out to them as soon as possible. Here is their contact information:</p>' +
            '<p>Name: ' + data["formName"] + '<br />Email: ' + data["formEmail"]
        )
    else:
        return('Something went wrong.')

# REDIS FUNCTIONS #

def _add_row_to_sheet(sheet_name, data, utc_now):
    try:
        sheet = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(
            './client_secret.json',
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )).open_by_key("1kKqs94jLBiiatyjpx-t7kf4N2RpzjuiyPWOrqkQPI08").worksheet(sheet_name)
        number_of_rows = len(sheet.get_all_values()) + 1

        if sheet_name == 'Form Submissions':
            new_row = ['','','','','']
            new_row[0] = utc_now
            if 'sourceForm' in data:
                new_row[1] = data['sourceForm']
            if 'formName' in data:
                new_row[2] = data['formName']
            if 'formEmail' in data:
                new_row[3] = data['formEmail']
            if 'formMessage' in data:
                new_row[4] = data['formMessage']

        generated_range = ("A%s:E%s" %(number_of_rows, number_of_rows))
        cell_list = sheet.range(generated_range)
        for x, y in enumerate(new_row):
            cell_list[x].value = y
        sheet.update_cells(cell_list)

        return '200'
    except Exception as e:
        return '500'

def _send_email(html_content, utc_now, data):
    message_source = data['sourceForm']
    subject = ("New form submission from the %s page (%s)" %(message_source, utc_now))
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=os.getenv("TO_EMAIL"),
        subject=subject,
        html_content=html_content,
    )
    try:
        if os.getenv('SENDGRID_ENABLED') == 'True':
            sg = SendGridAPIClient(os.getenv('SENDGRID'))
            response = sg.send(message)
            return(str(response.status_code))
        else:
            return('200')
    except Exception as e:
        if os.getenv('SENDGRID_ENABLED') == 'True':
            return(str(e))
        else:
            abort(500)
