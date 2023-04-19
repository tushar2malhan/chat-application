from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, json
from flask_cors import CORS
from pusher import pusher
import boto3
from boto3.dynamodb.conditions import Key
import uuid

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'secret_key'

# Create a file to store user credentials if it doesn't exist
if not os.path.exists('user_credentials.txt'):
    with open('user_credentials.txt', 'w') as f:
        f.write('')

# Pusher setup
pusher = pusher_client = pusher.Pusher(
  app_id='1587091',
  key='c4b2719a837f669e59ca',
  secret='0e87926247b9cf3cbf41',
  cluster='ap2',
  ssl=True
)


dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id='AKIA5UOMHERXTEIB4LRW',
    aws_secret_access_key='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',
    region_name='ap-south-1'
)

# Get the Users table
table = dynamodb.Table('Users')


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Generate a unique ID for the user
        user_id = str(uuid.uuid4())

        # Save user credentials in DynamoDB
        table.put_item(Item={
            'id': user_id,
            'name': name,
            'email': email,
            'password': password
        })

        # Redirect to the login page
        return redirect(url_for('login'))

    # If not a POST request, show the registration form
    return render_template('register.html')


# Index route for logged in users
@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('register'))
    elif session['logged_in']:
        # if session.get('admin'):
        #     return render_template('admin.html')
        # else:
            return render_template('index.html')
    
@app.route('/admin')
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('register'))
    elif session['logged_in']:
            return render_template('admin.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        print(name, password)
        # Query DynamoDB for the user with the given name
        
        response = table.query(
            IndexName='name-index',
            KeyConditionExpression=Key('name').eq(name)
        )

        if response['Items'] and response['Items'][0]['password'] == password:
            # Set user as logged in using session
            session['logged_in'] = True
            session['user_id'] = response['Items'][0]['id']
            # session['admin'] = response['Items'][0]['admin'] == 'true'
            return redirect(url_for('index'))

        return render_template('login.html', error='Invalid name or password')

    elif 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'})


@app.route('/new/guest', methods=['POST'])
def guestUser():
    data = request.json

    pusher.trigger(u'general-channel', u'new-guest-details', {
        'name': data['name'],
        'email': data['email']
    })

    return json.dumps(data)


@app.route("/pusher/auth", methods=['POST'])
def pusher_authentication():
    auth = pusher.authenticate(channel=request.form['channel_name'],socket_id=request.form['socket_id'])
    return json.dumps(auth)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
