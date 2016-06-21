from sqlalchemy import Column, Integer, String, DateTime, create_engine, MetaData, Table
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
    updated_time = Column(DateTime)


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    completed = Column(String)
    uncompleted = Column(String)
    coordination = Column(String)
    updated_time = Column(DateTime)


if __name__ == "__main__":
    engine = create_engine('mysql://root:333666@123.57.58.91/dailytask')
    metadata = MetaData(engine)
    task_table = Table("task", metadata,
                       Column('id', Integer, primary_key=True),
                       Column('user_id', Integer),
                       Column('completed', String(500)),
                       Column('uncompleted', String(500)),
                       Column('coordination', String(500)),
                       Column('updated_time', DateTime))
    task_table.create()
