import discord
import io
from bot.llm_client import get_gemini_file_response

async def handle_cicd_request(message: discord.Message):
    """
    Handle CI/CD pipeline YAML generation requests in ci-cd-pipelines channel.
    """
    content = message.content.strip()
    lowered = content.lower()

    if "jenkins" in lowered:
        pipeline_type = "Jenkins pipeline"
        filename = "Jenkinsfile"
        description = "a Jenkins pipeline script"
    elif "gitlab" in lowered:
        pipeline_type = "GitLab CI pipeline"
        filename = ".gitlab-ci.yml"
        description = "a GitLab CI YAML pipeline configuration"
    else:
        pipeline_type = "GitHub Actions workflow"
        filename = "ci.yml"
        description = "a GitHub Actions workflow YAML file"

    prompt_lines = [
        "You are a senior DevOps engineer.",
        f"Generate {description} based on the user's request below.",
        "Include best practices, caching, testing, building, and deployment steps.",
        "Add comments to explain each stage and step.",
        f"User's request: {content}",
    ]
    prompt = "\n".join(prompt_lines).strip()

    await message.channel.send(f"Generating {pipeline_type} for you. Please wait...")

    try:
        file_content = await get_gemini_file_response(prompt)
        if not file_content or "Sorry" in file_content[:10]:
            await message.channel.send("Sorry, I could not generate the pipeline file. Please provide more details or try rephrasing.")
            return

        discord_file = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)
        await message.channel.send(f"Here is your generated {pipeline_type}:", file=discord_file)

    except Exception as e:
        await message.channel.send("Sorry, an error occurred while generating your pipeline file.")
        print(f"[cicd_generator] Error in handle_cicd_request: {e}")
