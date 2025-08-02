
# bot/utils.py
import asyncio

async def run_blocking_io(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
def setup_logging():
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    return logger

def format_message(message):
    return f"**Message:** {message}"

# Example usage of the utility functions
logger = setup_logging()
logger.info("Utility functions loaded successfully.")