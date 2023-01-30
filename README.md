# TADA Telegram Bot
 A simple bot for the Telegram Art Display Action (TADA). 
 
## Setup
This project requires Python 3.10+, pip 22.0+, and a Postgres DB
1. `git clone git@github.com:Amustache/TADA-Telegram-Bot.git`
2. `cd TADA-Telegram-Bot`
3. `python -m venv env`
4. `source env/bin/activate`
5. `pip install -r requirements.txt`
6. `cp secret.dist.py secret.py`
7. Edit `secret.py`:
   * `TOKEN`: Your Telegram bot token
   * `ADMINS_GROUPCHAT`: Telegram ID of the groupchat in which messages will be forwarded 
   * `DUMP_GROUPCHAT`: Telegram ID of the channel in which submissions will be dumped
   * `DB_DB`: Name of the database
   * `DB_USER`: Username to authenticate with the database
   * `DB_PW`: Password to authenticate with the database
   * `DB_HOST`: URL of the database
   * `DB_PORT`: Port of the database

## Usage
run the bot with `python main.py`