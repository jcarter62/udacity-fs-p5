import uuid

from flask import Flask, jsonify, render_template, request, redirect, url_for, escape, session as flask_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth

from models import Base, User, Item, Category, DBName, Sample
import json
import datetime

auth = HTTPBasicAuth()

engine = create_engine(DBName)

Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
# Session = DBSession()
app = Flask(__name__)
app.secret_key = 'this is a secret key'

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
            'logged_in': user_logged_in(request)
        }
        return render_template("login.html", data=data)
    else: # POST
        print request.form['user_name']
        print request.form['user_password']
        #
        # Validate User & Password, or by other method
        #
        flask_session['username'] = request.form['user_name']
        return redirect('/')

@app.route('/logout')
def logout():
    wipe_session()
    return redirect('/')

@app.route('/<categoryid>', methods=['GET'])
def main_catid(categoryid):
    return homepage_content(request, catid=categoryid)


@app.route('/item/<itemid>', methods=['GET'])
def main_itemid(itemid):
    return homepage_content(request, itemid=itemid)


@app.route('/edit/<itemid>', methods=['GET'])
def main_edit_itemid(itemid):
    return item_edit_content(request, itemid=itemid)


@app.route('/delete/<itemid>', methods=['GET'])
def main_delete_itemid(itemid):
    return item_delete_content(request, itemid=itemid)


@app.route('/save', methods=['POST'])
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
    #TODO: handle invalid item_id
    this_id = request.form['item_id']

    session = Session()
    for record in session.query(Item).filter_by(id=this_id).all():
        session.delete(record)
    session.commit()
    session.close()

    new_url = '/'
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
            'logged_in': user_logged_in(request)
        }
        return render_template("item_add.html", data=data)


def homepage_content(request, catid='', itemid=0, edit_item=0):
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
    data.session = get_session_info(request)

    return render_template("main.html", data=data)


def item_edit_content(request, itemid=0):
    data = request.form
    data.title = 'Edit Item'
    cat_list = api_categories()
    item_detail = api_one_item(itemid)
    data.categories = cat_list.json
    data.item = item_detail.json
    data.logged_in = user_logged_in(request)
    return render_template("item_edit.html", data=data)


def item_delete_content(request, itemid=0):
    data = request.form
    data.title = 'Delete Item'
    cat_list = api_categories()
    item_detail = api_one_item(itemid)
    data.categories = cat_list.json
    data.item = item_detail.json
    data.logged_in = user_logged_in(request)
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

    print 'user logged in: ' + flask_session['loggedIn']
    return logged_in

def get_session_info(request):
    def new_sid():
        guid = str(uuid.uuid4()).replace('-','')
        return guid

    if 'sid' in flask_session:
        sid = flask_session['sid']
    else:
        sid = new_sid()
        flask_session['sid'] = sid

    username = ''
    if 'username' in flask_session:
        username = flask_session['username']

    session_info = {
        'logged_in': user_logged_in(request),
        'username': username,
        'sid': sid
    }
    print 'Session Info: ' + json.dumps(session_info)
    return session_info

def wipe_session():
    if 'username' in flask_session:
        flask_session.pop('username', None)
    if 'sid' in flask_session:
        flask_session.pop('sid', None)
    return

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
