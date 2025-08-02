import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TARGET_CHANNEL_NAMES = ["chatbot", "docker-k8s-generator", "ci-cd-pipelines"]

TARGET_CHANNEL_NAME = "chatbot"
DOCKER_K8S_CHANNEL_NAME = "docker-k8s-generator"
CI_CD_CHANNEL_NAME = "ci-cd-pipelines"

def get_all_target_channels():
    return TARGET_CHANNEL_NAMES

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in environment variables")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables")
