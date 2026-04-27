from google import genai
from dotenv import load_dotenv
import discord
from discord import app_commands
import os
from datetime import datetime
import asyncio
import json
import sqlite3
import traceback

#super small 1 day project for personal use
#is now like 1 week project I am actually going to deploy
#AI use: dotenv, gemini api call, json stuff ai generated
# helping me figure out what libraries to use (ex sqlite for better storage than txt files, traceback for better errors in errors.db etc.)

#getting api keys
load_dotenv()
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
disc_client = os.getenv("DISCORD_TOKEN")

#default intents enuf b/c slash commands dont req
intents = discord.Intents.default()

#class for the bot
#ai generated
class disc_class(discord.Client):
    async def on_ready(self):
        print("bot")
        for guild in self.guilds:
            print(guild.name)

    def __init__(self):
        #initializes command tree
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    #actually sets it up
    async def setup_hook(self):
        await self.tree.sync()

bot = disc_class()

#stuff to make blacklisting work
blacklist = []
#checks if a uid is in blacklist (txt file)
def is_blacklisted(uid):
    with sqlite3.connect("blacklist.db") as conn:
        isBlacklisted = conn.execute("SELECT user FROM blacklisted WHERE uid = ?", (uid,)).fetchone()
    if isBlacklisted:
        return True
    else:
        return False
def blacklist_uid(uid, user):
    with sqlite3.connect("blacklist.db") as conn:
        conn.execute("INSERT OR IGNORE INTO blacklisted (uid, user) VALUES (?,?)", (uid, user))
    print(f"blacklisted uid: {uid}")
def unblacklist_uid(uid):
    with sqlite3.connect("blacklist.db") as conn:
        conn.execute("DELETE FROM blacklisted where uid = ?", (uid,))
    print(f"unblacklisted uid {uid}")

#parses lines in logs and turns them into an easily accessible dictionary
def parse_log_line(line):
    parts = line.split(" || ")
    result = {}
    for part in parts:
        if ": " in part:
            key, value = part.split(": ", 1)
            result[key.strip()] = value.strip()
    return result

#inserts stuff to appropriate db
def insert_to_db(dbName, table, command, input, output, user):
    with sqlite3.connect(dbName) as conn:
        #f string for table is ok
        conn.execute(f"INSERT INTO {table} (command, input, output, user) VALUES (?,?,?,?)",
                    (command, input, output, str(user))
                     )

#commands that dont require gemini api
#connect to sqlite l8r
#perms n setup stuff
@bot.tree.command(name="ryoshify", description="Ryoshify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def ryoshify(interaction: discord.Interaction, text: str):

    #stops blacklisted people
    user = interaction.user
    if is_blacklisted(user.id):
        await interaction.response.send_message("Y.A.B.")
        return

    try:
        #turns text into acronyms
        words = text.split(" ")
        string = ""
        for word in words:
            string += word[0].upper() + "."

        message = string
        #adds info to log
        #ryoshify table isn't in function b/c the table lacks a "command" column and hard writing it is simply easier
        with sqlite3.connect("bot.db") as conn:
            #1st used by sinclair translator to reverse ryoshify, 2nd general logs
            conn.execute("INSERT INTO ryoshify (timestamp, input, output, user) VALUES (?,?,?,?)",
                         (str(datetime.now()), text, message, str(user)))
        insert_to_db("bot.db", "logs", "Ryoshify", text, message, user)

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I.A.B."
        e_details = traceback.format_exc()

        #adds error info to log
        insert_to_db("errors.db", "errors", "Ryoshify", text, str(e_details), str(user))

    #sends the message
    await interaction.response.send_message(message)

#connect to sqlite l8r
#perms n setup stuff
@bot.tree.command(name="sinclair_translator", description="Translate ryoshified text!")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def sinclair_translator(interaction: discord.Interaction, text: str):

    #stops blacklisted people
    user = interaction.user
    if is_blacklisted(user.id):
        await interaction.response.send_message("y-you're banned.")
        return

    try:
        with sqlite3.connect("bot.db") as conn:
            tuple = conn.execute("SELECT * FROM ryoshify WHERE output = ? ORDER BY id DESC LIMIT 1", (text,)).fetchone()
        if tuple:
            message = tuple[2] 
        else:
            #factual statement
            message = "Can't translate cuz I'm a pathetic useless coward"

        #insert data to db
        insert_to_db("bot.db", "logs", "sinclair_translator", text, message, user)

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I-I'm broken."
        e_details = traceback.format_exc()

        #adds error info to log
        insert_to_db("errors.db", "errors", "sinclair_translator", text, e_details, user)

    #sends the message
    await interaction.response.send_message(message)

#commands that require gemini api
prompts = {}
async def execute_command(sinner, text, interaction):
    promptInfo = prompts[sinner]
    instructions = promptInfo["Instructions"]
    examples = "Examples of char speech: "+ " | ".join(promptInfo["Examples"])
    rejection = promptInfo["Blacklisted"]

    user = interaction.user
    if is_blacklisted(user.id):
        await interaction.response.send_message(rejection)
        return
    
    #required so discord doesn't cut the bot off if takes too long
    #must be after blacklist check or blacklist cant send
    await interaction.response.defer()
    
    generalInstructions = "Do not translate examples, they are for reference only. Roughly match input length. Text in parentheses = extra instructions. Only output the translation, nothing else. Make sure to preserve noun, account for incorrect grammer/slang. DO NOT add extra nouns/context beyond what is provided. If unclear respond with 'k'. Translate this text:"
    prompt = instructions + examples + generalInstructions + text

    try:
        #next 5 lines ai generated
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
                        contents=prompt
        ))

        message = response.text
        #adds info to log
        insert_to_db("bot.db", "logs", sinner, text, message, user)
         
    except Exception as e:
        print(f"Error: {str(e)}")
        message = "Alas it appeareth that I am out of service! Tis truly a most lamentable occurence!"
        e_details = traceback.format_exc()

        #adds error info to log 
        insert_to_db("errors.db", "errors", sinner, text, message, user)

    #actually sends the message
    await interaction.followup.send(message)

#perms n setup stuff
@bot.tree.command(name="quixotify", description="Quixotify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def quixotify(interaction: discord.Interaction, text: str):
    await execute_command("Quixotify", text, interaction)

#perms n setup stuff
@bot.tree.command(name="outify", description="Outify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def outify(interaction: discord.Interaction, text: str):
    await execute_command("Outify", text, interaction)

#perms n setup stuff
@bot.tree.command(name="hongify", description="Hongify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def hongify(interaction: discord.Interaction, text: str):
    await execute_command("Hongify", text, interaction)

def init():
    global prompts
    with sqlite3.connect("bot.db") as connection:
        #creates the logs
        #INTEGER PRIMARY KEY AUTOINCREMENT assigns an id to each entry, TEXT is the input type (str int etc)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                command TEXT,
                input TEXT,
                output TEXT,
                user TEXT
            )
        """),
        #used by sinclair_translator to reverse ryoshified texts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ryoshify (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                input TEXT,
                output TEXT,
                user TEXT
            )
        """)
        #testing new ver of ryoshify and sinclair_translator
        connection.execute("""
            CREATE TABLE IF NOT EXISTS newRyoTest (
                unAbbreviated TEXT,      
                abbreviated TEXT PRIMARY KEY    
            )
        """)
    print("logs sqlite initialized")

    #i made this one myself no ai no reference :D 
    with sqlite3.connect("errors.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    command TEXT,
                    input TEXT,
                    output TEXT,
                    user TEXT
            )           
        """)
    print("errors sqlite initialized")
    with sqlite3.connect("blacklist.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted (
        uid INTEGER PRIMARY KEY,
        user TEXT
        )
    """)
    print("blacklist sqlite initialized")

    with open("sinners.json", "r", encoding='utf-8') as file:
        prompts = json.load(file)
    print("prompts loaded from json")
    print(prompts.keys())

init()
blacklist_uid(1232910902525952020, "berry")
unblacklist_uid(1232910902525952020)
bot.run(disc_client)