import uuid

from flask import Flask, jsonify, render_template, request, redirect, url_for, escape, session as flask_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth

from models import Base, User, Item, Category, DBName, Sample
import json
import datetime

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests

from passlib.apps import custom_app_context as pwd_context

auth = HTTPBasicAuth()

engine = create_engine(DBName)

Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
# Session = DBSession()
app = Flask(__name__)
app.secret_key = 'this is a secret key'

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']


@app.route('/', methods=['GET'])
def main():
    return homepage_content(request)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        data = {
            'title': 'Login',
            'user_name': '',
            'user_password': '',
            'logged_in': user_logged_in(request),
            'message': '',
            'client_id': CLIENT_ID,
            'session': get_session_info()
        }
        return render_template("login.html", data=data)
    else:  # POST
        #
        # Validate User & Password, or by other method
        #
        username = request.form['user_name']
        password = request.form['user_password']
        client_id = ''

        #
        # Determine if they are correct.
        #
        up_valid = False
        session = Session()

        user = session.query(User).filter_by(username=username,
                                             login_type='simple').first()
        if user:
            if user.verify_password(password):
                up_valid = True
                client_id = user.client_id
            else:
                up_valid = False

        session.close()

        if not up_valid:
            data = {
                'title': 'Login',
                'user_name': username,
                'user_password': password,
                'logged_in': user_logged_in(request),
                'message': 'Login Failed, due to incorrect Username or Password',
                'client_id': CLIENT_ID,
                'session': get_session_info()
            }
            return render_template("login.html", data=data)
        else:
            # Valid Username, so then complete the login process.
            flask_session['username'] = username
            flask_session['method'] = 'simple'
            flask_session['client_id'] = client_id

            return redirect('/')


@app.route('/login/create', methods=['GET', 'POST'])
def login_create():
    if request.method == 'GET':
        data = {
            'title': 'Create Account',
            'user_name': '',
            'user_password': '',
            'logged_in': user_logged_in(request),
            'message': '',
            'session': get_session_info()
        }
        return render_template("create_account.html", data=data)
    elif request.method == 'POST':
        proceed = True
        # Create Account.
        username = request.form['user_name']
        pw1 = request.form['password1']
        pw2 = request.form['password2']

        if proceed and (username <= ''):
            proceed = False

        if proceed and (pw1 <= ''):
            proceed = False

        if proceed and (pw1 != pw2):
            proceed = False

        if proceed:
            # save username in db and redirect to login route

            session = Session()
            user_exists = False

            user = session.query(User).filter_by(username=username,
                                                 login_type='simple').first()
            if user:
                # check to see if password is correct.
                if user.verify_password(pw1):
                    user_exists = True

            if not user_exists:
                client_id = str(uuid.uuid4()).replace('-','')
                user = User(username=username,
                            login_type='simple', client_id=client_id)
                user.hash_password(pw1)
                session.add(user)
                session.commit()

            session.close()

        return redirect('/login')


@app.route('/login-google', methods=['POST'])
def login_google():
    data = request.data

    print data
    return redirect('/')


@app.route('/oauth/google', methods=['POST'])
def login_provider():
    # STEP 1 - Parse the auth code
    auth_code = request.data
    print "Step 1 - Complete, received auth code %s" % auth_code
    provider = 'google'
    if provider == 'google':
        # STEP 2 - Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # stored_credentials = login_session.get('credentials')
        # stored_gplus_id = login_session.get('gplus_id')
        # if stored_credentials is not None and gplus_id == stored_gplus_id:
        #     response = make_response(json.dumps('Current user is already connected.'), 200)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response
        # print "Step 2 Complete! Access Token : %s " % credentials.access_token

        # STEP 3 - Find User or make a new one

        # Get user info
        h = httplib2.Http()
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        #
        # TODO: Add client_id, and login_type to user table + flask_session
        #
        name = data['name']
        picture = data['picture']
        email = data['email']
        client_id = data['id']

        # see if user exists, if it doesn't make a new one
        session = Session()
        user = session.query(User).filter_by(client_id=client_id, login_type='google').first()
        if not user:
            user = User(username=name, picture=picture, email=email, client_id=client_id, login_type='google')
            session.add(user)
            session.commit()


        # STEP 4 - Make token
        token = user.generate_auth_token(600)


        flask_session['username'] = user.username
        flask_session['picture'] = user.picture
        flask_session['email'] = user.email
        flask_session['method'] = 'google'
        flask_session['token'] = token
        flask_session['client_id'] = user.client_id

        session.close()


        # STEP 5 - Send back token to the client
        return jsonify({'token': token.decode('ascii')})

        # return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'GET':
        data = {
            'title': 'Login',
            'user_name': '',
            'user_password': '',
            'logged_in': user_logged_in(request),
            'message': '',
            'client_id': CLIENT_ID,
            'session': get_session_info()
        }
        return render_template("logout.html", data=data)
    else:
        # 'POST'
        wipe_session()
        return redirect('/')


def get_session_vars():
    return ['username', 'picture', 'email',
            'method', 'token', 'loggedIn', 'sid',
            'client_id']


def wipe_session():
    names = get_session_vars()
    for name in names:
        if name in flask_session:
            flask_session.pop(name, None)
    return


def get_session_info():
    data = {}
    names = get_session_vars()
    for name in names:
        data[name] = flask_session.get(name, '')
    return data


@app.route('/category/<categoryid>', methods=['GET'])
def main_catid(categoryid):
    return homepage_content(request, catid=categoryid)


@app.route('/item/delete_fail')
def item_delete_failed_noid():
    msg = 'Item Delete Failed'
    return homepage_content(request, message=msg)


@app.route('/item/delete_fail/<int:itemid>')
def item_delete_failed(itemid=0):
    msg = 'Item Delete Failed for id:' + str(itemid)
    return homepage_content(request, message=msg)


@app.route('/item/<int:itemid>', methods=['GET'])
def main_itemid(itemid):
    return homepage_content(request, itemid=itemid)


@app.route('/edit/<int:itemid>', methods=['GET'])
def main_edit_itemid(itemid):
    return item_edit_content(request, itemid=itemid)


@app.route('/delete/<int:itemid>', methods=['GET'])
def main_delete_itemid(itemid):
    return item_delete_content(request, itemid=itemid)


@app.route('/item/save', methods=['POST'])
def item_save():
    #
    # find record based on form data.
    #
    # db.update(table_name).values(attribute = new_value).where(condition)
    this_name = escape(request.form['item_name'])
    this_id = request.form['item_id']
    this_desc = escape(request.form['item_text'])
    this_cat = request.form['item_cat']

    session = Session()
    for record in session.query(Item).filter_by(id=this_id).all():
        record.description = this_desc
        record.name = this_name
        record.categoryid = this_cat
    session.commit()
    session.close()

    new_url = '/item/' + str(this_id)
    return redirect(new_url)


@app.route('/delete', methods=['POST'])
def item_delete():
    #
    # find record based on form data.
    #
    # TODO: handle invalid item_id
    this_id = request.form['item_id']

    new_url = '/'

    session = Session()
    record_count = session.query(Item).filter_by(id=this_id).count()
    if record_count == 1:
        for record in session.query(Item).filter_by(id=this_id).all():
            session.delete(record)
        session.commit()
    else:
        new_url = '/item/delete_fail/' + str(this_id)

    session.close()

    return redirect(new_url)


@app.route('/add', methods=['POST', 'GET'])
def item_add():
    if request.method == 'POST':
        this_name = escape(request.form['item_name'])
        this_desc = escape(request.form['item_text'])
        this_cat = request.form['item_cat']
        this_create_date = datetime.datetime.now()

        record = Item(categoryid=this_cat, description=this_desc, \
                      name=this_name, create_date=this_create_date)

        session = Session()
        session.add(record)
        session.commit()
        session.close()

        return homepage_content(request)
    elif request.method == 'GET':
        cat_list = api_categories()

        data = {
            'title': 'Add Item',
            'categories': cat_list.json,
            'item': {
                'name': '',
                'categoryid': 0,
                'description': ''
            },
            'logged_in': user_logged_in(request),
            'session': get_session_info(),
            'message': ''
        }
        return render_template("item_add.html", data=data)


def homepage_content(request, catid='', itemid=0, edit_item=0, message=''):
    def is_not_empty(any_structure):
        if any_structure:
            return True
        else:
            return False

    data = request.form
    data.title = 'main'
    cat_list = api_categories()
    item_list = api_items(sortby='date desc', category=catid)
    item_detail = api_one_item(itemid)
    data.category = catid
    data.categories = cat_list.json
    data.items = item_list.json
    data.items_count = data.items.__len__()
    one_item = item_detail.json

    if is_not_empty(one_item):
        data.show_item = 1
        data.item = item_detail.json
        data.edit_item = edit_item
    else:
        data.show_item = 0

    # noinspection PyBroadException
    try:
        data.logged_in = user_logged_in(request)
    except:
        data.logged_in = False
    data.session = get_session_info()
    data.message = message

    return render_template("main.html", data=data)


def item_edit_content(request, itemid=0):
    data = request.form
    data.title = 'Edit Item'
    cat_list = api_categories()
    item_detail = api_one_item(itemid)
    data.categories = cat_list.json
    data.item = item_detail.json
    data.logged_in = user_logged_in(request)
    data.message = ''
    data.session = get_session_info()

    return render_template("item_edit.html", data=data)


def item_delete_content(request, itemid=0):
    data = request.form
    data.title = 'Delete Item'
    cat_list = api_categories()
    item_detail = api_one_item(itemid)
    data.categories = cat_list.json
    data.item = item_detail.json
    data.logged_in = user_logged_in(request)
    data.message = ''
    data.session = get_session_info()
    return render_template("item_delete.html", data=data)


# noinspection PyBroadException
def user_logged_in(request):
    logged_in = False
    try:
        if 'username' in flask_session:
            flask_session['loggedIn'] = 'yes'
            logged_in = True
        else:
            flask_session['loggedIn'] = 'no'
    except:
        flask_session['loggedIn'] = 'no'

    return logged_in

#
# API Routes
#

@app.route('/api/v1/categories')
@app.route('/api/v1/categories/<catid>')
def api_categories(catid=''):
    recs = []

    session = Session()
    try:
        if catid == '':
            recs = session.query(Category).all()
        else:
            recs = session.query(Category).filter_by(name=catid)
    except Exception, e:
        print 'API_Categories Error: ' + str(e)

    # Create sample data if empty
    if not recs:
        sample = Sample()
        for eachRec in sample.category():
            rec = Category(name=eachRec['name'], description=eachRec['description'])
            session.add(rec)
        session.commit()
        recs = session.query(Category).all()

    json_records = [r.serialize for r in recs]
    session.close()
    return jsonify(json_records)


@app.route('/api/v1/items')
def api_items(sortby='', category=''):
    all_records = True
    selected_id = 0
    category_specified = (category.__len__() > 0)

    session = Session()
    if category_specified:
        # See if we have this type of category
        catrec = session.query(Category).filter_by(name=category).one()
        if catrec:
            selected_id = catrec.id
        else:
            selected_id = 0

    if selected_id == 0:
        recs = session.query(Item).all()
    else:
        all_records = False
        recs = session.query(Item).filter_by(categoryid=selected_id).all()

    # Create sample data if empty
    if all_records and (recs == []):
        sample = Sample()
        for eachRec in sample.item():
            rec = Item(name=eachRec['name'], categoryid=eachRec['categoryid'], \
                       description=eachRec['description'], \
                       create_date=eachRec['create_date'])
            session.add(rec)
        session.commit()
        recs = session.query(Item).all()

    json_records = [r.serialize for r in recs]
    session.close()

    for j in json_records:
        j['fmtdate'] = j['create_date'].__format__('%m/%d/%Y %H:%M')

    def cmpdatedec(a, b):
        try:
            aval = a.create_date
            bval = b.create_date
            if aval < bval:
                return 1
            elif aval > bval:
                return -1
            return 0
        except:
            return 0

    if sortby == 'date desc':
        recs.sort(cmp=cmpdatedec)

    return jsonify(json_records)


@app.route('/api/v1/items/<itemid>')
def api_one_item(itemid):
    # noinspection PyBroadException
    try:
        session = Session()
        one_record = session.query(Item).filter_by(id=itemid).one()
        session.close()
        #
        # one_record['fmtdate'] = one_record['create_date'].__format__('%m/%d/%Y %H:%M')
        #
        return jsonify(one_record.serialize)
    except:
        return jsonify({})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
