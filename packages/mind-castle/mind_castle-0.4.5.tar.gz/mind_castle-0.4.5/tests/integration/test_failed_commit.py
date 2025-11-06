# from sqlalchemy import create_engine, event
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import OperationalError
# import json
# import pytest
# import logging

# # Required if this file runs before another that requires AWS mocking
# from moto import mock_aws  # noqa

# from mind_castle.stores import stores as stores_cache
# from models import Base, SimpleMemoryModel

# logger = logging.getLogger(__name__)
# logger.level = logging.DEBUG


# # Create an in-memory SQLite database
# engine = create_engine("sqlite://", echo=True)
# Base.metadata.create_all(engine)


# # Simulate a DB-offline error on commit
# def simulate_db_offline(session, flush_context):
#     raise OperationalError("Simulated DB offline", params=None, orig=None)


# def test_failed_commit_create():
#     """
#     Tests that if there is an error on DB commit after creating a secret,
#     that the new secret is deleted
#     """

#     session = Session(engine)
#     event.listen(session, "after_flush", simulate_db_offline)
#     test_object = SimpleMemoryModel(data="A very secret string")

#     with pytest.raises(OperationalError):
#         with session.begin():
#             session.add(test_object)
#             # commit is attempted when exiting this block,
#             # and on failure it’s rolled back immediately

#     # at this point the mind-castle after_rollback hook has already run
#     assert stores_cache["memory"].secrets == {}


# def test_failed_commit_update():
#     """
#     Tests that if there is an error on DB commit after updating a secret,
#     that the secret value is still the old value
#     """

#     session = Session(engine, autobegin=False)
#     test_object = SimpleMemoryModel(data="A very secret string")
#     with session.begin():
#         session.add(test_object)
#     logger.debug(f"Added secret: {stores_cache['memory'].secrets}")

#     assert json.dumps("A very secret string") in list(
#         stores_cache["memory"].secrets.values()
#     )

#     event.listen(session, "after_flush", simulate_db_offline)

#     with pytest.raises(OperationalError):
#         with session.begin():
#             test_object = session.get(SimpleMemoryModel, test_object.id)
#             test_object.data = "An updated secret string"
#             # commit is attempted when exiting this block,
#             # and on failure it’s rolled back immediately
#     logger.debug(stores_cache["memory"].secrets)
#     # at this point the mind-castle after_rollback hook has already run
#     assert json.dumps("A very secret string") in list(
#         stores_cache["memory"].secrets.values()
#     )
#     assert json.dumps("An updated secret string") not in list(
#         stores_cache["memory"].secrets.values()
#     )


# def test_failed_commit_delete():
#     """
#     Tests that if there is an error on DB commit after deleting a secret,
#     that the secret still exists
#     """

#     session = Session(engine, autobegin=False)
#     test_object = SimpleMemoryModel(data="A very secret string")
#     with session.begin():
#         session.add(test_object)
#     logger.debug(f"Added secret: {stores_cache['memory'].secrets}")

#     event.listen(session, "after_flush", simulate_db_offline)

#     assert json.dumps("A very secret string") in list(
#         stores_cache["memory"].secrets.values()
#     )

#     with pytest.raises(OperationalError):
#         with session.begin():
#             test_object = session.get(SimpleMemoryModel, test_object.id)
#             session.delete(test_object)
#             # commit is attempted when exiting this block,
#             # and on failure it’s rolled back immediately

#     # at this point the mind-castle after_rollback hook has already run
#     assert json.dumps("A very secret string") in list(
#         stores_cache["memory"].secrets.values()
#     )
