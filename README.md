# TADA Telegram Bot
 A simple bot for the Telegram Art Display Action (TADA). 
 
## Setup
This project requires Python 3.10+ and pip 22.0+
1. `git clone git@github.com:Amustache/TADA-Telegram-Bot.git`
2. `cd TADA-Telegram-Bot`
3. `python -m venv env`
4. `source env/bin/activate`
5. `pip install -r requirements.txt`
6. `cp secret.dist.py secret.py`
7. Edit `secret.py`:
   * `TOKEN`: Your Telegram bot token
   * `ADMINS_IDS`: Telegram ID of the people that should be able to vote on the bot
   * `ADMINS_GROUPCHAT`: Telegram ID of the groupchat in which messages will be forwarded 
   * `DUMP_GROUPCHAT`: Telegram ID of the channel in which submissions will be dumped
   * `BASE_URL`: Local webserver to access submissions

## Usage
