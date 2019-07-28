from flask import Flask, request, render_template, abort
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
load_dotenv()

@app.route('/')
def status_page():
    return(render_template('main.html', content='The <strong>emailer</strong> microservice is running.'))

@app.route('/api/v1/form', methods=['GET','POST'])
def api_v1_form():
    if request.method == 'GET':
        return render_template('main.html', content='<strong>Access denied.</strong><br /><br />Your IP address has been logged and this incident has been reported to the authorities.')
    if not request.json:
        abort(400);
    if not request.headers.get('Authorization') == ('Bearer ' + os.getenv('AUTH')):
        abort(403);

    return(_add_row_to_sheet('Form Submissions', request.json))

# PRIVATE FUNCTIONS #

def _add_row_to_sheet(sheet_name, data):
    try:
        sheet = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(
            './client_secret.json',
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )).open_by_key("1kKqs94jLBiiatyjpx-t7kf4N2RpzjuiyPWOrqkQPI08").worksheet(sheet_name)
        number_of_rows = len(sheet.get_all_values()) + 1

        if sheet_name == 'Form Submissions':
            new_row = ['','','','']
            if 'sourceForm' in data:
                new_row[0] = data['sourceForm']
            if 'formName' in data:
                new_row[1] = data['formName']
            if 'formEmail' in data:
                new_row[2] = data['formEmail']
            if 'formMessage' in data:
                new_row[3] = data['formMessage']

            for x, y in enumerate(new_row):
                sheet.update_cell(number_of_rows, x + 1, y)

            print(sheet.get_all_values())

        return '200'
    except Exception as e:
        return '500'


def _send_email(htmlContent):
    message_source = request.json['messageSource']
    message = Mail(
        from_email=request.json['fromEmail'],
        to_emails=request.json['toEmail'],
        subject=request.json['emailSubject'],
        html_content=request.json['emailHTML'],
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


