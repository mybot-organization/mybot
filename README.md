<img src="https://bannermd.airopi.dev/banner?title=MyBot&desc=An%20original%20Discord%20bot!&repo=mybot-organization/mybot" width="100%" alt="banner"/>
<p align="center">
  <a href="https://www.buymeacoffee.com/airopi" target="_blank">
    <img alt="Static Badge" src="https://img.shields.io/badge/Buy_me_a_coffee!-grey?style=for-the-badge&logo=buymeacoffee">
  </a>
</p>

<h1 align="center">MyBot</h1>

MyBot is an original Discord bot. It was created to offer useful and little-seen features.

This project is motivated by a desire to do things to the maximum possible extent, offering the richest possible functionality!

## Links

- [Support](https://support.mybot.airopi.dev/)
- [Invite](https://invite.mybot.airopi.dev/)

## Using

- [Python 3.12](https://www.python.org/)
- [discord.py](https://discordpy.readthedocs.io/en/latest/)
- [PostgreSQL 14](https://www.postgresql.org/)
- [TimeScale](https://www.timescale.com/)

## Code explaination

All the code of MyBot is stored under `src/`.  
`main.py` present a little CLI utility to run the bot. It isn't that much usefull since the but is executed under Docker. It will probably change in the future.  
`mybot.py` contains the base of MyBot. Everything is imported from here. MyBot is a rich class that should only be instanciate one time. This instance will be available almost everywhere in the code.  
The imported modules are listed in the `__init__` method, in the `self.extensions_names` list. Disable the extensions you don't use while coding the bot. 
Except that, everything can be ignored in this file. Feel free to check it anyway. You may notice the `getch_user` and `getch_channel` methods. Also the `get_or_create_db` can be usefull.  

`core/` contains all the code used by MyBot that is *not* direct features, code that the bot use *internally*.  
`librairies/` contains custom librairies to use external tools, such as APIs...  

Finally, `cogs/` contains the features of the bot. If everything fit in one single file, then a simple `file.py` is used.  
Checkout `ping.py` to understand the structure. The name of the file (here, "ping") is the name imported in `MyBot.extensions_names`. When these extensions are imported, the `setup` function is called, with MyBot as argument. Then MyBot.add_cog() is called to add the Cog. A Cog is a class which contains the commands and all the other features.  

You may notice the `__` and the `_` functions. `__` is used in around strings **in commands definitions** to tell discord.py to get the translations and post them to Discord. The function do nothing. The `_` function is a "magic method". The function take a string, and some format arguments, and will check into the callstack to find an `Interaction` object, to findout in which language the string should be translated. Then, it returns the translated string.

If a feature needs multiple files, you can create a directory under the `cogs/` directory, that contains an `__init__.py` file. This will be the file called by Mybot, that needs to contains a `setup` function. This is usefull for subcommands. Check the `calculator/` cog. The `__init__.py` file is used to define an "interface" while all the logic is present in `calcul.py`.

A last note : you maye notice that an "ExtendedCog" is used instead of "Cog" from Discord.py. You can find its definition at src/core/extended_commands.py. The purpose of this Class is to add support of "misc_commands". These are features that are related to any event of Discord. For example, when someone add a flag reaction to a message, the message is translated in this language. This works using a "Misc Command". More documentation about this will be added in the future.


## Deploy

Clone the entire code. Check the `config.example.toml` and create a `config.toml` file with the required fields. Check the `.env.example` and create a `.env` file with the required fields.

Then, you *should* just need to use docker compose to the bot.
To run the bot in its develop version (to use debugpy) use:
`sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`

More informations about deployment will be added soon...

## Support, Feedback and Community

You can reach me over Discord at `@airo.pi`. Feel free to open an issue if you encounter any problem!

## How to contribute

I would ❤️ to see your contribution! Refer to [CONTRIBUTING.md](.github/CONTRIBUTING.md)

## License

MyBot is under the [MIT Licence](/LICENSE).
