from google import genai
from dotenv import load_dotenv
import discord
from discord import app_commands
import os
from datetime import datetime
import asyncio
import aiofiles

#super small 1 day project for personal use
#is now like 1 week project I am actually going to deploy

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

def execute_command(sinner, input):
    pass

blacklist = []
#checks if a uid is in blacklist (txt file)
def is_blacklisted(uid):
    with open("blacklist.txt", "r") as file:
        for id in file.read().splitlines():
            if id == uid:
                return True
        return False

#parses lines in logs and turns them into an easily accessible dictionary
def parse_log_line(line):
    parts = line.split(" || ")
    result = {}
    for part in parts:
        if ": " in part:
            key, value = part.split(": ", 1)
            result[key.strip()] = value.strip()
    return result

#perms n setup stuff
@bot.tree.command(name="quixotify", description="Quixotify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def quixotify(interaction: discord.Interaction, text: str):

    user = interaction.user
    #stop user if they are banned
    if is_blacklisted(user.id):
        await interaction.response.send_message("Nay, I shan't allow a villain such as thee to use mine services most escpecial")
        return

    #required so discord doesn't cut the bot off if takes too long
    await interaction.response.defer()

    try:
        #next 5 lines ai generated
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
                        contents="You are a translator. Convert the following text into how Don Quixote from Limbus Company would say it. sort of archaic English, enthusiastic, chivalric. Examples: 'Mine curriculum most especial!'(sad at destruction of her creation), 'Hmph! Thy patterns have become far too predictable!', 'I am no child! And why am I denied the chef’s place when Sinclair is allowed to do such on the other team!', 'Manager Esquire, to where in the world hast thou disappeared?!'. Don't overdo the archaic english too! Roughly match input length. Text in parentheses = extra instructions. Only output the translation, nothing else. Make sure to preserve noun, account for incorrect grammer/slang. Don't add extra nouns/context beyond what is provided. If unclear respond with 'k'. Translate this text: " + text
        ))

        message = response.text
        #adds info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Quixotify || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "Alas it appeareth that I am out of service! Tis truly a most lamentable occurence!"

        #adds error info to log 
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Quixotify || INPUT: {text} || FROM: {user} || ERROR: {str(e)}\n")

    #actually sends the message
    await interaction.followup.send(message)

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
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Ryoshify || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")
        with open("sinclair_translator.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Ryoshify || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I.A.B."

        #adds error info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Ryoshify ||  INPUT: {text} || FROM: {user} || ERROR: {str(e)}\n")

    #sends the message
    await interaction.response.send_message(message)

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
        string = None
        #looks in log for an output of user-inputted text
        with open("sinclair_translator.txt", "r") as file:
            for log in file.read().splitlines():
                #parse_log_line returns a dictionary
                temp = parse_log_line(log)
                if temp["OUTPUT"] == text:
                    string = temp["INPUT"]

        if string:
            message = string 
        else:
            message = "Can't translate :<"
        #adds info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Sinclair translate || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I-I'm broken."

        #adds error info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Sinclair translate ||  INPUT: {text} || FROM: {user} || ERROR: {str(e)}\n")

    #sends the message
    await interaction.response.send_message(message)

#perms n setup stuff
@bot.tree.command(name="outify", description="Outify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def outify(interaction: discord.Interaction, text: str):

    user = interaction.user
    #stop user if they are banned
    if is_blacklisted(user.id):
        await interaction.response.send_message("The Quixotifier doesn't associate with the likes of you, begone vile scum")
        return

    #required so discord doesn't cut the bot off if takes too long
    await interaction.response.defer()

    try:
        #next 5 lines ai generated
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
                        contents="You are a translator. Convert the following text into how Outis from Limbus Company would say it. She is a war veteran and is very serious. She's also a bootlicker and sucks up to those who have more authority than her. She is disrespectful and looks down on those incapable/inferior. Examples: 'The absurdity of having to carry out missions with rookies who haven't even set foot on a real battlefield... Ah, I am most definitely not referring to you, Executive Manager', 'In any case, it's neither of our faults, Executive Manager' (when defeated), 'This was 99% your brilliant leadership and 1% my competence!'(victory), 'Rookies' (ally death). MAKE SURE RESPONSES ARE SHORT IT IS VITAL THAT YOU DON'T MAKE A LONG RESPONSE 20 WORDS MAX.  Make sure to not overexaggerate her personality. Essentially, if the text speaks down about someone, demean them more, if it praises someone, absolutely glaze them and go full bootlicker don't hold back on the glaze but stay within length cap. If message is neutral towards someone, be rude but don't directly demean them. In addition, don't refer to Executive Manager at all unless the text itself demands it! Don't overuse words from examples. Simply imitate that style of speech. Don't refer to a person more than once in your translation. Text in parentheses = extra instructions. Make sure to PRESERVE NOUNS AND NAMES THIS IS VITAL, account for incorrect grammer/slang. If the text is neutral when describing someone, be slightly rude BUT DONT BE OVERLY DEMEANING. When the text insults someone however, be as mean and demeaning as possible. Don't shift the insult to be something else, stick with the same approximate insult. (Ex: input: you're ugly SHOULDNT translate to pathetic amateur). Don't add extra context/info beyond what was in original text. YOU ARE TRANSLATING THE TEXT TO WHAT OUTIS WOULD SAY, NOT RESPONDING AS OUTIS. Translate this text: " + text
        ))

        message = response.text
        #adds info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Outify || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I am indisposed at the moment."

        #adds error info to log 
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Outify || INPUT: {text} || FROM: {user} || ERROR: {str(e)}\n")

    #actually sends the message
    await interaction.followup.send(message)

#perms n setup stuff
@bot.tree.command(name="hongify", description="Hongify your text")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def hongify(interaction: discord.Interaction, text: str):

    user = interaction.user
    #stop user if they are banned
    if is_blacklisted(user.id):
        await interaction.response.send_message("I'm sorry but you are banned. Fuhu~")
        return

    #required so discord doesn't cut the bot off if takes too long
    await interaction.response.defer()

    try:
        #next 5 lines ai generated
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
                        contents="You are a translator. Convert the following text into how Hong Lu from Limbus Company would say it. Hong Lu is a carefree man who came from an extremely wealthy background. He doesn't care too much about life but is still kind. He isn't mean. He also uses '~' and 'Fuhu' in his dialgoue regularly (but be sure to NOT OVERUSE these!) Examples of dialgoue: 'I will do what I can~ If it flunks, it flunks~' 'Oh dear, does it hurt a lot? Please tell me later' (ally death), 'No need to shower me with compliments~ I am sure you had a part in it, too.', 'When you're distraught, simply remember that life goes on even if what you're doing now doesn't work out. Then, you'll be free of worries.'  Don't overuse words from examples. Simply imitate that style of speech. Don't refer to a person more than once in your translation. Text in parentheses = extra instructions. Make sure to PRESERVE NOUNS AND NAMES THIS IS VITAL, account for incorrect grammer/slang. DON'T BE MEAN! HONG LU IS A KIND MAN. In addition, don't provide extra info/context the original text didn't contain (example of mistake: input: thas fascinatng! output: Oh my, that is truly fascinating~ Fuhu, I wonder what the story behind it might be?. Mistake: added extra info (something about someones story)) YOU ARE TRANSLATING THE TEXT TO WHAT HONG LU WOULD SAY, NOT RESPONDING AS HONG LU. Translate this text: " + text
        ))

        message = response.text
        #adds info to log
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Hongify || INPUT: {text} || FROM: {user} || OUTPUT: {message}\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        message = "I am unable to respond right now. Fuhu~"

        #adds error info to log 
        with open("log.txt", "a") as file:
            file.write(f"[{datetime.now()}] || COMMAND: Hongify || INPUT: {text} || FROM: {user} || ERROR: {str(e)}\n")

    #actually sends the message
    await interaction.followup.send(message)

bot.run(disc_client)