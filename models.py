from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)
    password = Column(String)
    type = Column(Integer)

    def __repr__(self):
        return "<User(name='%s', username='%s', password='%s', type='%d')>" % (
                         self.name, self.fullname, self.password, self.type)


class Report(Base):
    __tablename__ = 'report'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    system_name = Column(String)
    status = Column(String)
    bugs = Column(String)
    updated_time = Column(Integer)
