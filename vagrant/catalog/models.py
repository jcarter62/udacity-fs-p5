from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import urllib
from datetime import datetime, timedelta


Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
DBName = 'sqlite:///catalogApp.db'

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String)
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description
        }

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    categoryid = Column(Integer)
    name = Column(String)
    description = Column(String)
    create_date = Column(DateTime, default=datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'categoryid': self.categoryid,
            'name': self.name,
            'description': self.description,
            'create_date': self.create_date
        }

class Sample:
    def category(self):
        def buildone(name,desc=''):
            return {"name":name, "description": desc}
        items = [
            buildone('Soccer'),
            buildone('Basketball'),
            buildone('Baseball'),
            buildone('Frisbee'),
            buildone('Snowboarding')
        ]
        return items

    def item(self):
        def buildone(name,categoryid,desc='', offset=0):
            return {'name':name, 'categoryid':categoryid, \
                    'description': getdesc(), \
                    'create_date': getdatetime(offset)
                    }

        def getdesc():
            link = "https://loripsum.net/api/1/medium/plaintext"
            f = urllib.urlopen(link)
            result = f.read()
            return result

        def getdatetime(offset):
            dt = datetime.now() +  timedelta(seconds=offset)
            return dt

        items = [
            buildone('apples', 1),
            buildone('grapes', 1, offset=100),
            buildone('peppers', 2, offset=1000),
            buildone('pizza', 2, offset=1500),
            buildone('pears', 3, offset=300),
            buildone('bread', 4, offset=600),
        ]
        return items


engine = create_engine(DBName)

Base.metadata.create_all(engine)
