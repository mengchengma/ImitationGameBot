import os
from dotenv import load_dotenv
from bot import ImitationBot


def main():
    load_dotenv()

    discord_token = os.getenv('DISCORD_TOKEN')
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not discord_token or not gemini_api_key:
        print("Missing required environment variables!")
        return

    bot = ImitationBot(gemini_api_key)
    bot.run(discord_token)


if __name__ == "__main__":
    main()