from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import time

engine = create_engine('sqlite:///users.db', echo=False, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    full_name = Column(String)
    usage_count = Column(Integer, default=0)
    request_limit = relationship("RequestLimit", back_populates="user", uselist=False)

class RequestLimit(Base):
    __tablename__ = 'request_limits'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True)
    timestamps = Column(JSON, default=list)
    user = relationship("User", back_populates="request_limit")

Base.metadata.create_all(engine)
user_requests_data = {}
def load_user_requests():
    global user_requests_data
    with Session() as session:
        limits = session.query(RequestLimit).all()
        user_requests_data = {limit.user_id: {"timestamps": limit.timestamps or []} for limit in limits}

load_user_requests()

LIMIT_PERIOD = 90 * 24 * 60 * 60  # 90 روز
MAX_REQUESTS = 10

def add_or_update_user(user_id, username, full_name):
    with Session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.username = username
            user.full_name = full_name
            user.usage_count += 1
        else:
            user = User(user_id=user_id, username=username, full_name=full_name, usage_count=1)
            session.add(user)
        session.commit()

def get_all_users():
    with Session() as session:
        return session.query(User).all()

def save_user_requests():
    with Session() as session:
        for chat_id, data in user_requests_data.items():
            limit = session.query(RequestLimit).filter_by(user_id=chat_id).first()
            if not limit:
                limit = RequestLimit(user_id=chat_id, timestamps=data.get("timestamps", []))
                session.add(limit)
            else:
                existing_ts = set(limit.timestamps or [])
                new_ts = set(data.get("timestamps", []))
                limit.timestamps = list(existing_ts.union(new_ts))
        session.commit()

def can_send_request_db(user_id):
    now = time.time()
    user_data = user_requests_data.get(user_id, {"timestamps": []})
    user_data["timestamps"] = [t for t in user_data["timestamps"] if now - t < LIMIT_PERIOD]
    if len(user_data["timestamps"]) >= MAX_REQUESTS:
        remaining_days = int((LIMIT_PERIOD - (now - user_data["timestamps"][0])) / (24*60*60))
        return False, remaining_days
    return True, MAX_REQUESTS - len(user_data["timestamps"])

def register_request(user_id):
    now = time.time()
    user_data = user_requests_data.get(user_id, {"timestamps": []})
    user_data["timestamps"].append(now)
    user_requests_data[user_id] = user_data
    save_user_requests()