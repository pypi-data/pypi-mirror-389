from .store import MongoSessionStore, MongoDriver
from .config import _MongoConfig

def get_session_store_factory():
    """
    Returns a callable factory for creating the session store.
    
    This function is called by agentkernel's Runtime (via entry points)
    and should return a *callable* (like a lambda) that, when called,
    creates the session store instance.
    """
    # We return a lambda so creation is deferred until Runtime needs it.
    return lambda: MongoSessionStore(MongoDriver())

def get_config_model():
    """
    Returns the Pydantic config model class.
    
    This function is called by agentkernel's Config (via entry points)
    and should return the *class* itself, not an instance.
    """
    return _MongoConfig