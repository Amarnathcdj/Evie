from Evie import tbot, CMD_HELP
import os, re, csv, json, time, uuid
from Evie.function import is_admin
from io import BytesIO
import Evie.modules.sql.feds_sql as sql
from telethon import *
from telethon import Button
from telethon.tl import *
from telethon.tl.types import User
from Evie import *
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename
from Evie.events import register


async def get_user_from_event(event):
    """ Get the user from argument or replied message. """
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        user_obj = await tbot.get_entity(previous_message.sender_id)
        fname = previous_message.sender.first_name
    else:
        user = event.pattern_match.group(1)

        if user.isnumeric():
            user = int(user)

        if not user:
            await event.reply("Pass the user's username, id or reply!")
            return

        try:
            user_obj = await tbot.get_entity(user)
        except (TypeError, ValueError) as err:
            await event.reply(str(err))
            return None

    return user_obj

def is_user_fed_owner(fed_id, user_id):
    getsql = sql.get_fed_info(fed_id)
    if getsql is False:
        return False
    getfedowner = eval(getsql["fusers"])
    if getfedowner is None or getfedowner is False:
        return False
    getfedowner = getfedowner["owner"]
    if str(user_id) == getfedowner or int(user_id) == OWNER_ID:
        return True
    else:
        return False


@register(pattern="^/newfed ?(.*)")
async def new(event):
 if not event.is_private:
  return await event.reply("Create your federation in my PM - not in a group.")
 name = event.pattern_match.group(1)
 fedowner = sql.get_user_owner_fed_full(event.sender_id)
 if fedowner:
    for f in fedowner:
            text = "{}".format(f["fed"]["fname"])
    return await event.reply(f"You already have a federation called `{text}` ; you can't create another. If you would like to rename it, use /renamefed.")
 if not name:
  return await event.reply("You need to give your federation a name! Federation names can be up to 64 characters long.")
 if len(name) > 64:
  return await event.reply("Federation names can only be upto 64 charactors long.")
 fed_id = str(uuid.uuid4())
 fed_name = name
 x = sql.new_fed(event.sender_id, fed_name, fed_id)
 return await event.reply(f"Created new federation with FedID: `{fed_id}`.\nUse this ID to join the federation! eg:\n`/joinfed {fed_id}`")

@register(pattern="^/delfed")
async def smexy(event):
 if not event.is_private:
  return await event.reply("Delete your federation in my PM - not in a group.")
 fedowner = sql.get_user_owner_fed_full(event.sender_id)
 if not fedowner:
  return await event.reply("It doesn't look like you have a federation yet!")
 for f in fedowner:
            fed_id = "{}".format(f["fed_id"])
            name = f["fed"]["fname"]
 await tbot.send_message(
            event.chat_id,
            "Are you sure you want to delete your federation? This action cannot be undone - you will lose your entire ban list, and '{}' will be permanently gone.".format(name),
            buttons=[
                [Button.inline("Delete Federation", data="rmfed_{}".format(fed_id))],
                [Button.inline("Cancel", data="nada")],
            ],
        )

@tbot.on(events.CallbackQuery(pattern=r"rmfed(\_(.*))"))
async def delete_fed(event):
    tata = event.pattern_match.group(1)
    data = tata.decode()
    fed_id = data.split("_", 1)[1]
    delete = sql.del_fed(fed_id)
    await event.edit("You have deleted your federation! All chats linked to it are now federation-less.")

@tbot.on(events.CallbackQuery(pattern=r"nada"))
async def delete_fed(event):
  await event.edit("Federation deletion canceled")

@register(pattern="^/renamefed ?(.*)")
async def cgname(event):
 if not event.is_private:
   return await event.reply("You can only rename your fed in PM.")
 user_id = event.sender_id
 newname = event.pattern_match.group(1)
 fedowner = sql.get_user_owner_fed_full(event.sender_id)
 if not fedowner:
  return await event.reply("It doesn't look like you have a federation yet!")
 if not newname:
  return await event.reply("You need to give your federation a new name! Federation names can be up to 64 characters long.")
 for f in fedowner:
            fed_id = f["fed_id"]
            name = f["fed"]["fname"]
 sql.rename_fed(fed_id, user_id, newname)
 return await event.reply(f"Tada! I've renamed your federation from '{name}' to '{newname}'. [FedID: `{fed_id}`].")

@register(pattern="^/chatfed")
async def cf(event):
 chat = event.chat_id
 if event.is_private:
   return
 if not await is_admin(event, event.sender_id):
   return await event.reply("You need to be an admin to do this.")
 fed_id = sql.get_fed_id(chat)
 if not fed_id:
  return await event.reply("This chat isn't part of any feds yet!")
 info = sql.get_fed_info(fed_id)
 name = info["fname"]
 await event.reply(f"Chat {event.chat.title} is part of the following federation: {name} [ID: `{fed_id}`]")
 
@register(pattern="^/joinfed ?(.*)")
async def jf(event):
 if not event.is_group:
   return
 if not await is_admin(event, event.sender_id):
   await event.reply("You need to be an admin to do this.")
   return
 permissions = await tbot.get_permissions(event.chat_id, event.sender_id)
 if not permissions.is_creator:
          return await event.reply(f"You need to be the chat owner of {event.chat.title} to do this.")
 args = event.pattern_match.group(1)
 if not args:
   return await event.reply("You need to specify which federation you're asking about by giving me a FedID!")
 if len(args) < 8:
   return await event.reply("This isn't a valid FedID format!")
 getfed = sql.search_fed_by_id(args)
 name = getfed["fname"]
 if not getfed:
  return await event.reply("This FedID does not refer to an existing federation.")
 fed_id = sql.get_fed_id(event.chat_id)
 if fed_id:
    sql.chat_leave_fed(event.chat_id)
 x = sql.chat_join_fed(args, event.chat.title, event.chat_id)
 return await event.reply(f'Successfully joined the "{name}" federation! All new federation bans will now also remove the members from this chat.')
 
@register(pattern="^/leavefed")
async def lf(event):
 if not event.is_group:
   return
 if not await is_admin(event, event.sender_id):
   await event.reply("You need to be an admin to do this.")
   return
 permissions = await tbot.get_permissions(event.chat_id, event.sender_id)
 if not permissions.is_creator:
          return await event.reply(f"You need to be the chat owner of {event.chat.title} to do this.")
 chat = event.chat_id
 fed_id = sql.get_fed_id(chat)
 if not fed_id:
   return await event.reply("This chat isn't currently in any federations!")
 fed_info = sql.get_fed_info(fed_id)
 name = fed_info["fname"]
 sql.chat_leave_fed(chat)
 return await event.reply(f'Chat {event.chat.title} has left the " {name} " federation.')

@register(pattern="^/fpromote ?(.*)")
async def p(event):
 if event.is_private:
  return await event.reply("This command is made to be run in a group where the person you would like to promote is present.")
 fedowner = sql.get_user_owner_fed_full(event.sender_id)
 if not fedowner:
   return await event.reply("Only federation creators can promote people, and you don't seem to have a federation to promote to!")
 args = await get_user_from_event(event)
 if not args:
   return await event.reply("I don't know who you're talking about, you're going to need to specify a user...!")
 chat = event.chat
 for f in fedowner:
            fed_id = f["fed_id"]
            name = f["fed"]["fname"]
 user_id = args.id
 replied_user = await tbot(GetFullUserRequest(user_id))
 fname = replied_user.user.first_name
 getuser = sql.search_user_in_fed(fed_id, user_id)
 if getuser:
   return await event.reply(f"[{fname}](tg://user?id={args.id}) is already an admin in {name}!")
 await tbot.send_message(
            event.chat_id,
            f"Please get {fname} to confirm that they would like to be fed admin for {name}",
            buttons=[
                Button.inline("Confirm", data="fkfed_{}".format(user_id)),
                Button.inline("Cancel", data="smex_{}".format(user_id)),
            ],
        )
            