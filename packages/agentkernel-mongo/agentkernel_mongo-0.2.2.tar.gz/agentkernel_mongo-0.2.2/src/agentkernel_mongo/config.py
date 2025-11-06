from pydantic import BaseModel, Field

class _MongoConfig(BaseModel):
    """
    MongoDB session storage configuration.
    """
    url: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URL."
    )
    database: str = Field(
        default="agent_sessions",
        description="The name of the database to use for sessions."
    )
    collection: str = Field(
        default="sessions",
        description="The name of the collection to store session documents."
    )
    ttl: int = Field(
        default=604800,
        description="Session TTL in seconds. MongoDB's TTL index will purge documents after this duration."
    )