from sqlalchemy import Column, Integer, VARCHAR, String
from referenceframe.database import Base

class Asset(Base):
	__tablename__ = 'assets'
	id = Column(Integer, primary_key = True)
	type = Column(VARCHAR(64))
	filename = Column(VARCHAR(64))

class Tag(Base):
	__tablename__ = 'tags'
	id = Column(Integer, primary_key = True)
	value = Column(VARCHAR(64), unique=True)
