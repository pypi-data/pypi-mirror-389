import logging
import wrapt
import copy

from sqlalchemy import types


from mind_castle.secret_store_base import MindCastleSecret
from mind_castle.stores import (
    create_secret,
    retrieve_secret,
)

logger = logging.getLogger(__name__)


# TODO: for remote stores
#
# @event.listens_for(Mapper, "mapper_configured")
# def _register_secret_set_event(mapper, class_):
#     """Automatically register an attribute setter function on SecretData columns"""
#     for prop in mapper.iterate_properties:
#         col = getattr(prop, "columns", [None])[0]
#         if col is not None and isinstance(col.type, SecretData):
#             # prop.key is the attribute name, e.g. "api_key" or "data"
#             attr = getattr(class_, prop.key)
#             event.listen(attr, "set", _receive_secret_set, retval=True)


class MindCastleProxy(wrapt.ObjectProxy):
    """
    Wraps any Python value + its secret details.
    """

    def __init__(self, secret_value, secret_details):
        super(MindCastleProxy, self).__init__(secret_value)
        self._self_secret_details = secret_details

    def __deepcopy__(self, memo):
        return MindCastleProxy(
            copy.deepcopy(self.__wrapped__), self._self_secret_details
        )


class SecretData(types.TypeDecorator):
    impl = types.JSON
    cache_ok = True

    def __init__(self, store_type: str, secret_key_prefix: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_type = store_type
        self.secret_key_prefix = secret_key_prefix

    # Mutate/encrypt a value for storage in the DB
    def process_bind_param(self, value, dialect):
        if value is None:
            # Don't waste our time encrypting None
            return None
        if self.secret_type == "none":
            return value
        if isinstance(value, MindCastleProxy):
            # This value is a secret previously stored in the DB.
            # We can just return the secret details already calculated
            return value._self_secret_details.model_dump(mode="json")

        # Default: create a new secret from the value
        return create_secret(value, self.secret_type).model_dump(mode="json")

    # Decrypt a value after retrieval from the DB
    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if not isinstance(value, dict) or value.get("mind_castle_secret_type") is None:
            # This isn't a mind castle secret, so treat it like a raw value
            logger.warning("Got a plaintext value from the DB - returning it as-is")
            return value

        # Default: load the json data into a MindCastleSecret, then retrieve the plaintext
        secret = MindCastleSecret(**value)
        secret_plaintext = retrieve_secret(secret)
        return MindCastleProxy(secret_plaintext, secret)


# def _receive_secret_set(target, value, oldvalue, initiator):
#     """Handle setting a new SecretData value, while maintaining existing secret info"""
#     # if the thing you’re overwriting was already a proxy,
#     # just swap out its wrapped value, keep its secret ID, and return it.

#     logger.debug(f"RECEIVE SECRET SET: {oldvalue} -> {value}")
#     logger.debug(f"{target} | {initiator}")
#     if isinstance(oldvalue, MindCastleProxy) and oldvalue != value:
#         logger.debug(f"SETTING EXISTING SECRET: {oldvalue} -> {value}")
#         oldvalue.__wrapped__ = value  # change the “plaintext”
#         flag_modified(target, initiator.key)
#         return oldvalue  # SQLAlchemy will leave the attribute as-is
#     # otherwise it’s the first time setting, so just hand back the raw value;
#     # your before_flush hook will pick it up and wrap it later.
#     return value


# @event.listens_for(Session, "before_flush")
# def _track_secret_changes(session: Session, flush_context, instances):
#     # TODO: If an error occurs here with any secret interactions, explain implications to the user
#     logger.debug("================================= BEFORE FLUSH")
#     info = session.info
#     info.setdefault("pending_new", [])
#     info.setdefault("pending_old", [])
#     info.setdefault("pending_deleted", [])

#     # Handle INSERTs and UPDATEs
#     logger.debug(f"New or dirty objects: {list(session.new) + list(session.dirty)}")
#     for obj in list(session.new) + list(session.dirty):
#         state = inspect(obj)
#         is_update = obj in session.dirty
#         logger.debug(f"is_update: {is_update}")
#         for attr in state.mapper.column_attrs:
#             logger.debug(f"attr: {attr}")
#             col = attr.columns[0]
#             if not isinstance(col.type, SecretData):
#                 logger.debug("- is not secret data")
#                 continue
#             logger.debug("- is secret data")
#             secret_type = col.type.secret_type
#             logger.debug(f"- is a {secret_type} secret")
#             hist = state.get_history(attr.key, True)
#             if not hist.has_changes():
#                 logger.debug("- does not have changes")
#                 continue

#             new_value = hist.added[0]
#             logger.debug(f"- has new value: {new_value}")
#             if is_update and isinstance(new_value, MindCastleProxy):
#                 logger.debug("- has been updated")
#                 # Ideally we would call update_secret like below:
#                 # UPDATE in place: same ID, just update payload
#                 # update_secret(new_value._self_secret_details, new_value.__wrapped__)
#                 # sid = new_value._self_secret_details

#                 # For now we're going to create a new secret here and mark the old one for deletion.
#                 # This is because we can't guarantee an update will go through if we wait till after DB commit
#                 # and we can't guarantee the DB commit will go through if we update the secret here.

#                 # Maybe in future we will support updates/secret history, but for now we create a secret with the new value here
#                 # and delete the old secret after DB commit
#                 # This is a bit out of whack with how we handle updates to sqlalchemy attrs, as there we update the secret proxy value in-place
#                 sid = create_secret(
#                     new_value.__wrapped__,
#                     new_value._self_secret_details["mind_castle_secret_type"],
#                 )
#                 info["pending_new"].append(sid)
#                 info["pending_old"].append(new_value._self_secret_details)
#             else:
#                 logger.debug("- has been created")
#                 # brand‐new secret
#                 sid = create_secret(new_value, secret_type)
#                 logger.debug(f"- created secret: {sid}")
#                 info["pending_new"].append(sid)
#                 if hist.deleted and isinstance(hist.deleted[0], MindCastleProxy):
#                     info["pending_old"].append(hist.deleted[0]._self_secret_details)

#             # wrap so that process_bind_param emits sid
#             setattr(obj, attr.key, MindCastleProxy(new_value, sid))

#     # Handle DELETEs
#     for obj in list(session.deleted):
#         state = inspect(obj)
#         for attr in state.mapper.column_attrs:
#             col = attr.columns[0]
#             if isinstance(col.type, SecretData):
#                 val = getattr(obj, attr.key)
#                 if isinstance(val, MindCastleProxy):
#                     info["pending_deleted"].append(val._self_secret_details)


# @event.listens_for(Session, "after_commit")
# def _on_commit_cleanup(session: Session):
#     logger.debug("================================= AFTER COMMIT")
#     # Only after a successful commit do we delete old/removed secrets
#     # TODO: If an error occurs here, explain implications to the user
#     for sid in session.info.get("pending_old", []):
#         delete_secret(sid)
#     for sid in session.info.get("pending_deleted", []):
#         delete_secret(sid)
#     session.info.pop("pending_new", None)
#     session.info.pop("pending_old", None)
#     session.info.pop("pending_deleted", None)


# @event.listens_for(Session, "after_rollback")
# def _on_rollback_cleanup(session: Session):
#     logger.debug("================================= AFTER rollback")
#     # If we roll back, remove any NEW secrets that never made it into the DB
#     # TODO: If an error occurs here, explain implications to the user
#     for sid in session.info.get("pending_new", []):
#         delete_secret(sid)
#     session.info.pop("pending_new", None)
#     session.info.pop("pending_old", None)
#     session.info.pop("pending_deleted", None)
