import google.generativeai as genai
from bot.config import GEMINI_API_KEY
from bot.utils import run_blocking_io

genai.configure(api_key=GEMINI_API_KEY)

def _sync_get_gemini_response(user_question: str) -> str:
    model = genai.GenerativeModel('gemini-2.5-flash')
    system_prompt = (
        "You are a senior DevOps engineer assisting developers with DevOps, "
        "cloud, and software engineering questions. Provide concise, accurate answers using best practices."
    )
    prompt = f"{system_prompt}\nUser: {user_question.strip()}"
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if not text:
            return "Sorry, I couldn't generate a response. Please try rephrasing your question."
        return text
    except Exception as e:
        print(f"[llm_client] Error fetching Gemini response: {e}")
        return "Sorry, I encountered an internal error while processing your request. Please try again later."

def _sync_get_gemini_file_response(prompt: str) -> str:
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if not text:
            return "Sorry, no content was generated."
        return text
    except Exception as e:
        print(f"[llm_client] Error fetching Gemini file response: {e}")
        return "Sorry, I encountered an error generating your file."

async def get_gemini_response(user_question: str) -> str:
    return await run_blocking_io(_sync_get_gemini_response, user_question)

async def get_gemini_file_response(prompt: str) -> str:
    return await run_blocking_io(_sync_get_gemini_file_response, prompt)
