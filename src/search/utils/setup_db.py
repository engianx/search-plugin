"""Setup script for MongoDB database and collections."""
import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

from search.utils.config import load_config

logger = logging.getLogger(__name__)

project_config = load_config()

# Default MongoDB configuration
DEFAULT_CONFIG = {
    'database': project_config['mongodb']['database'],
    'collections': {
        'embeddings_cache': 'embeddings_cache'
    },
    'cache': {
        'max_age_days': 30,
        'index_fields': [
            'text_hash',
            'model',
            'created_at'
        ]
    }
}

def setup_database(uri: str = None, config: dict = None) -> bool:
    """Initialize MongoDB database and collections.

    Args:
        uri: MongoDB connection URI (optional)
        config: Configuration dictionary (optional)

    Returns:
        bool: True if setup successful
    """
    try:
        # Use provided config or default
        config = config or DEFAULT_CONFIG

        # Use provided URI or default
        site_config = load_config()
        uri = uri or site_config['mongodb']['uri']
        client = MongoClient(uri)

        # Get database
        db = client[config['database']]
        logger.info(f"Connected to database: {config['database']}")

        # Setup embeddings cache collection
        cache_collection = db[config['collections']['embeddings_cache']]

        # Create search
        cache_collection.create_index(
            [("text_hash", ASCENDING), ("model", ASCENDING)],
            unique=True,
            background=True
        )
        cache_collection.create_index(
            "created_at",
            background=True,
            expireAfterSeconds=config['cache']['max_age_days'] * 24 * 60 * 60
        )

        for field in config['cache']['index_fields']:
            if field not in ['text_hash', 'model', 'created_at']:  # Skip already created
                cache_collection.create_index(field, background=True)

        logger.info(f"Setup complete for collection: {config['collections']['embeddings_cache']}")
        return True

    except PyMongoError as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False
    finally:
        client.close()

def main():
    """Main entry point for database setup."""
    logging.basicConfig(level=logging.INFO)

    success = setup_database()
    if success:
        logger.info("Database setup completed successfully")
    else:
        logger.error("Database setup failed")
        exit(1)

if __name__ == '__main__':
    main()