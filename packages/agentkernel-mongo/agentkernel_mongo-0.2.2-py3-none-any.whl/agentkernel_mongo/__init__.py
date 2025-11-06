def get_session_store_factory():
    """
    Factory for the agentkernel Runtime session store.
    
    This function is called by agentkernel's Runtime and return a *callable* that, when called,
    creates the session store instance.
    """
    from .store import MongoSessionStore, MongoDriver
    
    # We return a lambda so creation is deferred until Runtime needs it.
    return lambda: MongoSessionStore(MongoDriver())

def get_config_model():
    """
    Factory for the agentkernel Config session store.
    Returns the Pydantic config model class that agentkernel's config.py expects.
    """
    from .config import _MongoConfig
    
    return _MongoConfig