from Evie import tbot, BOT_ID, OWNER_ID
from telethon import events, functions, Button
import telethon
from Evie.function import is_admin

@tbot.on(events.NewMessage(pattern=None))
async def handler(event):
        if await is_admin(event, event.sender_id):
             return
        if not event.sender_id == BOT_ID:
         if not event.sender_id == OWNER_ID:
           chat = int(-1001309757591)
           rip = await check_him(chat, 'lunabotnews', event.sender_id)
           if rip is False:
             await event.reply(
                "**To Talk in this Chat, Please Join My Channel. :)**",
                buttons=[Button.url("Join Channel", 't.me/lunabotnews')],
            )
             return
           else:
             pass





async def check_him(chnnl_id, chnnl_link, starkuser):
    try:
        result = await tbot(
            functions.channels.GetParticipantRequest(
                channel=chnnl_id, user_id=starkuser
            )
        )
        return True
    except telethon.errors.rpcerrorlist.UserNotParticipantError:
        return False
