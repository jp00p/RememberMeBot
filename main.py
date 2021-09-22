import discord
from discord.ext import tasks
import os
import random
from replit import db
from zalgo_text import zalgo    
from PIL import Image, ImageFilter
import glitchart
import requests
from glitch_this import ImageGlitcher
from bs4 import BeautifulSoup
import asyncio
from trivia import trivia
import tmdbsimple as tmdb
from fuzzywuzzy import fuzz


tmdb.API_KEY = os.getenv('TMDB_KEY')
TMDB_IMG_PATH = "https://image.tmdb.org/t/p/w500"
 
register_channel = 882804214588407901
crew_channel = 882804258049757224
ghost_channel = 882804279180689470
control_channel = 883393837173706812

crew_role = 883071740891254844
ghost_role = 883071789838778399

greetings = [
  'Welcome aboard, {0} -- nothing strange going on here...',
  'Happy Halloween {0}! Your registration has been recorded (in blood).',
  'We will remember this, {0}.',
  'I know what you did last summer, {0}.',
  '{0}’s registration is coming from INSIDE THE DISCORD!!!',
  'Now you’ve done it, {0}.',
  '{0}: your name has been recorded in the Tome of Names.',
  'We’re excited to see you here, {0}.  Very excited.',
  'Welcome {0}! The ceremony begins at dawn.',
  'A sickening crunch is heard as {0} opens the doors.',
  'Greetings, {0}!  Please be mindful of any sacred relics!',
  'Welcome aboard, {0}. STAY AWAY FROM DECK 6',
  'We have been waiting for you, {0}.',
  'There was a slight transporter malfunction bringing you aboard, {0}. I\'m sure it\'s nothing to worry about.',
]

alert_intros = [
  'The ship-wide intercom crackles to life',
  'The intercom beeps',
  'An unfamiliar voice over the intercom says',
  'You think you hear the Captain\'s voice'
]

alerts = [
  'For your own safety, please keep out of any subliminal or non-Euclidian Jeffries tubes.',
  'Please report to the Captain\'s office for your final review',
  'We have reports of screaming on deck 13. Believe nothing.',
  'Attention all senior staff: please report to deck 13 for The Ritual.', 
  'Attention all containment officers: We have a code VOID on deck 13. This is not a drill.',
  'Until further notice, the morgue is off limits to all officers.',
  'Do not attempt to communicate with anyone you do not recognize.',
  'We are watching you.',
  'We\'re coming to get you...',
  'There are unconfirmed reports of crewmembers dissolving into the floors. Mind your step!',
  'Are you following the rules?',
  'Please keep away from all windows or portholes until further notice.',
  'There\'s no cause for alarm.',
  'Will anyone with necromancy experience please report to deck 13?',
  'We are aware of the fatalities with the malfunctioning turbolifts and are actively looking into the issue. Have a nice day!',
  'Please report any untranslated or Eldritch languages your universal translator is unable to handle.',
  'It’s happening again!',
  'Transporters are currently down due to genetic mutation-related malfunctions.',
  'New in the replimat: We\'re grilling a kind of meat I bet you\'ve never tried before!',
  'The Captain has his companions, fellow devils, to admire and encourage him; but I am solitary and detested.',
  'TRICK OR TREAT!!!'
]

flavor = [
  'The lights flicker on the ship.',
  'You hear whispers down the hallway.',
  'The bulkheads creak and groan in the silence of space.',
  'The floors seem to twisting and warping... probably nothing to worry about.',
  'The red alert lights come on for a split second.  False alarm?',
  'You can hear skittering and squeaking inside the bulkheads.',
  'You glance out the window and notice the stars are gone.',
  'The PADD you\'re holding starting spitting out weird runes and shapes.',
  'You hear the sound of a malfunctioning turbolift whooshing by.',
  'The smell of sulfur wafts down the hallway.',
  'You see movement from the corner of your eye. Probably nothing.',
  'The sound of metal against bone can be heard somewhere.'
]

jobs = [
  'Medical Officer',
  'Command Officer',
  'Engineer Officer'
]

events = [
  {
    "name" : "Banger hits the ship!",
    "description" : "A huge banger suddenly hits the ship! The red alert siren wails! Get yourself somewhere safe!",
    "aftermath" : "Another banger rocks the ship with even more violence! The intertial dampeners in {0} were offline at the time due to a mysterious malfunction..."
  }
]

# read a file line by line into an array
def readFile(fileName):
  fileObj = open(fileName, "r") # opens the file in read mode
  words = fileObj.read().splitlines() # puts the file into an array
  fileObj.close()
  return words


spooky_words_master = readFile("./lore/spooky_words")
movies_master = readFile("./lore/auto_movie_list")
drinks_master = readFile("./lore/drinks")
advice_master = readFile("./lore/advice")
glassware_master = readFile("./lore/glassware")


class SpookyClient(discord.Client):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        random.seed()

        self.headers = {'user-agent': 'Mozilla/5.0'}

        self.guild = -1
        self.stopped = False

        self.last_intro = -1
        self.last_alert = -1
        self.last_flavor = -1
        self.last_greeting = -1
        self.last_job = -1

        self.event_happening = False
        self.end_of_event = False
        self.event = -1
        self.event_room = ""

        self.num_words = 30
        self.spooky_words = random.sample(spooky_words_master, self.num_words)
        self.words_used = 0

        self.crew_quiz_started = False
        self.crew_quiz = []
        self.correct_answers = []

        self.movie_quiz_started = False
        self.movie_title = ""
        self.movie_answers = []
        self.movie_release_date = ""
        self.movie_desc = ""

        self.locations = {
          "turbolift" : { "name" : "Turbolift", "crew": [], "tasks" : [], "desc":"The turbolift moves you between stations on the ship.\nUse `move` to go somewhere else now! Type `map` to see the map." },
          "bridge" : { "name" : "Bridge", "crew": [], "tasks": ["raise shields", "lower shields", "speed up", "speed down"], "desc":"The bridge is where the primary ship functions are controlled.  Only Command officers may use the bridge.\nCommands:`lower shields` `raise shields` `speed up` `speed down`" },
          "sickbay" : { "name" : "Sicks Bay", "crew": [], "tasks":["research"], "desc":"The primary medical facilities aboard the Hood. Medical officers may continue researching the anomalies affecting the crew here.\nCommands: `research`" },
          "cargobay" : { "name" : "Cargo Bay", "crew": [], "tasks":["take stock", "inventory"], "desc":"The cargo bay is a vast warehouse of blue barrels. It is impossible to keep track of all the stuff stored in here.\nCommands:`take stock` `inventory`" },
          "shuttlebay" : { "name" : "Shuttle Bay", "crew": [], "tasks":["explore", "take shuttle"], "desc":"The shuttle bay is where the infinite array of shuttles are launched from.\nCommands: `explore` `take shuttle`" },
          "warpcore" : { "name" : "Warp Core", "crew": [], "tasks": ["turn on", "turn off", "eject core"], "desc":"The warp core is where our ship's primary power and fuel come from.\nCommands:`turn on` `turn off`" },
          "lounge" : { "name" : "Lounge", "crew": [],  "tasks": ["jazz", "advice", "drink"], "desc":"The lounge is where the crew comes to drink, remember their friends, and seek advice from the bartender.\nCommands:`jazz` `drink` `advice`" },
        }

        self.shop = {"name":"Shop", "crew":[], "tasks":[], "desc":"A mysterious shop run by a masked Ferengi."}
        self.shop_items = [
          {
            "item" : "trivia game",
            "cost" : 250,
            "desc" : "Unlocks a trivia game you can play in the lounge."
          },
          {
            "item" : "movie quiz",
            "cost" : 450,
            "desc" : "Unlocks a movie quiz game you can play in the lounge."
          },
          {
            "item" : "orb of memory",
            "cost" : 1000,
            "desc" : "A mysterious orb"
          },
          {
            "item" : "memory seed",
            "cost" : 1000,
            "desc" : "A strange crystalline seed"
          }
        ]

        self.ship_tasks = {}

       

        # ship status        
        self.ship = {
          "shields" : "On", # shields on or off
          "speed" : 0,
          "warp_core" : "Off", # warp core on or off
        }

        self.jazz_active = False
        self.jazz_counter = 0
        self.jazz_threshold = 0
       

        # setup DB keys
        schema = ["ghosts", "crew", "ghost_messages", "bad_movies", "need_to_see"]
        db_keys = db.keys()
        for s in schema:
          if s not in db_keys: 
            db[s] = []
        
        unlocks = [
          "shop_unlocked", 
          "quiz_unlocked", 
          "movies_unlocked", 
          "movies_level_1", 
          "movies_level_2", 
          "movies_level_3", 
          "movie_hint_1", 
          "movie_hint_2"
          "quiz_hint",
        ]

        if "crystals" not in db_keys:
          db["crystals"] = 15

        for u in unlocks:
          if u not in db_keys:
            db[u] = False
        
        #self.main_ship_loop.start()
        
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.rebuild_ship_tasks()
        await self.change_presence(activity=discord.Game("Haunting the Hood 👻", type=3))
        self.guild = self.get_guild(689512841887481875)
        print('------')   
        
        if db["shop_unlocked"] == True:
          self.unlock_shop()
        
        self.main_ship_loop.start()

        '''  --- harvest a list of horror movies 
        discover = tmdb.Discover()

        for i in range(1,25+1):
          print(f"Page {i}")
          discover_args = {'primary_release_date.lte' : '2006-12-31', 'with_genres' : 27, 'sort_by' : 'popularity.desc', 'region': 'US', 'language' : 'en-US', 'page': i}
          discover.movie(**discover_args)
          #print(discover.results)
          for r in discover.results:
            with open('auto_movie_list', 'a') as f:
              f.write(r["title"] + '|' + str(r["id"]) + '|' + str(r["release_date"]) + '|' + str(r["overview"]) + '\n')
          await asyncio.sleep(1)

        '''
        await self.get_channel(crew_channel).send("Everyone has transported back to their personal quarters.")








    # HANDLE REACTIONS
    async def on_reaction_add(self, reaction, user):
      if reaction.message.channel.id != crew_channel:
        return

      #if reaction.message == self.jazz_active:
      #  if user.id not in db["crew"]:
      #    await self.remove_reaction(message=reaction.message,emoji=reaction.emoji,member=user.id)



    # HANDLE MESSAGES
    # most logic goes in here, listening for messages and responding
    async def on_message(self,message):
      
      # don't listen to yourself bot!
      if message.author.id == self.user.id:
        return     

      channel_id = message.channel.id
      channel = self.get_channel(channel_id)

      if channel_id not in [register_channel, ghost_channel, control_channel, crew_channel]:
        # completely ignore any channel cept these
        return

      # HANDLE BOT COMMANDS
      if channel_id == control_channel:
        
        if message.content.startswith("!clear_db"):
          # clear the entire db
          # also purges channels and roles
          
          if message.author.id == 572540272563716116:
            msg = "Clearing the DB of all crew, ghosts, messages... :ghost:"
            db["ghost_messages"] = ["VOID"]
            crew = db["crew"]
            ghosts = db["ghosts"]
            all_crew = crew.value + ghosts.value

            keys = db.keys()
            for c in all_crew:
              if c in keys:
                del db[c]
            db["crew"] = []
            db["ghosts"] = []
            db["crystals"] = 0

            for id in all_crew:
              user = await self.guild.fetch_member(id)
              remove_role_1 = discord.utils.get(user.guild.roles, id=ghost_role)
              remove_role_2 = discord.utils.get(user.guild.roles, id=crew_role)
              if remove_role_1 in user.roles:
                await user.remove_roles(remove_role_1)
              if remove_role_2 in user.roles:
                await user.remove_roles(remove_role_2)

            reg = self.get_channel(register_channel)
            await reg.purge(limit=1000)

            crew = self.get_channel(crew_channel)
            await crew.purge(limit=1000)

            ghost = self.get_channel(ghost_channel)
            await ghost.purge(limit=1000)
          else:
            msg = "Only jp00p may clear the ghost DB"

          await channel.send(msg)       

        if message.content.startswith("!list_creepy"):
          # list all creepy messages
          creepies = db["ghost_messages"]
          msg = ""
          for c in creepies:
            msg += c + "\n"
          await channel.send(msg)

        if message.content.startswith("!set_job"):
          args = message.content.replace("!set_job ", "").split("_")
          player = db[str(args[0])].value
          player["job"] = args[1]
          db[str(args[0])]["job"] = player["job"]
          await channel.send("Job set")

        if message.content.startswith("!send_alert"):
          # send a random alert
          await self.send_alert(self.get_channel(crew_channel))
          await channel.send("Sending alert")

        if message.content.startswith("!clear_wishlist"):
          db["need_to_see"] = []
          await channel.send("Wishlist cleared!")
        
        if message.content.startswith("!set_crystals"):
          amt = message.content.lower().replace("!set_crystals ", "" )
          
        
        if message.content.startswith("!make_ghost"):
          user_id = message.content.replace("!make_ghost ", "")
          ghosts = db["ghosts"]
          if user_id in ghosts:
            await channel.send("User already a ghost!")
          else:
            await self.make_ghost(user_id)
            await channel.send("User has been ghost'd")

        if message.content.startswith("!resurrect"):
          user_id = int(message.content.replace("!resurrect ", ""))
          ghosts = db["ghosts"]
          if user_id not in ghosts:
            await channel.send("User not a ghost!")
          else:
            await self.resurrect(user_id)
            await channel.send("User has been resurrected")

        if message.content.startswith("!list_crew"):
          crew = db["crew"]
          msg = ""
          for c in crew:
            msg += str(c) + "\n"
          await channel.send("List of crew:\n" + msg)

        if message.content.startswith("!list_ghosts"):
          ghosts = db["ghosts"]
          msg = ""
          for c in ghosts:
            msg += str(c) + "\n"
          await channel.send("List of ghosts:\n" + msg)

        if message.content.startswith("!movie"):
          if self.movie_quiz_started != True:
            movie = message.content.replace("!movie", "").strip()
            if movie == "":
              movie = False
            print(movie)
            await channel.send("Sending movie!")
            await self.get_movie_image(movie)
          else:
            await channel.send("Movie quiz in progress, hold up")

        if message.content.startswith("!badmovie"):
          #self.remove_from_list(self.movie_title)
          await channel.send("Removing " + self.movie_title + " from the list.")

        if message.content.startswith("!get_info"):
          # get a user's info
          user_id = message.content.replace("!get_info ", "")
          
          keys = db.keys()

          if user_id not in keys:
            await channel.send("That user couldn't be found")
            return
          else:
            username = await self.guild.fetch_member(user_id)
            user = db[user_id].value
            msg = "Crewmember " + str(user_id) + " info:"
            msg += "\n**Name:** " + str(username.name)
            msg += "\n**Job:** " + str(user["job"])
            msg += "\n**Counter:** " + str(user["counter"])
            await channel.send(msg)
        
        if message.content.startswith("!send_flavor"):
          await self.send_flavor(self.get_channel(crew_channel))
          await channel.send("Sending flavor")

        if message.content.startswith("!start_event"):
          await channel.send("Starting event")
          await self.start_event(self.get_channel(crew_channel))
          
        
        if message.content.startswith("!send_creepy"):
          await self.send_creepy(self.get_channel(crew_channel))
          await channel.send("Sending creepy")
        
        if message.content.startswith("!stop_bot"):
          if self.stopped:
            await channel.send("Bot is already stopped")
          else:
            self.stopped = True
            await channel.send("Bot is stopped!")
        
        if message.content.startswith("!start_bot"):
          if not self.stopped:
            await channel.send("Bot is already started!")
          else:
            self.stopped = False
            await channel.send("Bot is started!")
        
        if message.content.startswith("!start_quiz"):
          if not self.crew_quiz_started:
            await channel.send("Starting quiz")
            await self.quiz.start()
        
        if message.content.startswith("!unlock_shop"):
          self.unlock_shop()
          await channel.send("Shop unlocked")

        if message.content.startswith("!lock_shop"):
          self.lock_shop()
          await channel.send("Shop locked")
            

        if message.content.startswith("!add_creepy"):
          if len(message.content) < 10:
            return
          messages = db["ghost_messages"]
          messages.append(message.content.replace("!add_creepy", ""))
          db["ghost_messages"] = messages
          print("Adding message to Ghost DB: " + message.content)
          await channel.send("Adding your message to the creepy DB")





      # HANDLE CREW CHANNEL
      if channel_id == crew_channel:
        
        player_id = db[str(message.author.id)]

        for spookyword in self.spooky_words:
          if spookyword in message.content.lower():
            spooky_reactions = ["👻", "🎃", "🦇", "💀"]
            react = random.choice(spooky_reactions)
            await message.add_reaction(react)
            self.spooky_words.remove(spookyword)
            self.words_used += 1
            if self.words_used >= 5:
              await self.spooky_word_threshold()

        if player_id:

          player = player_id.value
          
          # handle ticking down death clock
          player["counter"] -= 1

          db[message.author.id] = {
            "job" : player["job"],
            "counter" : player["counter"],
            "drinks" : player["drinks"]
          }


          # HANDLE MOVIE QUIZ
          if self.movie_quiz_started:
            
            temp_answer = self.movie_title.lower()

            ratio = fuzz.ratio(message.content.lower(), self.movie_title.lower())
            pratio = fuzz.partial_ratio(message.content.lower(), self.movie_title.lower())
            
            if (ratio > 66 and pratio > 66):
              print("Probably close enough!")
              if message.author.mention not in self.movie_answers:
                  self.movie_answers.append(message.author.mention)

          # HANDLE NORMAL TRIVIA QUIZ
          if self.crew_quiz_started:
            
            temp_answer = self.crew_quiz["correct_answer"].lower()
            user_answer = message.content.lower()

            if temp_answer in user_answer or self.crew_quiz["correct_answer"].lower() in user_answer:
              if message.author.mention not in self.correct_answers:
                self.correct_answers.append(message.author.mention)
            

          # handle moving
          if message.content.lower().startswith("move"):
            
            valid_locs = self.locations.keys()
            temp_loc = message.content.replace("move", "").lower().strip().replace(" ", "")
            # bits bits bits
            if temp_loc in ["sicksbay", "sicks bay"]:
              temp_loc = "sickbay"
            player_id = message.author.id
            mention = message.author.mention
            current_player_location = ""
           
            if temp_loc not in valid_locs:
              await channel.send("> "+mention+" -- that's not a valid location.")
            else:

              # find current location
              current_player_location = self.get_player_location(player_id)

              # don't move into the same room
              if current_player_location == temp_loc:
                await channel.send("> "+mention+" -- you're already there!")
              elif current_player_location != "turbolift" and temp_loc !="turbolift":
                await channel.send("> "+mention+" -- you must be in the turbolift to get there.")
              else:              
                # remove player's id from old location
                if current_player_location:
                  self.locations[current_player_location]["crew"].remove(player_id)

                # add player's id to new location
                self.locations[temp_loc]["crew"].append(player_id)
                room_description = "> "+mention+" moves to the "+self.locations[temp_loc]["name"]+".\n*"+self.locations[temp_loc]["desc"]+"*"

                if temp_loc == "shop":
                  room_description = "\nA hooded Ferengi has the following items for sale, and they seem very interested in your memory crystals.\n"
                  for i in self.shop_items:
                    room_description += "**" + i["item"].title() + "** - " + str(i["cost"]) + " crystals\n*" + i["desc"] + "*\n\n"

                await channel.send(room_description)


          if message.content.lower() in ["need to see", "want to see", "wishlist"]:
            wishlist = db["need_to_see"]
            if self.movie_title != "" and self.movie_title not in wishlist:
              wishlist.append(self.movie_title)
              db["need_to_see"] = wishlist
              await channel.send("Adding to the wishlist!  Type 'show wishlist' to see it.")
          
          if message.content.lower() == "show wishlist":
            msg = "**Here is your current 'need to see' list:**\n"
            wishlist = db["need_to_see"]
            for mov in wishlist:
              msg += mov + "\n"
            await channel.send(msg)
            
          # show the map!
          if message.content.lower() in ["map", "ship"]:
            crew_size = len(db["crew"].value)
            crystals = db["crystals"]
            shop = db["shop_unlocked"]
            shop_map = ""
            if shop:
              shop_map = "---- Mystery Shop"

            ship_map = '''
              \n
            [U.S.S Hood NCC-42296]
                [Compliment:{0}]
    [Shields:{1}]  [Warp Core:{2}]  [Speed:{3}]

      Bridge ------ |   |
                    | T |
                    | U | ---- Sick Bay
                    | R |
      Lounge ------ | B | 
                    | O | {5}
                    | L | -- Shuttle Bay
                    | I |
      Warp Core --- | F |
                    | T | 
                    |   | ---- Cargo Bay

            [Memory Crystals: {4}]

            '''.format(crew_size, self.ship["shields"], self.ship["warp_core"], self.ship["speed"], crystals, shop_map)
            await channel.send("```" + ship_map + "```")


          if message.content.lower() in ["profile", "status"]:
            current_player_location = self.get_player_location(message.author.id)
            if not current_player_location:
              current_player_location = "Personal Quarters"
            player = db[str(message.author.id)].value
            embed=discord.Embed(title=f"{message.author} Personnel File", description="*Starfleet Confidential*")
            embed.add_field(name='Job', value=player["job"], inline=False)
            embed.add_field(name='Location', value=current_player_location, inline=False)
            opacity = "Fully Opaque"
            if player["counter"] <= 35 and player["counter"] > 11:
              opacity = "Slightly see-through"
            if player["counter"] <= 11 and player["counter"] > 5:
              opacity = "Almost completely transparent"
            if player["counter"] <= 5:
              opacity = "Just an outline"
            embed.add_field(name='Opacity', value=opacity, inline=False)

            await channel.send(embed=embed)
            



          # handle ship tasks
        
          
          if message.content.lower() in self.ship_tasks:

            attempted_task = message.content.lower().strip()
            current_player_location = self.get_player_location(message.author.id)
            attempted_loc = self.ship_tasks[attempted_task]
            

            if attempted_loc != current_player_location:
              # player is not in the right location
              print("Player is not in the correct location to perform that task")
              await channel.send("You're not at the right station to do that.")
            else:

              player = db[str(message.author.id)].value

              #
              # BRIDGE
              #
              if attempted_loc == "bridge":
                # BRIDGE COMMANDS
                if player["job"] != "Command Officer":
                  await channel.send("Only Command Officers may use the Bridge!")
                else:
                  if attempted_task == "raise shields":
                    if self.ship["shields"] == "On":
                      await channel.send("Shields are already raised!")
                    else:
                      self.ship["shields"] = "On"
                      await channel.send("Shields up!")
                  if attempted_task == "lower shields":
                    if self.ship["shields"] == "Off":
                      await channel.send("Shields are already down!")
                    else:
                      self.ship["shields"] = "Off"
                      await channel.send("Shields down!")
                  if attempted_task == "speed up":
                    if self.ship["warp_core"] == "On":
                      if self.ship["speed"] == 9:
                        await channel.send("The ship can't go any faster than warp 9!")
                      else:
                        self.ship["speed"] += 1
                        await channel.send("Increasing speed to warp " + str(self.ship["speed"]))
                    else:
                      await channel.send("The warp core is currently offline!")
                  if attempted_task == "speed down":
                    if self.ship["warp_core"] == "On":
                      if self.ship["speed"] == 0:
                        await channel.send("The ship is already stopped!")
                      else:
                        self.ship["speed"] -= 1
                        if self.ship["speed"] == 0:
                          await channel.send("Full stop!")
                        else:
                          await channel.send("Decreasing speed to warp " + str(self.ship["speed"]))
                    else:
                      await channel.send("The warp core is currently offline!")

              #
              # SICK BAY
              #
              elif attempted_loc == "sickbay":
                # SICKS BAY COMMANDS
                if player["job"] != "Medical Officer":
                  await channel.send("Only Medical Officers may perform research.")
                else:  
                  if attempted_task == "research":
                    await self.handle_research(message.author.id)

              #
              # LOUNGE
              #
              elif attempted_loc == "lounge":
                crystals = db["crystals"]

                if attempted_task == "drink":
                  if crystals >= 1:
                    db["crystals"] = crystals - 1
                    verb = random.choice(["flip", "toss", "hand", "slip", "pass", "slide", "give"])
                    drink_choice = random.choice(drinks_master)
                    glass_choice = random.choice(glassware_master)
                    msg = "You {} the bartender a memory crystal and she pours you a {} of **{}**".format(verb, glass_choice, drink_choice)
                    player = db[str(message.author.id)].value
                    player["drinks"] += 1
                    db[str(message.author.id)] = player

                    death = random.randint(1,100)
                    if death >= 99:
                      msg += "\n ...unfortunately the anomalies affecting the ship have tainted this batch and you feel yourself starting to phase into another dimension..."
                      await self.make_ghost(message.author.id)
                  else:
                    msg = "You do not have enough memory crystals to tip the bartender.  Better not."
                  await channel.send(msg)

                if attempted_task == "advice":

                  tellers = random.choice(["a wise senior officer", "the bartender", "a random changeling", "a random patron", "an old scientist", "a down-on-their-luck redshirt", "the ship's counsellor", "a random advice machine", "someone nearby", "the voices deep within", "scrawlings on the bathroom wall", "a fortune cookie", "an old fortune telling machine"])
                  advice = random.choice(advice_master)
                  msg = "You seek advice from {}.\nThey tell you:\n\n> \"{}\"".format(tellers, advice)

                  await channel.send(msg)

                if attempted_task == "jazz":
                  if self.jazz_active:
                    await channel.send("A jazz memorial is currently in progress. Please be respectful with your finger snaps!")
                  else:
                    self.jazz_counter = random.randint(2,5)
                    self.jazz_threshold = random.randint(5,25)
                    jazz_image = random.randint(1,9)
                    await channel.send("You start the somber yet jazzy procedings for your missing friends. All crew should show their respects by reacting to the following picture with emoji they think the departed would appreciate:")
                    image = "./nightbird/jazz{}.jpg".format(jazz_image)
                    self.jazz_active = await channel.send(file=discord.File(image))



              #
              # WARP CORE
              #
              elif attempted_loc == "warpcore":
                # WARP CORE COMMANDS
                if player["job"] != "Engineer Officer":
                  await channel.send("Only Engineering Officers may use the Warp Core")
                else:
                  if attempted_task == "turn on":
                    if self.ship["warp_core"] == "On":
                      await channel.send("Warp core is already on!")
                    else:
                      self.ship["warp_core"] = "On"
                      await channel.send("The warp core comes online.")
                  
                  if attempted_task == "turn off":
                    if self.ship["warp_core"] == "Off":
                      await channel.send("Warp core is already powered down.")
                    else:
                      if self.ship["speed"] != 0:
                        await channel.send("You cannot power off the warp core while the ship is moving!")
                      else:
                        self.ship["warp_core"] = "Off"
                        self.ship["speed"] = 0
                        await channel.send("Warp core has been turned off.")

                  if attempted_task == "eject core":
                    await channel.send("You eject the warp core and everyone dies!!! Just kidding, Happy Halloween!")
              
              #
              # CARGO BAY
              #
              elif attempted_loc == "cargobay":
                if attempted_task in ["take stock", "inventory"]:
                  stock_chance = random.randint(1,5)
                  barrel_chance = random.randint(0,100)
                  if barrel_chance <= 5:
                    await channel.send("As " + message.author.mention + " is taking stock of the cargo bay, a blue barrel falls right on top of their head! They seem to phase out of existence before the barrel lands...")
                    await self.make_ghost(message.author.id)
                  else:
                    if stock_chance >= 2:
                      crystal_amt = random.randint(1,10)
                      db["crystals"] += crystal_amt 
                      await channel.send("While taking stock, " +message.author.mention+" finds a surplus of " + str(crystal_amt) + " memory crystals!")
                    else:
                      await channel.send(message.author.mention + " was unable to find anything unaccounted for in the cargo bay.")

              #
              # SHUTTLE BAY
              #                    
              elif attempted_loc == "shuttlebay":
                if attempted_task in ["explore", "take shuttle"]:
                  if self.ship["speed"] > 0:
                    await channel.send("You cannot take a shuttle out while the ship at warp!")
                  elif self.ship["shields"] == "On":
                    await channel.send("The shields need to be down before the shuttle can leave!")
                  else:
                    await channel.send(message.author.mention + " takes a shuttle out for a brief survey of the system...")
                    disaster_roll = random.randint(1,100)
                    if disaster_roll > 50:
                      await channel.send("...and "+message.author.mention+"'s shuttle was never seen again...")
                      await self.make_ghost(message.author.id)
                    else:
                      crystal_amt = random.randint(50,100)
                      db["crystals"] += crystal_amt
                      await channel.send("...and "+message.author.mention+" returns with a bounty of " + str(crystal_amt) + " memory crystals!")
              else:
               print("Task that can be done anywhere! Should not see this.")


        
          
          
          # handle converting player to ghost after message has been sent
          if player["counter"] <= 0 and message.author.id not in db["ghosts"]:
            await self.make_ghost(message.author.id)
        





      # handle both crew and ghost channel
      if channel_id == crew_channel or channel_id == ghost_channel:
        
        if message.attachments:
          glitched_image = ""
          imageURL = message.attachments[0].url
          print(imageURL)
          
          # handle jpg
          if imageURL.lower().endswith(".jpg") or imageURL.endswith(".jpeg"):
            r=requests.get(imageURL, headers=self.headers)
            with open('image.jpg', 'wb') as f:
                f.write(r.content)
            glitchart.jpeg("image.jpg", min_amount=5, max_amount=10)
            glitched_image = "image_glitch.jpg"

          # handle png
          if imageURL.lower().endswith(".png"):
            r=requests.get(imageURL, headers=self.headers)
            with open('image.png', 'wb') as f:
                f.write(r.content)
            glitchart.png("image.png", min_amount=5, max_amount=10)
            glitched_image = "image_glitch.png"

          # handle webp
          if imageURL.lower().endswith(".webp"):
            r=requests.get(imageURL, headers=self.headers)
            with open('image.webp', 'wb') as f:
                f.write(r.content)
            glitchart.webp("image.webp", min_amount=5, max_amount=10)
            glitched_image = "image_glitch.webp"

          # handle attached gif
          if imageURL.lower().endswith(".gif"):
            glitcher = ImageGlitcher()
            r=requests.get(imageURL, headers=self.headers)
            with open('image.gif', 'wb') as f:
                f.write(r.content)
            img, src_gif_duration, src_gif_frames  = glitcher.glitch_gif(Image.open('image.gif'), random.randrange(1,5), color_offset=random.choice([True, False]))
            img[0].save('glitched_image.gif', format='GIF',  append_images=img[1:],save_all=True,duration=src_gif_duration,loop=0 )
            
            glitched_image = "glitched_image.gif"
            
          await channel.send(file=discord.File(glitched_image))
          await message.delete()
        
          # handle gif embeds
        elif message.content.startswith("https://tenor.com") or message.content.endswith(".gif"):
          glitcher = ImageGlitcher()
          print("Handling embedded gif")
          pageURL = message.content         
          r=requests.get(pageURL, headers=self.headers)
          soup = BeautifulSoup(r.content, "html.parser")
          image_src = soup.find(attrs={"rel": "image_src"}).get('href')
          print("image src ", image_src)

          r=requests.get(image_src, headers=self.headers)
          with open('image.gif', 'wb') as f:
            f.write(r.content)

          img, src_gif_duration, src_gif_frames  = glitcher.glitch_gif(Image.open('image.gif'), random.randrange(1,5), color_offset=random.choice([True, False]))

          img[0].save('glitched_image.gif', format='GIF',  append_images=img[1:],save_all=True,duration=src_gif_duration,loop=0 )
          glitched_image = "glitched_image.gif"
          
          await channel.send(file=discord.File(glitched_image))
          await message.delete()
      
      # handle only ghost channel
      if channel_id == ghost_channel:
        if len(message.content) > 10 and len(message.content) < 69:
          messages = db["ghost_messages"]
          messages.append(message.content)
          db["ghost_messages"] = messages
          print("Adding message to Ghost DB: " + message.content)
          await channel.send(message.author.mention + "... your message has passed through the veil somehow... ")

      # handle register channel
      if channel_id == register_channel:
        # register a new crew member
        crew = db["crew"]
        
        if message.author.id in crew:
          await message.delete()
        else:
          await self.register_new_crew(message.author, channel)


    
    
    # register a new user
    async def register_new_crew(self, user, channel):
      if user.id not in db["crew"]:
        db["crew"].append(user.id)

      # add crew role
      role = discord.utils.get(user.guild.roles, id=crew_role)
      if role not in user.roles:
        await user.add_roles(role)

      job = random.choice(jobs)
      while job == self.last_job:
        job = random.choice(jobs)

      self.last_job = job
        
      death_clock = random.randint(50,70)

      db[str(user.id)] = {
        "job" : job,
        "counter" : death_clock,
        "location" : 0,
        "drinks" : 0
      }

      greeting = random.choice(greetings).format(user.mention)
      greeting += "\n\nYour job is: __{0}__".format(job)

      await channel.send(greeting)




    # make a user a ghost
    async def make_ghost(self, user):
      print(str(user) + " is being converted to a ghost!")
      user = await self.guild.fetch_member(int(user))
      print(user)

      if user:
        ghosts = db["ghosts"]
        ghosts.append(int(user.id))
        db["ghosts"] = ghosts

        crew = db["crew"]
        if user.id in crew:
          crew.remove(user.id)
          db["crew"] = crew

        remove_role = discord.utils.get(user.guild.roles, id=crew_role)
        role = discord.utils.get(user.guild.roles, id=ghost_role)
        if remove_role in user.roles:
          await user.remove_roles(remove_role)
        if role not in user.roles:
          await user.add_roles(role)
      else:
        print("User not found")



    # resurrect a user
    async def resurrect(self, user_id):
      print(f"Resurrecting {user_id} now")
      user = await self.guild.fetch_member(user_id)
      print(user)
      if user:
        
        ghosts = db["ghosts"]
        if user.id in ghosts:
          
          # remove from db
          ghosts.remove(user.id)
          db["ghosts"] = ghosts
          # add to crew db
          crew = db["crew"]
          crew.append(user.id)
          db["crew"] = crew

          player = db[str(user_id)].value
        
          db[str(user_id)] = {
            "job" : player["job"],
            "counter" : 100,
            "drinks" : player["drinks"]
          }

          remove_role = discord.utils.get(user.guild.roles, id=ghost_role)
          role = discord.utils.get(user.guild.roles, id=crew_role)
          if remove_role in user.roles:
            await user.remove_roles(remove_role)
          if role not in user.roles:
            await user.add_roles(role)
          channel = self.get_channel(crew_channel)
          await channel.send(user.mention + " has reappeared in front of you!")
        else:
          print("User not a ghost")
      else:
        print("User not found")


    # when enough spooky words have been typed
    async def spooky_word_threshold(self):
      print("Reached the number of spooky words required")
      self.spooky_words = random.sample(spooky_words_master, self.num_words)
      print("New batch of words")
      print(self.spooky_words)
      self.words_used = 0
      ghosts = db["ghosts"]
      if len(ghosts) > 0:
        random_ghost = random.choice(ghosts)
        print(f"Random ghost is {random_ghost}")
        await self.resurrect(random_ghost)
      else:
        print("No one to resurrect yet!")




    @tasks.loop(seconds=15, count=1)
    async def quiz(self):
      if self.crew_quiz_started:
        return
      print("Starting quiz")
      
      self.crew_quiz_started = True
      question = await trivia.question(amount=1, category=0, difficulty='easy', quizType='multiple')
      print(question[0])
      self.crew_quiz = question[0]
      
      answers = self.crew_quiz["incorrect_answers"]
      answers.append(self.crew_quiz["correct_answer"])
      random.shuffle(answers)

      embed=discord.Embed(title=self.crew_quiz["question"], description=self.crew_quiz["category"], color=0xff00ea)
      embed.set_author(name="Quiz Attack!!!")
      #embed.set_thumbnail(url="https://c.tenor.com/7QhoA9wcstgAAAAC/confused-no.gif")
      answer_string = ""

      for i in answers:
        answer_string += i + "\n"
      
      embed.add_field(name='Choices', value=answer_string, inline=False)
      embed.set_footer(text="type the full answer in chat!")
      channel = self.get_channel(crew_channel)
      await channel.send(embed=embed)

    @quiz.after_loop
    async def on_quiz_timeout(self):
      print("Quiz finished")
      channel = self.get_channel(crew_channel)
      msg = "The quiz is finished! The correct answer was **" + self.crew_quiz["correct_answer"] + "**"
      if len(self.correct_answers) > 0:
        msg += "\n WINNERS: \n"
        for m in self.correct_answers:
          msg += m + "\n"
      else:
        msg += "\n No one got it right this time! \n"

      await channel.send(msg)
      self.crew_quiz_started = False
      self.quiz.stop()
      self.correct_answers = []
      



    # send a ghost message
    async def send_creepy(self, channel):
      print("Sending creepy message")
      messages = db["ghost_messages"]
      if len(messages) <= 0:
        print("Empty message db")
        return
      msg = random.choice(messages)
      messages.remove(msg)
      db["ghost_messages"] = messages
      for spooky_word in self.spooky_words:
        if spooky_word in msg:
          tempword = list(spooky_word)
          random.shuffle(tempword)
          tempword = ''.join(tempword).upper()
          print("Scrambling {0} into {1}".format(spooky_word, tempword))
          msg = msg.replace(spooky_word, "**"+tempword+"**")
      creepy = zalgo.zalgo().zalgofy(msg)
      creepy = "\n :black_small_square: \n> ..." + creepy + "...\n :black_small_square: \n"
      if creepy != "":
        await channel.send(creepy)
      else:
        print("Empty creepy message?")
        print(creepy)
        return

    # SEND FLAVOR TEXT
    async def send_flavor(self, channel):
      print("Sending flavor")

      # don't do the same one as last time
      f = self.last_flavor
      while f == self.last_flavor:
        f = random.randint(0, len(flavor)-1)
      self.last_flavor = f
      msg = ":black_small_square:\n *"+flavor[f]+"* \n :black_small_square:"
      await channel.send(msg)

    # SEND SHIPWIDE ALERT
    async def send_alert(self, channel):
      print("Sending alert")

      # don't do the same one as last time
      intro = self.last_intro
      while intro == self.last_intro:
        intro = random.randint(0, len(alert_intros)-1)
      self.last_intro = intro

      alert = self.last_alert
      while alert == self.last_alert:
        alert = random.randint(0,len(alerts)-1)
      self.last_alert = alert      

      msg = ":black_small_square:\n"
      msg += "**"+alert_intros[intro]+"**"
      msg += ":\n"
      msg += '> *"' + alerts[alert] + '"*'
      msg += '\n:black_small_square:'
      if msg != "":
        await channel.send(msg)


    async def start_event(self, channel):
      print("Sending event!")
      self.event_happening = True
      # choose a random event
      self.event = events[0]
      self.event_room = random.choice(locations)
      
      await channel.send("**"+self.event["name"]+"**" + "\n" + self.event["description"])
      await self.get_channel(ghost_channel).send("*Mysterious energies are building up in the following location:* " + self.event_room)
      self.event_timer.start()

    async def end_event(self, channel):
      self.end_of_event = True
      print("Ending event!")
      # choose a room
      affected_room = self.event_room
      room_index = locations.index(affected_room)
      num_people = random.randint(1,3)
      affected_crew = []
      # deal with the people in the rooms
      crew = db["crew"]
      keys = db.keys()

      aftermath = self.event["aftermath"].format(affected_room)
      
      # show aftermath
      await channel.send(aftermath)
      
      # casualty report
      report = f"{num_people} people are unaccounted for after the event."
      await channel.send(report)
    
      # reset event vars
      self.event_happening = False
      self.event = -1
      self.end_of_event = False

    @tasks.loop(seconds=15, count=1) # event lasts 15 sec
    async def event_timer(self):
      print("Event timer tick")
      
    @event_timer.after_loop
    async def on_event_timer_timeout(self):
      print("Event timer is over")
      await self.end_event(self.get_channel(crew_channel))






    @tasks.loop(seconds=20) # task runs every x seconds
    async def main_ship_loop(self):
      print("Starting background task.  Hmm what to do this time...")
      
      if self.jazz_active:
        print(f"Jazz counter: {self.jazz_counter}")
        if self.jazz_counter <= 0:
          message = await self.get_channel(crew_channel).fetch_message(self.jazz_active.id)
          reactions = message.reactions
          total_reactions = 0
          for r in reactions:
            player = await r.users().flatten()
            for p in player:
              if p.id in db["crew"]:
                total_reactions += 1
          print(f"Total reactions from crew: {total_reactions}")
          if total_reactions >= self.jazz_threshold:
            
            await self.get_channel(ghost_channel).send("You hear the warbling of a trombone from across the veil...")

            # ressurect a few ghosts
            ghosts = db["ghosts"]
            if len(ghosts) > 0:
              max_rez = round(len(ghosts)/10)+1
              print(f"Resurrecting up to {max_rez} ghosts")
              lucky_ghosts = random.sample(ghosts, max_rez)
              for ghost in lucky_ghosts:
                await self.resurrect(ghost)
          else:
            await self.get_channel(crew_channel).send("While your jazz proceedings were lighthearted yet serious, nothing supernatural seems to have happened this time.")

          self.jazz_active = False
          
        self.jazz_counter -= 1
      if self.stopped:
        print("Bot is stopped")
        return

      decide = random.randint(1,100)

      if decide == 6: 
        await self.send_creepy(self.get_channel(crew_channel))

      elif decide == 7:
        await self.send_alert(self.get_channel(crew_channel))

      elif decide == 8:
        await self.send_flavor(self.get_channel(crew_channel))
      
      elif decide == 9 or decide == 10:
        await self.get_movie_image()
      
      else:
        print("Doin nothin' this time")

    @main_ship_loop.before_loop
    async def before_ship_loop_task(self):
      await self.wait_until_ready() # wait until the bot logs in
    

    # get a random movie image and start the quiz
    async def get_movie_image(self, movie_name=False):
      self.stopped = True
      
      movie_choice = random.choice(movies_master)

      while movie_choice == "":
        movie_choice = random.choice(movies_master)

      movie_choice = movie_choice.split("|")

      self.movie_title = movie_choice[0]
      self.movie_release_date = movie_choice[2]
      self.movie_desc = movie_choice[3]

      image_result = tmdb.Movies(movie_choice[1]).images(include_image_language="en,null")

      #print(image_result)
      
      if len(image_result) == 0 or not "backdrops" in image_result or len(image_result["backdrops"]) == 0:
        #self.remove_from_list(movie_name)
        await self.get_movie_image()
        return

      random_image = random.choice(image_result["backdrops"])
      r=requests.get(TMDB_IMG_PATH + random_image["file_path"], headers=self.headers)
      
      # get movie screenshot and save to disk
      with open('movie.jpg', 'wb') as f:
        f.write(r.content)
      self.movie_quiz.start()



    @tasks.loop(seconds=20, count=1)
    async def movie_quiz(self):
      print("Movie quiz starting")
      self.movie_quiz_started = True

      channel = self.get_channel(crew_channel)
      glitched_image = "movie_glitch.jpg"
      # glitch the movie art
      glitchart.jpeg("movie.jpg", min_amount=20, max_amount=50)
      image = Image.open(glitched_image)
      # blur the movie art
      image = image.filter(ImageFilter.BoxBlur(2))
      image.save(glitched_image)
      await asyncio.sleep(3)
      await channel.send("\n.\n.\n.")
      await channel.send(file=discord.File(glitched_image))
      await channel.send("What movie is this?\nReleased: " + self.movie_release_date + "\nClue:||" + self.movie_desc.replace(self.movie_title, "**REDACTED**").replace(self.movie_title.lower(), "**REDACTED**") + "||")

    @movie_quiz.after_loop
    async def movie_quiz_finish(self):
      # sleep to allow any last minute stragglers
      await asyncio.sleep(1)
      print("Movie quiz finished")
      channel = self.get_channel(crew_channel)
      await channel.send(file=discord.File("movie.jpg"))
      await channel.send("The movie was *"+self.movie_title+"*")
      msg = ""
      if len(self.movie_answers) > 0:
        msg = "The winners were:\n"
        for m in self.movie_answers:
          msg += m + "\n"
      else:
        msg = "No one guessed it correctly!"
      await channel.send(msg)
      self.movie_answers = []
      #self.movie_title = ""
      self.stopped = False
      self.movie_quiz_started = False

    # remove a movie from the master list
    def remove_from_list(self, movie_name):
      print("Removing movie from list: " + movie_name)
      badmovies = db["bad_movies"]
      badmovies.append(movie_name)
      db["bad_movies"] = badmovies
      with open("movies", "r+") as f:
        d = f.readlines()
        f.seek(0)
        for i in d:
            if i != movie_name:
                f.write(i)
        f.truncate()
      return


    # find a player's location in the ship
    def get_player_location(self, player_id):
      for loc in self.locations:
        if player_id in self.locations[loc]["crew"]:
          return loc

    # get array of all players in a room
    def get_players_in_room(self, room_name):
      players = []
      for crew in self.locations[room_name]["crew"]:
        players.append(crew)

      return players
  
    async def handle_research(self, researcher):

      research_cost = 10
      researcher = await self.guild.fetch_member(researcher)
      channel = self.get_channel(crew_channel)
      patients = self.get_players_in_room("sickbay")
      patients.remove(researcher.id)

      if len(patients) <= 0:
        await channel.send("You can't perform research on yourself.  Someone else needs to be in Sicks Bay!")
        return

      patient = random.choice(patients)
      patient_records = db[str(patient)].value

      crystals = db["crystals"]

      if crystals < research_cost:
        await channel.send("Not enough memory crystals to perform the research!")
      else:
        amount_restored = random.randint(10,30)
        patient_records["counter"] += amount_restored
        db[str(patient)]["counter"] = patient_records["counter"]
        crystals -= 10
        db["crystals"] = crystals
        patient_name = await self.guild.fetch_member(patient)
        patient_name = patient_name.mention
        await channel.send("You spent 10 Memory Crystals researching, and restored " + str(amount_restored) + " temporal essence to " + patient_name)
      
    def unlock_shop(self):
      db["shop_unlocked"] = True
      print("Shop is open!")
      self.locations['shop'] = self.shop
      for i in self.shop_items:
        self.ship_tasks["buy "+i["item"]] = "shop"

    def lock_shop(self):
      print(self.locations)
      db["shop_unlocked"] = False
      if self.locations['shop']:
        self.locations.pop('shop')
        self.rebuild_ship_tasks()
      print("Shop is closed!")

    def rebuild_ship_tasks(self):
      # create list of all tasks for matching later
      self.ship_tasks = {}
      for loc in self.locations:
        for t in self.locations[loc]["tasks"]:
          self.ship_tasks[t] = loc
      

client = SpookyClient()
client.run(os.getenv('TOKEN'))