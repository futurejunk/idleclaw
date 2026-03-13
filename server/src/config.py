from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"
    log_level: str = "INFO"

    # Rate limiting (requests per minute)
    rate_limit_chat_rpm: int = 20
    rate_limit_default_rpm: int = 60
    rate_limit_ws_rpm: int = 5

    # Input validation
    max_messages_per_request: int = 50
    max_message_length: int = 10_000
    max_model_name_length: int = 64

    # Node registration
    max_nodes_per_ip: int = 3
    max_models_per_node: int = 20

    # Tools
    searxng_url: str = ""
    tool_rate_limit_rpm: int = 20  # max tool calls per minute per node

    # Admin
    admin_token: str = ""

    # Persistent metrics
    stats_file: str = "data/stats.json"

    # Content filtering (regex patterns)
    inbound_blocklist: list[str] = [
        r"<script[\s>]",
        r"javascript:",
        r"data:text/html",
    ]
    outbound_blocklist: list[str] = [
        r"<script[\s>]",
        r"javascript:",
        r"data:text/html",
    ]

    # Node probing
    probe_interval_seconds: int = 300

    # Concurrent chat limits
    max_concurrent_chat_per_ip: int = 3

    # Graceful shutdown
    shutdown_drain_timeout: int = 30


settings = Settings()
