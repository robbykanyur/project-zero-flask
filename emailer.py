from flask import Flask, request, render_template
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
    message = Mail(
        from_email='robert@theoakco.com',
        to_emails='robertkanyur+a@gmail.com',
        subject='test message 2',
        html_content='test successful',
    )

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID'))
        response = sg.send(message)
        return render_template('main.html', content=response.body)
    except Exception as e:
        return(str(e))
