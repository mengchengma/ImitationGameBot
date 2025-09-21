import discord
from discord.ext import commands
from gamemanager import gamemanager
from ai import ai


class ImitationBot(commands.Bot):
    def __init__(self, gemini_api_key):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='!', intents=intents)

        self.game_manager = gamemanager(self)
        self.ai_handler = ai(gemini_api_key)

        self.add_commands()

    def add_commands(self):
        @self.command(name='join')
        async def join_game(ctx):
            if self.game_manager:
                await self.game_manager.add_player(ctx)
            else:
                await ctx.send("Error")

        @self.command(name='start')
        async def start(ctx):
            if self.game_manager:
                await self.game_manager.start_game(ctx)
            else:
                await ctx.send("Error")

        @self.command(name='ask')
        async def ask_question(ctx, *args):
            """Ask a question to both players or a specific player.
            Usage:
              `!ask your question` -> asks both players
              `!ask a your question` -> asks player A only
              `!ask b your question` -> asks player B only
            """
            if len(args) == 0:
                await ctx.send("Usage: `!ask your question` or `!ask a your question` / `!ask b your question`")
                return

            # If first arg is 'a' or 'b', treat it as target
            target = None
            if args[0].lower() in ('a', 'b') and len(args) > 1:
                target = args[0].lower()
                question = ' '.join(args[1:]).strip()
            else:
                question = ' '.join(args).strip()

            if not question:
                await ctx.send("Please provide a question to ask.")
                return

            print(f"Ask command called by {ctx.author}: target={target} - {question}")
            if self.game_manager:
                await self.game_manager.handle_question(ctx, target, question)
            else:
                await ctx.send("Error")

        @self.command(name='guess')
        async def guess(ctx, player=None):
            if not player:
                await ctx.send("Usage: `!guess a` or `!guess b`")
                return


            if self.game_manager:
                await self.game_manager.handle_guess(ctx, player)
            else:
                await ctx.send("Error")

        @self.command(name='endgame')
        async def end_game(ctx):
            """End the current game"""
            if self.game_manager:
                await self.game_manager.end_game(ctx)
            else:
                await ctx.send("Error")

        @self.command(name='askai')
        async def ask_ai_command(ctx, *, question=None):
            """Ask the AI any question directly"""
            if not question:
                await ctx.send("Usage: `!askai your question`")
                return
            if not self.ai_handler:
                await ctx.send("AI handler not available.")
                return
            await ctx.send("Thinking...")
            try:
                response = await self.ai_handler.get_response(question)
                await ctx.send(response or "AI did not return a response.")
            except Exception as e:
                await ctx.send(f"AI error: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f"Message received: {message.content} from {message.author}")

        
        if isinstance(message.channel, discord.DMChannel):
            if self.game_manager and await self.game_manager.handle_dm_response(message):
                return

        await self.process_commands(message)