import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required tokens and credentials
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Channel name constants—these are used both for display and channel lookup.
CHATBOT_CHANNEL = "chatbot"
DOCKER_K8S_CHANNEL = "docker-k8s-generator"
CI_CD_CHANNEL = "ci-cd-pipelines"

# Aliases for compatibility with other files (import/export)
DOCKER_K8S_CHANNEL_NAME = DOCKER_K8S_CHANNEL
TARGET_CHANNEL_NAME = CHATBOT_CHANNEL
CI_CD_CHANNEL_NAME = CI_CD_CHANNEL

# All target channels list
TARGET_CHANNEL_NAMES = [CHATBOT_CHANNEL, DOCKER_K8S_CHANNEL, CI_CD_CHANNEL]

def get_all_target_channels():
    """Returns the list of all target channel names."""
    return TARGET_CHANNEL_NAMES

def validate_required_env_vars():
    """Ensures all required environment variables are set, or raises ValueError."""
    missing_vars = []
    if not DISCORD_TOKEN:
        missing_vars.append("DISCORD_TOKEN")
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
    if not GITHUB_TOKEN:
        missing_vars.append("GITHUB_TOKEN")
    if missing_vars:
        raise ValueError(f"The following environment variables are missing or empty: {', '.join(missing_vars)}")

# Validate required variables at import
validate_required_env_vars()
