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


@app.route("/", methods=['GET'])
def main():
    data = request.form
    data.title = 'main'
    data.categories = api_categories()
    return render_template("main.html", result=data)


@app.route("/api/v1/categories")
def api_categories():
    recs = session.query(Category).all()

    # Create sample data if empty
    if recs == []:
        sample = Sample()
        for eachRec in sample.category():
            rec = Category(name=eachRec['name'], description=eachRec['description'])
            session.add(rec)
        session.commit()
        recs = session.query(Category).all()

    json_records = [r.serialize for r in recs]

#    return jsonify([r.serialize for r in recs] )
    return json_records

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
