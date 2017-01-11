import pymongo    
from psessionDA import PsessionDAO
from flask import Flask, url_for, redirect, render_template, request, session
from flask_oauth import OAuth
import json
import os

app = Flask(__name__)
app.debug = True

mongostr = os.environ['MONGODB_URI']

con = pymongo.MongoClient(mongostr)
DB = con.heroku_vfs22s9f
dao = PsessionDAO(DB)
registers = dao.GetRegisters()
valid_constituencies = [c['constituency'] for c in registers]

g_auth = DB.authorization.find_one({"name":"google"})

# app.secret_key = g_auth["secret_key"]

app.secret_key = os.environ['GOOGLE_CLIENT_SECRET']
google = OAuth().remote_app('google',
                        base_url='https://www.google.com/accounts/',
                        authorize_url='https://accounts.google.com/o/oauth2/auth',
                        request_token_url=None,
                        request_token_params={
                            'scope': 'https://www.googleapis.com/auth/userinfo.email',
                            'response_type': 'code'
                        },
                        access_token_url='https://accounts.google.com/o/oauth2/token',
                        access_token_method='POST',
                        access_token_params={'grant_type': 'authorization_code'},
                        #consumer_key=g_auth["consumer_key"],
                        consumer_key=os.environ['GOOGLE_CLIENT_ID'],
                        #consumer_secret=g_auth["consumer_secret"]
                        consumer_secret=os.environ['GOOGLE_CLIENT_SECRET'])

@app.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError

    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    try:
        user_info = json.load(urlopen(req))
    except URLError as e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))
        return "Error authorizing: " + json.dumps(user_info)

    session["constituency"] = user_info.get("constituency")
    return redirect(url_for("sessions_page",))

@app.route('/login')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route("/oauth2callback")
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')

@app.route('/parliamentarians', methods=['POST', 'GET'])
def parliamentarians_page():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        emergencyphone = request.form.get('emergencyphone')
        emergencycontact = request.form.get('emergencycontact')
        gender = request.form.get('gender')
        constituency = request.form.get('constituency')
        dao.Addparliamentarian(name, dob, gender, constituency, emergencycontact, emergencyphone)
    return render_template('parliamentarians.html', parliamentarians = dao.Getparliamentarians())

@app.route('/parliamentarian_autocomplete')
def parliamentarian_autocomplete():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    term = request.args.get("term")
    return dao.Autocompleteparliamentarian(term)

@app.route('/parliamentarian/<parliamentarian_id>', methods=['POST', 'GET'])
def parliamentarian_page(parliamentarian_id):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        emergencyphone = request.form.get('emergencyphone')
        emergencycontact = request.form.get('emergencycontact')
        gender = request.form.get('gender')
        constituency = request.form.get('constituency')
        dao.Editparliamentarian(name, dob, gender, constituency, emergencycontact, emergencyphone, parliamentarian_id)
        return render_template('parliamentarians.html', parliamentarians = dao.Getparliamentarians())
    return render_template('parliamentarian.html', parliamentarian = dao.Getparliamentarian(parliamentarian_id))

@app.route('/edit_parliamentarian/<parliamentarian_id>', methods=['POST', 'GET'])
def edit_parliamentarian(parliamentarian_id):
    return render_template('edit_parliamentarian.html', parliamentarian = dao.Getparliamentarian(parliamentarian_id, edit=True))

@app.route('/psessions', methods=['POST', 'GET'])
def psessions_page():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        register = request.form.get('register')
        date = request.form.get('date')
        ctype = request.form.get('type')
        dao.AddPsession(register, date, ctype)
    return render_template('psessions.html', psessions = dao.GetPsessions(), registers = dao.GetRegisters())

@app.route('/remove_session/<session_id>', methods=['POST'])
def remove_psession(psession_id):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    dao.RemovePsession(psession_id)
    return redirect(url_for('psessions_page', psession_id=psession_id))

@app.route('/session/<session_id>', methods=['POST', 'GET'])
def psession_page(psession_id):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        payment = request.form.get('payment')
        method = request.form.get('method')
        ptype = request.form.get('type')
        dao.AddPsessionAttendance(psession_id, name, payment, method, ptype)
    return render_template('psession.html', psessionrec = dao.GetPsession(psession_id))

@app.route('/remove_attendance/<psession_id>', methods=['POST'])
def remove_attendance(psession_id):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
        
    parliamentarian_id = request.form.get('parliamentarian_id')
    dao.RemovePsessionAttendance(psession_id, parliamentarian_id)
    return redirect(url_for('session_page', session_id=session_id))

@app.before_request
def check_auth():
    constituency = session.get("constituency")
    if valid_constituencies and constituency and (constituency not in valid_constituencies):
        session.pop('access_token', None)
        session.pop('constituency', None)
        redirect(url_for('login'))

if __name__ == "__main__":
    app.run()

