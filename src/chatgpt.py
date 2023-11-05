import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
API_KEY = os.getenv("API_KEY")

import openai

openai.api_key = API_KEY

# user_input = input("Prompt: ")

# completion = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",
#     messages=[{"role":"user", "content": user_input}]
# )

def request_playlist_name(playlist):

    message = "Come up with a playlist name for a playlist with the following songs: " + playlist

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user", "content": message}]
    )

    reply_content = completion.choices[0].message.content
    token_usage = completion.usage.total_tokens

    print("Total Tokens: " + str(token_usage))

    return reply_content

# token_usage = completion.usage.total_tokens

# print("GPT 3.5 Response: \n" + reply_content)
# print("Total Tokens" + str(token_usage))