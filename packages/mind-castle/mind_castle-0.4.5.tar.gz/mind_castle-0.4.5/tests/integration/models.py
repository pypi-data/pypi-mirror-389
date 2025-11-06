from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

from mind_castle.sqlalchemy_type import SecretData


class Base(DeclarativeBase):
    pass


class SimpleNoneModel(Base):
    __tablename__ = "testnonemodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("none"))


class SimpleMemoryModel(Base):
    __tablename__ = "testmemorymodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("memory"))


class SimpleJsonModel(Base):
    __tablename__ = "testjsonmodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("json"))


class SimpleAWSSecretsManagerModel(Base):
    __tablename__ = "testawssecretsmanagermodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("awssecretsmanager"))


class SimpleAWSKMSModel(Base):
    __tablename__ = "testawskmsmodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("awskms"))


class SimpleLocalEncryptionModel(Base):
    __tablename__ = "testlocalmodel"
    id = Column(Integer, primary_key=True)
    data = Column(SecretData("localencryption"))
