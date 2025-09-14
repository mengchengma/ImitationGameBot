import asyncio
import random
import discord


class GameSession:
    def __init__(self, channel, interrogator):
        self.channel = channel
        self.interrogator = interrogator
        self.players = {}
        self.game_active = False
        self.human_player = None


class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.waiting_players = []

    async def add_player(self, ctx):
        if ctx.author not in self.waiting_players:
            self.waiting_players.append(ctx.author)
            await ctx.send(f"{ctx.author.mention} added to queue. Players waiting: {len(self.waiting_players)}")
        else:
            await ctx.send("You're already in the queue!")

    async def start_game(self, ctx):
        if len(self.waiting_players) < 1:
            await ctx.send("Need at least 1 other player. Use `!join` to join the queue.")
            return

        interrogator = ctx.author
        human_player = self.waiting_players.pop(0)

        session = GameSession(ctx.channel, interrogator)
        session.human_player = human_player

        # Randomly assign A/B
        if random.choice([True, False]):
            session.players['a'] = human_player
            session.players['b'] = 'AI'
        else:
            session.players['a'] = 'AI'
            session.players['b'] = human_player

        self.active_games[ctx.channel.id] = session
        await self.send_instructions(session)

    async def send_instructions(self, session):
        embed = discord.Embed(
            title="🤖 Turing Test Started!",
            description="One of Player A or Player B is an AI. Ask questions to figure out which!",
            color=0x00ff00
        )
        embed.add_field(name="How to play:", value="Type `!ask a your question` or `!ask b your question`",
                        inline=False)
        await session.channel.send(embed=embed)

        # DM instructions
        await session.interrogator.send(
            "You are the **Interrogator**. Use `!ask a question` or `!ask b question` to ask questions.")

        # Find human player label
        human_label = 'A' if session.players['a'] != 'AI' else 'B'
        await session.human_player.send(f"You are **Player {human_label}**. Respond naturally when questioned!")

        session.game_active = True

    async def handle_question(self, ctx, player, question):
        if ctx.channel.id not in self.active_games:
            await ctx.send("No active game in this channel!")
            return

        session = self.active_games[ctx.channel.id]

        if ctx.author != session.interrogator:
            await ctx.send("Only the interrogator can ask questions!")
            return

        player = player.lower()
        if player not in ['a', 'b']:
            await ctx.send("Use `!ask a question` or `!ask b question`")
            return

        target = session.players[player]

        if target == 'AI':
            # AI response
            response = await self.bot.ai_handler.get_response(question)
            await self.send_response(session, player.upper(), response)
        else:
            # Human response
            await target.send(f"**Question:** {question}\nReply to this DM with your answer!")

    async def send_response(self, session, player_label, response):
        # Add delay to seem more human
        delay = random.uniform(2.0, 6.0)
        await asyncio.sleep(delay)

        await session.channel.send(f"**Player {player_label}:** {response}")

    async def handle_dm_response(self, message):
        # Find which game this human is part of
        for session in self.active_games.values():
            if message.author == session.human_player:
                label = 'A' if session.players['a'] == message.author else 'B'
                await self.send_response(session, label, message.content)
                return True
        return False