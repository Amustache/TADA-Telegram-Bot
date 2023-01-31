# TADA Telegram Bot
A simple bot for the Telegram Art Display Action (TADA).

More information [here](https://github.com/Amustache/TADA-Telegram-Bot/wiki).
 
## Setup
This project requires Python 3.10+ and pip 22.0+.
1. `git clone git@github.com:Amustache/TADA-Telegram-Bot.git`
2. `cd TADA-Telegram-Bot`
3. `python -m venv env`
4. `source env/bin/activate`
5. `pip install -r requirements.txt`
6. `cp secret.dist.py secret.py`
7. Edit `secret.py`:
   * `TOKEN`: Your Telegram bot token.
   * `ADMINS_GROUPCHAT`: Telegram ID of the groupchat in which messages will be forwarded. 
   * `DUMP_GROUPCHAT`: Telegram ID of the channel in which submissions will be dumped.
   * For Sqlite:
     * `DB_FILENAME`: Path to the database.
   * For Postgresql (you will need a Postgres DB):
     * `DB_DB`: Name of the database.
     * `DB_USER`: Username to authenticate with the database.
     * `DB_PW`: Password to authenticate with the database.
     * `DB_HOST`: URL of the database.
     * `DB_PORT`: Port of the database.

## Usage
* Run the bot with `python main.py`.
* Start a new contest for the current year using `/new`.
* Add a new theme for the current contest using `/theme <your theme>`.
* Add a new admin by replying to an admin message in the `ADMINS_GROUPCHAT` using `/admin`.
* Create a new notification for all people using the bot using `/notify`.
* People can send messages to the bot, the messages will be forwarded in the `ADMINS_GROUPCHAT`.
