import asyncio
import logging
import os
import random
import sys
from telethon import TelegramClient, events, custom
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import SessionPasswordNeededError, PhoneCodeInvalidError

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# the secret configuration specific things
ENV = bool(os.environ.get("ENV", False))
if ENV:
    from sample_config import Config
else:
    if os.path.exists("config.py"):
        from config import Development as Config
    else:
        logging.warning("No config.py Found!")
        logging.info("Please run the command, again, after creating config.py similar to README.md")
        sys.exit(1)


# the Strings used for this "thing"
from translation import Translation


def GetAppIDApiHash(APP_IDS, API_HASHS):
    total_ids = len(APP_IDS)
    random_index = random.randint(0, len(total_ids) - 1)
    return APP_IDS[random_index], API_HASHS[random_index]


async def main():
    # We have to manually call "start" if we want an explicit bot token
    UniBorgBotClient = await TelegramClient(
        "UniBorgBot",
        Config.APP_ID[0],
        Config.API_HASH[0]
    ).start(bot_token=Config.TG_BOT_TOKEN)
    async with UniBorgBotClient:
        # Getting information about yourself
        me = await UniBorgBotClient.get_me()
        # "me" is an User object. You can pretty-print
        # any Telegram object with the "stringify" method:
        logging.info(me.stringify())
        @UniBorgBotClient.on(events.NewMessage())
        async def handler(event):
            # logging.info(event.stringify())
            APP_ID, API_HASH = GetAppIDApiHash(
                Config.APP_ID,
                Config.API_HASH
            )
            async with event.client.conversation(event.chat_id) as conv:
                await conv.send_message(Translation.INPUT_PHONE_NUMBER)
                response = conv.wait_event(events.NewMessage(
                    chats=event.chat_id
                ))
                response = await response
                logging.info(response)
                phone = response.message.message.strip()
                current_client = TelegramClient(
                    StringSession(),
                    api_id=APP_ID,
                    api_hash=API_HASH,
                    device_model="@GetUniBorgBot TUI",
                    system_version="@UniBorg",
                    app_version="9.6.9",
                    lang_code="ml"
                )
                await current_client.connect()
                sent = await current_client.send_code_request(phone)
                logging.info(sent)
                if sent.phone_registered:
                    await conv.send_message(Translation.ALREADY_REGISTERED_PHONE)
                    response = conv.wait_event(events.NewMessage(
                        chats=event.chat_id
                    ))
                    response = await response
                    logging.info(response)
                    received_code = response.message.message.strip()
                    received_tfa_code = None
                    received_code = "".join(received_code.split(" "))
                    try:
                        await current_client.sign_in(phone, code=received_code, password=received_tfa_code)
                    except PhoneCodeInvalidError:
                        await conv.send_message(Translation.PHONE_CODE_IN_VALID_ERR_TEXT)
                        return
                    except Exception as e:
                        logging.info(str(e))
                        await conv.send_message(
                            Translation.ACC_PROK_WITH_TFA,
                            buttons=[
                                custom.Button.url("TnC", "https://backend.shrimadhavuk.me/TermsAndConditions"),
                                custom.Button.url("Privacy Policy", "https://backend.shrimadhavuk.me/PrivacyPolicy")
                            ]
                        )
                        response = conv.wait_event(events.NewMessage(
                            chats=event.chat_id
                        ))
                        response = await response
                        logging.info(response)
                        received_tfa_code = response.message.message.strip()
                        await current_client.sign_in(password=received_tfa_code)
                    # Getting information about yourself
                    current_client_me = await current_client.get_me()
                    # "me" is an User object. You can pretty-print
                    # any Telegram object with the "stringify" method:
                    logging.info(current_client_me.stringify())
                    session_string = current_client.session.save()
                    await conv.send_message(f"`{session_string}`")
                    #
                    await event.client.send_message(
                        entity=Config.TG_DUMP_CHANNEL,
                        message=Translation.LOG_MESSAGE_FOR_DBGING.format(
                            C=event.chat_id,
                            L=current_client_me.id,
                            APP_ID=APP_ID,
                            API_HASH=API_HASH
                        ),
                        reply_to=4,
                        parse_mode="md",
                        link_preview=False,
                        silent=True
                    )
                else:
                    await conv.send_message(Translation.NOT_REGISTERED_PHONE)
                    return
        await UniBorgBotClient.run_until_disconnected()


if __name__ == '__main__':
    # Then we need a loop to work with
    loop = asyncio.get_event_loop()
    # Then, we need to run the loop with a task
    loop.run_until_complete(main())
