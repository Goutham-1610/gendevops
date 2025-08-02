import re
import io
import discord
from typing import Optional
from bot.config import (
    DISCORD_TOKEN,
    TARGET_CHANNEL_NAMES,
    DOCKER_K8S_CHANNEL_NAME,
    TARGET_CHANNEL_NAME,
    CI_CD_CHANNEL_NAME,
)
from bot.llm_client import get_gemini_response, get_gemini_file_response
from bot.generator import handle_generator_request
from bot.cicd_generator import handle_cicd_request

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

MAX_DISCORD_MSG_LEN = 2000

# In-memory sessions for ChatOps: user_id -> session dict
user_sessions = {}

# Helper function to send multi-file output from Gemini nicely split
async def send_separate_generated_files(channel: discord.abc.Messageable, user_id: int, full_output: str):
    dockerfile_match = re.search(r"###\s*Dockerfile\s*\n(.*?)(?=\n###|$)", full_output, re.DOTALL | re.IGNORECASE)
    k8s_match = re.search(r"###\s*Kubernetes manifest\s*\n(.*?)(?=\n###|$)", full_output, re.DOTALL | re.IGNORECASE)
    cicd_match = re.search(r"###\s*CI/CD pipeline\s*\n(.*?)(?=\n###|$)", full_output, re.DOTALL | re.IGNORECASE)

    files_to_send = []

    if dockerfile_match:
        dockerfile_content = dockerfile_match.group(1).strip()
        files_to_send.append(discord.File(io.BytesIO(dockerfile_content.encode("utf-8")), filename="Dockerfile"))
    if k8s_match:
        k8s_content = k8s_match.group(1).strip()
        files_to_send.append(discord.File(io.BytesIO(k8s_content.encode("utf-8")), filename="kubernetes.yaml"))
    if cicd_match:
        cicd_content = cicd_match.group(1).strip()
        files_to_send.append(discord.File(io.BytesIO(cicd_content.encode("utf-8")), filename="ci.yml"))

    if files_to_send:
        await channel.send(
            content=f"<@{user_id}> Here are your generated files:",
            files=files_to_send
        )
    else:
        # Fallback: Send entire content as one text file if no split
        await channel.send(
            f"<@{user_id}> I couldn't detect separate files, sending all content in one file.",
            file=discord.File(io.BytesIO(full_output.encode("utf-8")), filename="generated_files.txt")
        )


async def ask_question(channel: discord.abc.Messageable, user_id: int):
    session = user_sessions[user_id]
    stage = session.get('stage', 1)
    
    if stage == 1:
        await channel.send(f"<@{user_id}> What framework are you using? (e.g., Flask, FastAPI, Node.js)")
    elif stage == 2:
        await channel.send(f"<@{user_id}> Do you want HTTPS Ingress or only internal service?")
    elif stage == 3:
        await channel.send(
            f"<@{user_id}> Which CI/CD platform do you want: GitHub Actions, Jenkins, GitLab, or None?"
        )
    elif stage == 4:
        summary = (
            f"Framework: {session.get('framework')}\n"
            f"HTTPS Ingress: {session.get('https')}\n"
            f"CI/CD platform: {session.get('cicd')}\n"
            "Type 'yes' to generate the files or 'no' to cancel."
        )
        await channel.send(f"<@{user_id}> Please confirm your choices:\n{summary}")

@client.event
async def on_ready() -> None:
    print(f"[DiscordBot] Connected as {client.user}. Ready to handle messages.")

@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.strip()
    content_lower = content.lower()
    channel = message.channel
    channel_name: Optional[str] = getattr(channel, "name", None)

    # --- ChatOps multi-step session management ---
    if (
        content_lower.startswith("!deploy")
        or content_lower.startswith("/start")
        or user_id in user_sessions
    ):
        # Starting new session
        if content_lower.startswith("!deploy") or content_lower.startswith("/start"):
            user_sessions[user_id] = {"stage": 1}
            await ask_question(channel, user_id)
            return

        # Existing session continuation
        session = user_sessions[user_id]
        stage = session.get("stage", 1)

        if stage == 1:
            session["framework"] = content
            session["stage"] = 2
            await ask_question(channel, user_id)

        elif stage == 2:
            if "https" in content_lower or "ingress" in content_lower:
                session["https"] = True
            else:
                session["https"] = False
            session["stage"] = 3
            await ask_question(channel, user_id)

        elif stage == 3:
            cicd_options = ["github actions", "jenkins", "gitlab", "none"]
            user_choice = content_lower.strip()

            if user_choice in cicd_options:
                session["cicd"] = user_choice
                session["stage"] = 4
                await ask_question(channel, user_id)
            else:
                matches = [opt for opt in cicd_options if user_choice in opt or opt in user_choice]
                if len(matches) == 1:
                    session["cicd"] = matches[0]
                    session["stage"] = 4
                    await ask_question(channel, user_id)
                else:
                    await channel.send(
                        f"'{content}' is not a recognized CI/CD platform.\n"
                        "Please choose one of: GitHub Actions, Jenkins, GitLab, or None."
                    )
            return

        elif stage == 4:
            if content_lower in ["yes", "y"]:
                await channel.send(f"<@{user_id}> Generating files based on your inputs...")

                prompt = (
                    f"You are a senior DevOps engineer. "
                    f"Generate three distinct files for a {session['framework']} application:\n\n"
                    f"### Dockerfile\n"
                    f"Production-ready Dockerfile including multi-stage build, proper user, ports, and comments.\n\n"
                    f"### Kubernetes manifest\n"
                    f"Best-practice deployment, service, and {'HTTPS Ingress' if session['https'] else 'internal service only'} configuration.\n\n"
                    f"### CI/CD pipeline\n"
                    f"{session['cicd']} CI/CD YAML for build, test, docker push, and deployment.\n\n"
                    f"Label each section clearly as above."
                )

                try:
                    file_contents = await get_gemini_file_response(prompt)
                    await send_separate_generated_files(channel, user_id, file_contents)
                except Exception as e:
                    await channel.send(f"<@{user_id}> Error generating files: {e}")

                del user_sessions[user_id]

            else:
                await channel.send(f"<@{user_id}> Session cancelled.")
                del user_sessions[user_id]

        return  # ChatOps has exclusive control here

    # --- Channel-specific command handlers ---

    if channel_name not in TARGET_CHANNEL_NAMES:
        return  # Ignore messages outside target channels

    try:
        if channel_name == TARGET_CHANNEL_NAME:
            if not content:
                return
            print(f"[Chatbot] Processing message from {message.author}: {content}")
            response_text = await get_gemini_response(content)
            if len(response_text) > MAX_DISCORD_MSG_LEN:
                await channel.send(
                    "Response was too long for chat. See attached file for the full answer.",
                    file=discord.File(io.BytesIO(response_text.encode("utf-8")), filename="response.txt"),
                )
            else:
                await channel.send(response_text)

        elif channel_name == DOCKER_K8S_CHANNEL_NAME:
            print(f"[Generator] Processing message from {message.author}: {content}")
            await handle_generator_request(message)

        elif channel_name == CI_CD_CHANNEL_NAME:
            print(f"[CI/CD] Processing message from {message.author}: {content}")
            await handle_cicd_request(message)

    except discord.HTTPException as http_err:
        print(f"[Discord HTTP Exception] {http_err}")
        try:
            await channel.send("Sorry, there was an issue sending the response to the channel.")
        except Exception:
            pass
    except Exception as e:
        print(f"[Error in on_message] {e}")
        try:
            await channel.send("Sorry, an unexpected error occurred while processing your request.")
        except Exception:
            pass

def run() -> None:
    client.run(DISCORD_TOKEN)
