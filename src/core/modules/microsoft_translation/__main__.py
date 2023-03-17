from sys import argv

from . import MicrosoftTranslator

TOKEN = argv[1]


import asyncio


async def main():
    translator = MicrosoftTranslator(TOKEN)
    try:
        print(await translator.translate(["Il like cheese", "I want to a chewing-gum"], "fr-CA"))
    finally:
        await translator.close()


asyncio.run(main())
