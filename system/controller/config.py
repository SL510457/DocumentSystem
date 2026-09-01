class Config:
    # DEBUG / SEED_DUMMY_DATA are read from the environment in create_app(),
    # after load_dotenv() has run -- a value hardcoded here would win over the
    # env var and silently re-enable the debugger in production.
    DATABASE_URI = 'your_database_uri'

    # API setup
    APP_HOST = '0.0.0.0'
    APP_PORT = 5000

    # Redis
    REDIS_HOST = '0.0.0.0'
    REDIS_PORT = 6379