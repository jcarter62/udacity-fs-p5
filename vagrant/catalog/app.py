import datetime
import json
import uuid

import httplib2
import requests
from flask import Flask, jsonify, render_template, request, redirect, escape, \
    session as flask_session
from flask import make_response
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import Base, User, Item, Category, DBName

auth = HTTPBasicAuth()

engine = create_engine(DBName)

Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
# Session = DBSession()
app = Flask(__name__)
app.secret_key = 'this is a secret key'

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


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
            'logged_in': user_logged_in(),
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
                'logged_in': user_logged_in(),
                'message': 'Login Failed, ' +
                           'due to incorrect Username or Password',
                'client_id': CLIENT_ID,
                'session': get_session_info()
            }
            '''
            Login Failed, so send them back to login.html
            '''
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
            'logged_in': user_logged_in(),
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
                client_id = str(uuid.uuid4()).replace('-', '')
                user = User(username=username,
                            login_type='simple', client_id=client_id)
                user.hash_password(pw1)
                session.add(user)
                session.commit()

            session.close()

        return redirect('/login')


@app.route('/oauth/<provider>', methods=['POST'])
def login_provider(provider):
    # STEP 1 - Parse the auth code
    auth_code = request.data
    print '/oauth/' + provider
    # print "Step 1 - Complete, received auth code %s" % auth_code
    if provider == 'google':
        # STEP 2 - Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                                 scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."),
                401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(
                json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # STEP 3 - Find User or make a new one

        # Get user info
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
        user = session.query(User) \
            .filter_by(client_id=client_id, login_type='google').first()
        if not user:
            user = User(username=name, picture=picture, email=email,
                        client_id=client_id, login_type='google')
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
            'logged_in': user_logged_in(),
            'message': '',
            'client_id': CLIENT_ID,
            'session': get_session_info()
        }
        return render_template("logout.html", data=data)
    else:
        # 'POST'
        wipe_session()
        return redirect('/')


#
# Session methods
#

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


@app.route('/category/add', methods=['GET', 'POST'])
def category_add():
    if request.method == 'POST':
        this_name = escape(request.form['name'])

        record = Category(name=this_name)

        session = Session()
        session.add(record)
        session.commit()
        session.close()

        return homepage_content(request)
    elif request.method == 'GET':
        cat_list = api_categories()
        categories = []
        for c in cat_list.json:
            print c['name']
            categories.append(c['name'])

        data = {
            'title': 'Add Category',
            'categories': categories,
            'category': '',
            'logged_in': user_logged_in(),
            'session': get_session_info(),
            'message': ''
        }
        return render_template("category_add.html", data=data)


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
    this_name = escape(request.form['item_name'])
    this_id = request.form['item_id']
    this_desc = escape(request.form['item_text'])
    this_cat = request.form['item_cat']

    session = Session()
    for record in session.query(Item).filter_by(id=this_id).all():
        # Update fields for this record.
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
        this_client_id = request.form['client_id']

        record = Item(categoryid=this_cat, description=this_desc,
                      name=this_name, create_date=this_create_date)

        record.client_id = this_client_id

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
            'logged_in': user_logged_in(),
            'session': get_session_info(),
            'message': ''
        }
        return render_template("item_add.html", data=data)


def homepage_content(request, catid='', itemid=0, edit_item=0, message=''):
    """
    This method prepares the template data needed for most page renderings.

    :param request: http request object
    :param catid: Optional
    :param itemid: Optional
    :param edit_item: Optional
    :param message: Optional
    :return: rendered page template
    """

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
        data.logged_in = user_logged_in()
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
    data.logged_in = user_logged_in()
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
    data.logged_in = user_logged_in()
    data.message = ''
    data.session = get_session_info()
    return render_template("item_delete.html", data=data)


# noinspection PyBroadException
def user_logged_in():
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

    json_records = [r.serialize for r in recs]
    session.close()
    return jsonify(json_records)


def get_users(db_session):
    """return a list of client_id and username.
    :rtype: dict
    :type db_session: Session()
    """
    result = {}
    userlist = db_session.query(User).all()
    for user in userlist:
        result[user.client_id] = user.username
    return result


@app.route('/api/v1/items')
def api_items(sortby='', category=''):
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
        recs = session.query(Item).filter_by(categoryid=selected_id).all()

    users = get_users(session)


    json_records = [r.serialize for r in recs]
    session.close()

    # Add formatted date and owner to result set.
    for j in json_records:
        j['fmtdate'] = j['create_date'].__format__('%m/%d/%Y %H:%M')
        client_id = j['client_id']
        j['owner'] = users[client_id]

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
        users = get_users(session)
        session.close()

        owner = users[one_record.client_id]
        one = {
            'client_id': one_record.client_id,
            'create_date': one_record.create_date,
            'description': one_record.description,
            'categoryid': one_record.categoryid,
            'id': one_record.id,
            'name': one_record.name,
            'owner': owner
        }
        result = jsonify(one)

        return result
    except:
        return jsonify({})


@app.route('/api/v1/catalog')
def api_catalog():
    category_list = []
    session = Session()
    categories = session.query(Category).order_by(Category.name).all()
    for cat in categories:
        thiscat = {'category': cat.name, 'id': cat.id}
        thisid = cat.id
        items = session.query(Item).filter_by(categoryid=thisid).all()
        thisitems = []
        for i in items:
            thisitems.append({
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'category_id': i.categoryid
            })
        thiscat['items'] = thisitems
        category_list.append(thiscat)

    result = jsonify({'catalog': category_list})
    return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
