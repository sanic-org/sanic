""" SQLAlchemy integration demo
Use sqlalchemy to connect a in-memory sqlite database
Defined a table User contains id, name, fullname, password as its columns
Provider RESTFul service
GET /users to get all of users in User table
POST /user to create user
GET /users/{id} to get user with specific id

Could test it with after running the sanic server:
curl http://localhost:8000/users
curl http://localhost:8000/users/1
curl http://localhost:8000/users/4
curl http://localhost:8000/user --data '{"name": "ed", "password":"f8s7ccs","fullname":"Ed Jones"}'
"""

from sanic import Sanic
from sanic.response import json
from sanic.exceptions import NotFound
from sqlalchemy import (
    Column, String, Integer, Sequence,
    create_engine
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(12))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "fullname": self.fullname,
            "password": self.password,
        }

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

session = sessionmaker()
session.configure(bind=engine)

s = session()
s.add_all([
    User(name="wendy", fullname="Wendy Williams", password="foobar"),
    User(name="mary", fullname="Mary Contrary", password="xxg527"),
    User(name="fred", fullname="Fred Flinstone", password="blah")])
s.commit()

app = Sanic(__name__)


@app.route("/users", methods=["GET"])
async def all_users(request):
    users = list(map(lambda u: u.serialize(), s.query(User).all()))
    return json(users)


@app.route("/user", methods=["POST"])
async def new_user(request):
    try:
        s.add(User(**request.json))
        return json({"success": True})
    except Exception as e:
        return json({"success": False})


@app.route("/users/<user_id:int>", methods=["GET"])
async def user(request, user_id):
    try:
        return json(s.query(User).filter_by(id=user_id)[0].serialize())
    except IndexError:
        raise NotFound("no user found with id: " + str(user_id))


@app.exception(NotFound)
async def not_found(request, exception):
    return json({"type": type(exception).__name__, "message": str(exception)})


app.run(host="0.0.0.0", port=8000)
