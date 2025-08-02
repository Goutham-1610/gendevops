import re
import io
import os
import zipfile
import discord
import aiohttp
from bot.llm_client import get_gemini_file_response

def detect_repo_type_from_files(file_list):
    """
    Basic heuristic detection for repo type based on presence of key files.
    Returns a string describing the repo type for prompt customization.
    """
    files_lower = [f.lower() for f in file_list]
    if any('mkdocs.yml' in f or f.startswith('docs/') for f in files_lower):
        return 'documentation project (e.g., MkDocs)'
    if 'requirements.txt' in files_lower:
        # Could enhance by reading requirements.txt contents for fastapi/flask, etc.
        # For now, just generic Python app
        return 'Python web application'
    if 'package.json' in files_lower:
        return 'Node.js application'
    return 'unspecified application'

async def handle_generator_request(message: discord.Message):
    """
    Handle Dockerfile and Kubernetes manifest generation from GitHub repo URL or zip file upload.
    Sends two files: Dockerfile and kubernetes.yaml.
    """

    content = message.content.strip()
    files_to_send = []

    def cleanup_extracted_folder(path: str):
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    # Detect GitHub repo URL in message text
    match = re.search(r'https?://github\.com/[^\s]+', content)
    repo_url = match.group() if match else None

    # Detect .zip attachment
    zip_attachment = None
    for attachment in message.attachments:
        if attachment.filename.lower().endswith('.zip'):
            zip_attachment = attachment
            break

    if repo_url:
        prompt = f"""
You are a senior DevOps engineer.

First, analyze the given repository URL quickly to determine if it is:
- A documentation project (e.g., MkDocs, Sphinx),
- A web/API app (e.g., FastAPI, Flask, Django, Node.js),
- Or something else.

If it is documentation, generate a multi-stage Dockerfile for building static HTML with Python tools and a Kubernetes manifest to serve with NGINX.

If it is an application, generate a Dockerfile to run the app properly (e.g., using Uvicorn or Gunicorn for Python), including dependencies and environment variables, and a Kubernetes manifest with deployment, service, health probes, and resource limits.

Clearly label each generated file and include a brief comment explaining your choices at the top.

Repository URL: {repo_url}

Output the Dockerfile first, then the Kubernetes manifest, separated and labeled clearly.
""".strip()

    elif zip_attachment:
        await message.channel.send(f"Downloading and extracting uploaded zip file `{zip_attachment.filename}`. Please wait...")

        zip_file_name = f"temp_{message.id}.zip"
        extracted_folder = f"extracted_{message.id}"

        try:
            # Download the zip file
            async with aiohttp.ClientSession() as session:
                async with session.get(zip_attachment.url) as resp:
                    if resp.status != 200:
                        await message.channel.send("Failed to download the zip file. Please try again.")
                        return
                    data = await resp.read()
                    with open(zip_file_name, 'wb') as f:
                        f.write(data)

            # Extract zip and read file list for detection
            with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
                zip_ref.extractall(extracted_folder)
                file_list = zip_ref.namelist()

            repo_type_desc = detect_repo_type_from_files(file_list)

            # Summarize files (limit 100 for prompt size)
            summary = "\n".join(file_list[:100])
            if len(file_list) > 100:
                summary += f"\n...and {len(file_list) - 100} more files."

            prompt = f"""
You are a senior DevOps engineer.

A user uploaded source code with the following file/folder structure:

{summary}

Based on this, the repository appears to be a {repo_type_desc}.

Generate a production-ready Dockerfile and Kubernetes manifest:

- For documentation, use a multi-stage Dockerfile with static HTML serving in NGINX.
- For applications, use Dockerfile with app server, dependencies, and environment configs.
- In all cases, provide Kubernetes manifests with deployment, service, health probes, and resource requests/limits.

Clearly label and briefly comment each file.

Output the Dockerfile first, then the Kubernetes manifest.
""".strip()

        except Exception as e:
            await message.channel.send(f"Error processing the uploaded zip file: {e}")
            return

    else:
        await message.channel.send("Please provide a GitHub repository URL or upload a zip file of your source code containing your app.")
        return

    await message.channel.send("Generating Dockerfile and Kubernetes manifest for you. Please wait...")

    try:
        full_output = await get_gemini_file_response(prompt)
    except Exception as e:
        await message.channel.send("Sorry, an error occurred while generating your files.")
        print(f"[generator] Error calling Gemini: {e}")
        if zip_attachment:
            os.remove(zip_file_name)
            cleanup_extracted_folder(extracted_folder)
        return

    dockerfile_content = ""
    k8s_content = ""

    dockerfile_marker = re.search(r"(?:^|\n)###?\s*Dockerfile\s*(?:\n|$)", full_output, re.IGNORECASE)
    k8s_marker = re.search(r"(?:^|\n)###?\s*Kubernetes manifest\s*(?:\n|$)", full_output, re.IGNORECASE)

    if dockerfile_marker and k8s_marker:
        dockerfile_start = dockerfile_marker.end()
        k8s_start = k8s_marker.end()

        if dockerfile_start < k8s_marker.start():
            dockerfile_content = full_output[dockerfile_start:k8s_marker.start()].strip()
            k8s_content = full_output[k8s_start:].strip()
        else:
            dockerfile_content = full_output.strip()
    else:
        parts = full_output.split('---')
        if len(parts) > 1:
            dockerfile_content = parts[0].strip()
            k8s_content = '---'.join(parts[1:]).strip()
        else:
            dockerfile_content = full_output.strip()

    if dockerfile_content:
        files_to_send.append(discord.File(io.BytesIO(dockerfile_content.encode('utf-8')), filename="Dockerfile"))

    if k8s_content:
        files_to_send.append(discord.File(io.BytesIO(k8s_content.encode('utf-8')), filename="kubernetes.yaml"))

    if files_to_send:
        await message.channel.send(content="Here are the generated files:", files=files_to_send)
    else:
        await message.channel.send("Failed to parse the generated content. Please try again.")

    if zip_attachment:
        try:
            os.remove(zip_file_name)
            cleanup_extracted_folder(extracted_folder)
        except Exception as e:
            print(f"[generator] Error cleaning up temp files: {e}")
