from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///users.db', echo=False, connect_args={'check_same_thread': False})
Base = declarative_base()

Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    full_name = Column(String)
    usage_count = Column(Integer, default=0)

Base.metadata.create_all(engine)

def add_or_update_user(user_id, username, full_name):
    """
    Creates a new session for this transaction.
    Adds a new user or updates an existing one.
    """
    with Session() as session:
        try:
            user = session.query(User).filter_by(user_id=user_id).first()

            if user:
                user.username = username
                user.full_name = full_name
                user.usage_count += 1
            else:
                user = User(user_id=user_id, username=username, full_name=full_name, usage_count=1)
                session.add(user)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")

def get_all_users():
    """
    Creates a new session to fetch all users.
    """
    with Session() as session:
        try:
            return session.query(User).all()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return [] 