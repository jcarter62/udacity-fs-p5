import random
import string

from itsdangerous import \
    (TimedJSONWebSignatureSerializer as Serializer,
     BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                     for x in xrange(32))

import os

# SQLite database path
if os.sys.platform == 'linux2':
    db_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    # db_root = '/var/local/'
    if not os.path.exists(db_root):
        os.makedirs(db_root)
else:
    db_root = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(db_root, 'catalogApp.db')

print 'dbpath = ' + db_path
DBName = 'sqlite:///' + db_path
# SQLite database path


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String)
    password_hash = Column(String(64))
    client_id = Column(String)
    login_type = Column(String)  # simple, or google

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
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    categoryid = Column(Integer)
    name = Column(String)
    description = Column(String)
    create_date = Column(DateTime)
    client_id = Column(String)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'categoryid': self.categoryid,
            'name': self.name,
            'description': self.description,
            'create_date': self.create_date,
            'client_id': self.client_id
        }


engine = create_engine(DBName)

Base.metadata.create_all(engine)
