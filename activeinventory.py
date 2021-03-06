# Inventory
class Inventory:

    def __init__(self, slots = 0):
        self.slots = slots
        self.objects = dict()

    def add_object(self, obj, amount = 1):
        if amount*obj.bulk + self.get_object_bulk() <= self.slots:
            if obj in self.objects.keys():
                self.objects[obj] += amount
            else:
                self.objects[obj] = amount
            return f"You have {self.objects[obj]} {obj}(s)"
        else:
            return f"You don't have enough room to fit {amount} {obj}(s)"

    def remove_object(self, obj, amount = 1):
        if obj in self.objects.keys():
            if self.objects[obj] > amount:
                self.objects[obj] -= amount
                return f"You have {self.objects[obj]} {obj}(s)"
            elif self.objects[obj] == amount:
                self.objects.pop(obj)
                return f"You have no more {obj}s"
            else:
                return f"You don't have at least {self.objects[obj]} {obj}(s)"
        else:
            return f"You don't have any {obj} at all in the first place!"

    def get_object_bulk(self):
        output_bulk = 0
        for obj, amount in self.objects.items():
            output_bulk += obj.bulk*amount
        return output_bulk

    def change_slots(self, slot_change):
        self.slots += slot_change
        print(f"You have {self.slots} now!")

#Character
class Character(Inventory):
    def __init__(self, id_num = 0, name = "demo", slots=0):
        Inventory.__init__(self, slots=slots)
        self.name=name
        self.id = id_num

#Price
denomination_values = {"cp":1, "sp":10, "ep":50, "gp":100, "pp":1_000}

def parse_price_str(price_str):
    for denomination in denomination_values.keys():
        if denomination in price_str:
            return (int(price_str.replace(denomination, "")), denomination)
    else:
        return 0, "cp"

class Price:
    def __init__(self, price_str = "0"):
        price_str = price_str.strip()

        if price_str == "0":
            self.amount, self.denomination = 0, "cp"
        else:
            self.amount, self.denomination = parse_price_str(price_str)

    def __str__(self):
        return str(self.amount) + str(self.denomination)

    def __repr__(self):
        return f"Price(amount={self.amount},denomination={self.denomination})"

# Object
class Object:
    def __init__(self, name = "demo", bulk = 0, price = "0"):
        self.name = name
        self.bulk = bulk
        self.price = Price(price)

    def __hash__(self):
        return hash((self.name,self.bulk, str(self.price)))

    def __eq__(self, other):
        return (self.name,self.bulk, str(self.price)) == (other.name,other.bulk, str(other.price))

    def __str__(self):
        return self.name

test_obj = Object(name = "test", bulk = 30, price="69sp")
test_inv = Inventory(slots = 100)

#############IMPORT ITEM LIST######################################

import csv

item_dict = dict()
with open("items",'r') as item_file:
    item_reader = csv.reader(item_file, delimiter = ';')
    for item_row in item_reader:
        obj_name = item_row[0].lower().strip()
        obj_price = item_row[1].lower().strip().replace(',','')
        obj_bulk = item_row[2].lower().strip()
        row_obj = Object(name = obj_name, bulk = float(obj_bulk), price=obj_price)
        item_dict[obj_name] = row_obj
    print("Imported all items.")

def save_item_list(obj:Object):
    with open('items', 'a+') as item_file:
        item_writer = csv.writer(item_file, delimiter = ' ; ')
        item_writer.writerow([obj.name, obj.price, obj.bulk])

#############START BOT#############################################
import discord
from discord.ext import commands
import pickle
import os

description = '''
This bot keeps track of player inventories using the active-inventory system.
'''

users = []

def save_users(filename = "users.pickle"):
    global users
    with open(filename,'wb') as file:
        pickle.dump(users, file)
    print(f"Saved current users to {filename}")

def load_users(filename = "users.pickle"):
    global users
    with open(filename,'rb') as file:
        users = pickle.load(file)
    print(f"Loaded previous users from {filename}")

#Loads last state if any
if os.path.isfile("users.pickle"):
    load_users(filename="users.pickle")

def add_user(author, new_slots:int):
    global users
    users.append(Character(name = author.name, id_num=author.id, slots = new_slots))

def is_added_user(author):
    global users
    for user in users:
        if author.id == user.id:
            return True
    return False

def change_user_slots(author, new_slots):
    global users
    for user in users:
        if author.id == user.id:
            user.slots = new_slots
            return "Success"
    return f"{author.nick} was not found."

def give_user_object(author, obj_name, amount):
    global users
    for user in users:
        if author.id == user.id:
            for item_dict_name, item_dict_obj in item_dict.items():
                if obj_name.lower() == item_dict_name:
                    return user.add_object(item_dict_obj, amount)
            return f"{obj_name} was not found."
    return f"{author.nick} was not found."

def take_user_item(author, item_name, item_amount):
    global users
    for user in users:
        if author.id == user.id:
            for obj in user.objects.keys():
                if obj.name == item_name:
                    return user.remove_object(obj, item_amount)
            return f"{item_name} was not found."
    return f"{author.nick} was not found."

def print_user_inventory(author):
    global users
    for user in users:
        if author.id == user.id:
            inv_str = ""
            for obj, amount in user.objects.items():
                inv_str += "{:<8} {:^6} {:^30}\n".format(amount,obj.bulk,str(obj))
            if not inv_str:
                inv_str += "You have nothing in your inventory 😕\n"
            else:
                inv_str = "{:<8} {:^6} {:^30}\n".format("Amount","Bulk","Item Name") + inv_str
            inv_str += f"You have {user.get_object_bulk()}/{user.slots} of slots used.\n"
            return inv_str
    return f"{author.nick} was not found."

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='>', description=description, intents=intents)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('---🤖---')

@bot.event
async def on_command(ctx):
    print(f"{ctx.author} has used {ctx.command} in {ctx.channel}")
    save_users()

@bot.command(name='slots')
async def change_slots(ctx, new_slots:int):
    """
    Updates the amount of inventory slots you have. If you haven't run this command before, this command makes your character.
    """
    try:
        if not is_added_user(ctx.author):
            add_user(ctx.author, new_slots)
        else:
            change_user_slots(ctx.author, new_slots)
        await ctx.send(f"{ctx.author} now has {new_slots} slots.")
    except Exception as e:
        print(e.with_traceback(None))
        await ctx.send(f"You need to write the command as {bot.command_prefix}slots <new amount of slots>")

@bot.command(name='register')
async def add_item_to_item_list(ctx, item_amount, item_name, bulk_per_item, worth_per_item):
    """
    Adds new item to global item list.
    """
    try:
        global item_dict
        item_amount = int(item_amount)
        bulk_per_item = float(bulk_per_item)
        item_name = item_name.lower()
        if item_name in item_dict.keys():
            await ctx.send(f"{item_name} has already been added.")
        else:
            new_obj = Object(name=item_name,bulk=bulk_per_item,price=worth_per_item)
            item_dict[item_name] = new_obj
            save_item_list(new_obj)
            await ctx.send(f"Added {obj_name} to item list.")
    except Exception as e:
        print(e)
        await ctx.send(f"You need to write the command as {bot.command_prefix}add <item amount> <item's name> <bulk per item> <price per item>")

@bot.command(name="take")
async def take_item(ctx, item_amount, item_name):
    """
    Removes <item amount> times of <item name> from your inventory.
    """
    try:
        item_amount = int(item_amount)
        if not is_added_user(ctx.author):
            await ctx.send(f"Please use the {bot.command_prefix}slots first.")
        else:
            await ctx.send(take_user_item(ctx.author, item_name, item_amount))
    except Exception as e:
        print(e)
        await ctx.send(f"You need to write the command as {bot.command_prefix}take <item amount> <item name>")

@bot.command(name="add")
async def give_item(ctx, item_amount, item_name):
    """
    Adds <item amount> times of <item name> to your inventory.
    """
    try:
        item_amount = int(item_amount)
        if not is_added_user(ctx.author):
            await ctx.send(f"Please use the {bot.command_prefix}slots first.")
        else:
            await ctx.send(give_user_object(ctx.author, item_name, item_amount))
    except Exception as e:
        print(e)
        await ctx.send(f"You need to write the command as {bot.command_prefix}add <item amount> <item name>")

@bot.command(name="show")
async def send_inventory(ctx):
    """
    Shows your inventory.
    """
    try:
        if not is_added_user(ctx.author):
            await ctx.send(f"Please use the {bot.command_prefix}slots first.")
        else:
            await ctx.send(print_user_inventory(ctx.author))
    except Exception as e:
        print(e)
        await ctx.send(f"You need to write the command as {bot.command_prefix}show")

@bot.command(name="search")
async def search_for_item(ctx, query):
    """
    Searches for item in item list for <query>.
    """
    def levenshtein(a, b):
        if not a: return len(b)
        if not b: return len(a)
        return min(levenshtein(a[1:], b[1:])+(a[0] != b[0]),
                   levenshtein(a[1:], b)+1,
                   levenshtein(a, b[1:])+1)
    try:
        search_distance = lambda x : levenshtein(x.lower(),query.lower())
        search_results = sorted(item_dict.keys(),key=search_distance)[:5]
        await ctx.send('\n'.join(search_results))
    except Exception as e:
        print(e)
        await ctx.send(f"You need to write the command as {bot.command_prefix}search <search term>")
