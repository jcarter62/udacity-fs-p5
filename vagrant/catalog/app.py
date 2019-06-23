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
    return homepage_content(request, categoryid)

def homepage_content(request, catid=''):
    data = request.form
    data.title = 'main'
    cat_list = api_categories()
    item_list = api_items()
    data.category = catid
    data.categories = cat_list.json
    data.items = item_list.json
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
def api_items():
    recs = session.query(Item).all()

    # Create sample data if empty
    if recs == []:
        sample = Sample()
        for eachRec in sample.item():
            rec = Item(name=eachRec['name'], categoryid=eachRec['categoryid'], description=eachRec['description'])
            session.add(rec)
        session.commit()
        recs = session.query(Item).all()

    json_records = [r.serialize for r in recs]
    return jsonify( json_records )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
