# generative-ai-devops-assistant

## Overview
This project is a Python-based Discord bot designed to assist with DevOps tasks using a large language model (LLM) like Gemini Pro. The bot interacts with users on Discord and provides helpful responses based on the tasks and queries related to DevOps.

## Project Structure
```
generative-ai-devops-assistant
├── bot
│   ├── __init__.py
│   ├── discord_bot.py
│   ├── llm_client.py
│   ├── config.py
│   └── utils.py
├── tests
│   ├── test_llm_client.py
│   └── test_discord_bot.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run_bot.py
```

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/generative-ai-devops-assistant.git
   cd generative-ai-devops-assistant
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your API keys and bot token:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token
   LLM_API_KEY=your_llm_api_key
   ```

### Running the Bot
To start the bot, run the following command:
```
python run_bot.py
```

### Testing
To run the tests, use the following command:
```
pytest tests/
```

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.