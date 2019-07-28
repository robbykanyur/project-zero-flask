from flask import Flask, request, render_template, abort
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
load_dotenv()

@app.route('/')
def status_page():
    return render_template('main.html', content='The <strong>emailer</strong> microservice is running.')

@app.route('/api/v1', methods=['GET','POST'])
def send_email():
    if request.method == 'GET':
        return render_template('main.html', content='<strong>Access denied.</strong><br /><br />Your IP address has been logged and this incident has been reported to the authorities.')
    if not request.json or not 'messageSource' in request.json or not 'fromEmail' in request.json or not 'toEmail' in request.json or not 'emailSubject' in request.json or not 'emailHTML' in request.json:
        abort(400);
    if not request.headers.get('Authorization') == ('Bearer ' + os.getenv('AUTH')):
        abort(403);
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
