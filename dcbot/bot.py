#!/usr/bin/env python3
import os
import sys
import json
from discord import app_commands
import discord
from dotenv import load_dotenv
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.EdgeGPT import Chatbot, ConversationStyle
from src.ImageGen import ImageGen


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')
MY_GUILD = discord.Object(id=SERVER_ID)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


gptbot = Chatbot(cookiePath='cookies.json')


@client.tree.command()
async def ask(interaction: discord.Interaction, prompt: str):
    """Ask BingGPT a question"""
    await interaction.response.defer(thinking=True)
    try:
        res =  (
            (await gptbot.ask(prompt=prompt, conversation_style=ConversationStyle.balanced))["item"][
                "messages"
            ][1]["adaptiveCards"][0]["body"][0]["text"],
        )
    except Exception as e:
        await interaction.followup.send("Error: " + str(e))
    if len(res[0]) < 1950:
        await interaction.followup.send('`' + 'Prompt: ' + prompt + '`\n' + res[0], suppress_embeds=True)
    else:
        await interaction.followup.send('`' + 'Prompt: ' + prompt + '`\n' + res[0][:1950], suppress_embeds=True)
        await interaction.followup.send(res[0][1950:], suppress_embeds=True, )


@client.tree.command()
async def imagine(interaction: discord.Interaction, prompt: str):
    """Ask BingGPT to imagine visuals"""
    await interaction.response.defer(thinking=True)
    with open('cookies.json', encoding="utf-8") as file:
        cookie_json = json.load(file)
        for cookie in cookie_json:
            if cookie.get("name") == "_U":
                auth_cookie = cookie.get("value")
                break
    try:
        images = ImageGen(auth_cookie=auth_cookie).get_images(prompt)
    except Exception as e:
        await interaction.followup.send("Error: " + str(e))
    images = '\n'.join(images)
    await interaction.followup.send('`' + 'Prompt: ' + prompt + '`\n' + images)


@ask.error
async def ask_error(interaction: discord.Interaction, error):
    await interaction.response.send_message("Error: " + str(error))


@imagine.error
async def imagine_error(interaction: discord.Interaction, error):
    await interaction.response.send_message("Error: " + str(error))


@client.tree.command()
async def reset(interaction: discord.Interaction):
    """Reset the conversation"""
    await gptbot.reset()
    await interaction.response.send_message("Alfred conversation has been reset")


@client.tree.command()
async def hardreset(interaction: discord.Interaction):
    """Reset the session"""
    global gptbot
    await gptbot.close()   
    gptbot = Chatbot(cookiePath='cookies.json')
    await interaction.response.send_message("Alfred session reloaded")


client.run(TOKEN)