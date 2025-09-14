import discord
from discord.ext import commands
from game_manager import GameManager
from ai_handler import AIHandler


class ImitationBot(commands.Bot):
    def __init__(self, gemini_api_key):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='!', intents=intents)

        self.game_manager = GameManager(self)
        self.ai_handler = AIHandler(gemini_api_key)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

    @commands.command(name='join')
    async def join_game(self, ctx):
        """Join the game queue"""
        await self.game_manager.add_player(ctx)

    @commands.command(name='start')
    async def start_turing_test(self, ctx):
        """Start a Turing Test game"""
        await self.game_manager.start_game(ctx)

    @commands.command(name='ask')
    async def ask_question(self, ctx, player, *, question):
        """Ask a question to player A or B"""
        await self.game_manager.handle_question(ctx, player, question)

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Handle DM responses from human players
        if isinstance(message.channel, discord.DMChannel):
            if await self.game_manager.handle_dm_response(message):
                return

        await self.process_commands(message)