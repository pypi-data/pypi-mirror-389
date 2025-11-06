import logging
import pickle
import traceback
from typing import Any, Optional
from datetime import datetime, timezone

import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from .config import _MongoConfig

# --- CRITICAL ---
# Import base classes and config from the *core* agentkernel package
try:
    from agentkernel.core.sessions.base import SessionStore
    from agentkernel.core.base import Session
    from agentkernel.core.config import AKConfig
except ImportError:
    # Handle error if agentkernel isn't installed
    logging.critical("agentkernel core package not found. Please install agentkernel.")
    raise


#
# ... PASTE YOUR FULL MongoDriver CLASS HERE ...
#
class MongoDriver:
    _mongo_client = None
    _mongo_db = None
    _mongo_collection = None

    def __init__(self):
        self._log = logging.getLogger("ak.core.sessions.mongo.util")

        # plugin gets its config from the main app
        try:
            config = AKConfig.get().session.mongo
        except AttributeError:
            self._log.error("Failed to load 'mongo' config. Is `type: mongo` set in your config?")
            # Fallback to default config object
            config = _MongoConfig()

        self._url = config.url
        self._database_name = config.database
        self._collection_name = config.collection
        self._ttl = int(config.ttl)

    # ... (rest of MongoDriver implementation) ...
    @property
    def collection(self) -> pymongo.collection.Collection:
        if self._mongo_collection is None:
            self._connect()
        return self._mongo_collection

    @property
    def ttl(self) -> int:
        return self._ttl

    def _connect(self):
        try:
            self._log.debug(f"Connecting to MongoDB at {self._url}")
            client = pymongo.MongoClient(
                self._url,
                serverSelectionTimeoutMS=5000
            )
            client.admin.command('ping')
            self._log.debug("MongoDB connection successful")

            self._mongo_client = client
            self._mongo_db = self._mongo_client[self._database_name]
            self._mongo_collection = self._mongo_db[self._collection_name]

            self._ensure_ttl_index()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self._log.error(f"Failed to connect to MongoDB: {e}")
            self._log.error(traceback.format_exc())
            raise

    def _ensure_ttl_index(self):
        if self._ttl <= 0:
            self._log.debug("TTL is 0, skipping TTL index creation.")
            return

        index_name = "session_ttl_index"
        indexes = self.collection.index_information()

        if index_name in indexes:
            existing_ttl = indexes[index_name].get('expireAfterSeconds')
            if existing_ttl == self._ttl:
                self._log.debug(f"TTL index '{index_name}' already exists with correct TTL.")
                return
            else:
                self._log.warning(f"TTL index '{index_name}' has incorrect TTL. Recreating.")
                self.collection.drop_index(index_name)

        self._log.info(f"Creating TTL index '{index_name}' on 'last_updated' with {self._ttl}s expiry.")
        self.collection.create_index(
            "last_updated",
            name=index_name,
            expireAfterSeconds=self._ttl
        )

    def get_document(self, session_id: str) -> Optional[dict]:
        self._log.debug(f"GET document {session_id}")
        return self.collection.find_one({"_id": session_id})

    def replace(self, session_id: str, document: dict) -> None:
        document["last_updated"] = datetime.now(timezone.utc)
        self._log.debug(f"REPLACE document {session_id}")
        document["_id"] = session_id
        self.collection.replace_one(
            {"_id": session_id},
            document,
            upsert=True
        )

    def exists(self, session_id: str) -> bool:
        try:
            return self.collection.count_documents({"_id": session_id}) > 0
        except pymongo.errors.PyMongoError:
            return False

    def clear_all(self) -> None:
        self._log.info(f"Clearing all sessions from collection {self._collection_name}")
        self.collection.delete_many({})


#
# ... PASTE YOUR FULL MongoSessionStore CLASS HERE ...
#
class MongoSessionStore(SessionStore):
    def __init__(
            self,
            driver: MongoDriver
    ):
        self._log = logging.getLogger("ak.core.sessions.mongo")
        self._serde = MongoSessionSerde()
        self._driver = driver

    # ... (load, new, clear, store methods) ...
    def load(self, session_id: str, strict: bool = False) -> Session:
        self._log.debug(f"Loading mongo session with ID {session_id}")
        document = self._driver.get_document(session_id)
        if document:
            session = Session(session_id)
            for field, value in document.items():
                if field in ["_id", "last_updated", "__init__"]:
                    continue
                session.set(field, self._serde.loads(value))
            return session
        else:
            if strict:
                raise KeyError(f"Session {session_id} not found")
            self._log.warning(f"Session {session_id} not found, creating new session")
            return self.new(session_id)

    def new(self, session_id: str) -> Session:
        self._log.debug(f"Creating new mongo session with ID {session_id} ")
        minimal_doc = {
            "__init__": self._serde.dumps(True)
        }
        self._driver.replace(session_id, minimal_doc)
        return Session(session_id)

    def clear(self) -> None:
        self._driver.clear_all()

    def store(self, session: Session) -> None:
        self._log.debug(f"Storing session {session.id}")
        document_to_store = {}
        keys = list(session.get_all_keys())
        for key in keys:
            value = session.get(key)
            document_to_store[key] = self._serde.dumps(value)
        if not keys:
            document_to_store["__init__"] = self._serde.dumps(True)
        self._driver.replace(session.id, document_to_store)


#
# ... PASTE YOUR FULL MongoSessionSerde CLASS HERE ...
#
class MongoSessionSerde:
    _log = logging.getLogger("ak.core.sessions.mongoserde")

    @classmethod
    def dumps(cls, obj: Any) -> bytes:
        cls._log.debug(f"dumped: {obj}")
        return pickle.dumps(obj)

    @classmethod
    def loads(cls, payload: bytes) -> Any:
        cls._log.debug(f"loads: {type(payload)}")
        if payload is None:
            return None
        loaded = pickle.loads(payload)
        cls._log.debug(f"loaded: {loaded}")
        return loaded