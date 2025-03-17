from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///users.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    full_name = Column(String)
    usage_count = Column(Integer, default=0)


Base.metadata.create_all(engine)

def add_or_update_user(user_id, username, full_name):
    user = session.query(User).filter_by(user_id=user_id).first()

    if user:
        user.usage_count += 1
    else:
        user = User(user_id=user_id, username=username, full_name=full_name, usage_count=1)
        session.add(user)

    session.commit()

def get_all_users():
    return session.query(User).all()
