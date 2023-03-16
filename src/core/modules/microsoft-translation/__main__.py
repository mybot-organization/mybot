from sys import argv

from . import MicrosoftTranslator

TOKEN = argv[1]


import asyncio


async def main():
    translator = MicrosoftTranslator(TOKEN)
    try:
        print(await translator.translate("J'aime vraiment le fromage", "it"))
    finally:
        await translator.close()


asyncio.run(main())
