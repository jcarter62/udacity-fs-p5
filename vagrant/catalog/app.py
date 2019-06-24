from flask import Flask, jsonify, render_template, request, redirect, url_for
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth

from models import Base, User, Item, Category, DBName, Sample
import json

auth = HTTPBasicAuth()

engine = create_engine(DBName)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    return homepage_content(request)

@app.route('/<categoryid>', methods=['GET'])
def main_catid(categoryid):
    return homepage_content(request, catid=categoryid)

@app.route('/item/<itemid>', methods=['GET'])
def main_itemid(itemid):
    return homepage_content(request, itemid=itemid)

@app.route('/edit/<itemid>', methods=['GET'])
def main_edit_itemid(itemid):
    return homepage_content(request, itemid=itemid, edit_item=1)

@app.route('/save', methods=['POST'])
def item_save():
    #
    # find record based on form data.
    #
    # db.update(table_name).values(attribute = new_value).where(condition)
    this_id = request.form['item_id']
    this_desc = request.form['item_text']

    for record in session.query(Item).filter_by(id=this_id).all():
        record.description = this_desc
    session.commit()

    print 'id:' + str(this_id)

    new_url = '/item/' + str(this_id)
    return redirect(new_url)

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
    one_item = item_detail.json

    if is_not_empty(one_item):
        data.show_item = 1
        data.item = item_detail.json
        data.edit_item = edit_item
    else:
        data.show_item = 0

    return render_template("main.html", result=data)


@app.route('/api/v1/categories')
@app.route('/api/v1/categories/<catid>')
def api_categories(catid=''):
    recs = []
    if catid == '':
        recs = session.query(Category).all()
    else:
        recs = session.query(Category).filter_by(name=catid)

    # Create sample data if empty
    if recs == []:
        sample = Sample()
        for eachRec in sample.category():
            rec = Category(name=eachRec['name'], description=eachRec['description'])
            session.add(rec)
        session.commit()
        recs = session.query(Category).all()

    json_records = [r.serialize for r in recs]
    return jsonify( json_records )

@app.route('/api/v1/items')
def api_items(sortby='', category=''):
    def cmpdatedec(a,b):
        aval = a.create_date
        bval = b.create_date
        if aval > bval:
            return 1
        elif aval < bval:
            return -1
        return 0

    selected_id = 0
    if category != '':
        # See if we have this type of category
        catrec = session.query(Category).filter_by(name=category).one()
        if catrec:
            selected_id = catrec.id
        else:
            selected_id = 0


    if selected_id <= 0:
        recs = session.query(Item).all()
    else:
        recs = session.query(Item).filter_by(categoryid=selected_id).all()

    if sortby=='date desc':
        recs.sort(cmp=cmpdatedec)

    # Create sample data if empty
    if recs == []:
        sample = Sample()
        for eachRec in sample.item():
            rec = Item(name=eachRec['name'], categoryid=eachRec['categoryid'], \
                       description=eachRec['description'], \
                       create_date=eachRec['create_date'])
            session.add(rec)
        session.commit()
        recs = session.query(Item).all()

    json_records = [r.serialize for r in recs]
    return jsonify( json_records )

@app.route('/api/v1/items/<itemid>')
def api_one_item(itemid):
    # noinspection PyBroadException
    try:
        one_record = session.query(Item).filter_by(id=itemid).one()
        return jsonify( one_record.serialize )
    except :
        return jsonify( {} )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
