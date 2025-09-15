import discord
from discord.ext import commands

# Add error handling for imports
try:
    from gamemanager import gamemanager

    print("✓ gamemanager imported successfully")
except Exception as e:
    print(f"✗ Error importing gamemanager: {e}")
    gamemanager = None

try:
    from ai import ai

    print("✓ ai imported successfully")
except Exception as e:
    print(f"✗ Error importing ai: {e}")
    ai = None


class ImitationBot(commands.Bot):
    def __init__(self, gemini_api_key):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='!', intents=intents)

        # Initialize with error handling
        if gamemanager:
            self.game_manager = gamemanager(self)
            print("✓ gamemanager initialized")
        else:
            self.game_manager = None
            print("✗ gamemanager not available")

        if ai:
            self.ai_handler = ai(gemini_api_key)
            print("✓ ai handler initialized")
        else:
            self.ai_handler = None
            print("✗ ai handler not available")

        # Register commands manually to ensure they're added
        self.add_commands()

    def add_commands(self):
        """Manually add commands to ensure they're registered"""

        @self.command(name='join')
        async def join_game(ctx):
            """Join the game queue"""
            print(f"Join command called by {ctx.author}")
            if self.game_manager:
                await self.game_manager.add_player(ctx)
            else:
                await ctx.send("Game manager not available - check console for errors")

        @self.command(name='start')
        async def start_turing_test(ctx):
            """Start a Turing Test game"""
            print(f"Start command called by {ctx.author}")
            if self.game_manager:
                await self.game_manager.start_game(ctx)
            else:
                await ctx.send("Game manager not available - check console for errors")

        @self.command(name='ask')
        async def ask_question(ctx, player=None, *, question=None):
            """Ask a question to player A or B"""
            if not player or not question:
                await ctx.send("Usage: `!ask a your question` or `!ask b your question`")
                return

            print(f"Ask command called by {ctx.author}: {player} - {question}")
            if self.game_manager:
                await self.game_manager.handle_question(ctx, player, question)
            else:
                await ctx.send("Game manager not available - check console for errors")

        @self.command(name='test')
        async def test_command(ctx):
            """Simple test command"""
            await ctx.send("Test command working! 🎉")

        print("Commands registered manually")

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

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Registered commands: {[cmd.name for cmd in self.commands]}')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            print(f"Command not found: {ctx.message.content}")
            available_commands = ', '.join([f'!{cmd.name}' for cmd in self.commands])
            await ctx.send(f"Command not found. Available commands: {available_commands}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Use `!help {ctx.command.name}` for usage.")
        else:
            print(f"Command error: {error}")
            await ctx.send(f"An error occurred: {error}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f"Message received: {message.content} from {message.author}")

        # Handle DM responses from human players
        if isinstance(message.channel, discord.DMChannel):
            if self.game_manager and await self.game_manager.handle_dm_response(message):
                return

        await self.process_commands(message)