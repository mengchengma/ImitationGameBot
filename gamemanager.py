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
        self.questions_asked = 0
        self.max_questions = 6


class gamemanager:
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.waiting_players = []

    async def add_player(self, ctx):
        # Check by user ID instead of user object
        player_ids = [player.id for player in self.waiting_players]

        if ctx.author.id not in player_ids:
            self.waiting_players.append(ctx.author)
            await ctx.send(f"{ctx.author.mention} added to queue. Players waiting: {len(self.waiting_players)}")
        else:
            await ctx.send("You're already in the queue!")

    async def start_game(self, ctx):
        if len(self.waiting_players) < 1:
            await ctx.send("Need at least 1 other player. Use `!join` to join the queue.")
            return

        interrogator = ctx.author

        if interrogator in self.waiting_players:
            self.waiting_players.remove(interrogator)

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
        await session.channel.send("**Game Started!** One of Player A or Player B is an AI. Ask questions to figure out which!\n\n**How to play:** Type `!ask a your question` or `!ask b your question`\nYou have 6 questions, then use `!guess a` or `!guess b`")

        # DM instructions
        await session.interrogator.send(
            "You are the **Interrogator**. Use `!ask a question` or `!ask b question` to ask questions.\nAfter 6 questions, use `!guess a` or `!guess b` to make your final choice!")

        # Find human player label
        human_label = 'A' if session.players['a'] != 'AI' else 'B'
        await session.human_player.send(f"You are **Player {human_label}**. Respond naturally when questioned!")

        session.game_active = True

    async def handle_question(self, ctx, player, question):
        session = self.active_games[ctx.channel.id]

        if ctx.author.id != session.interrogator.id:
            await ctx.send("Only the interrogator can ask questions!")
            return

        if session.questions_asked >= session.max_questions:
            await ctx.send(f"You've already asked {session.max_questions} questions! Use `!guess a` or `!guess b` to make your final choice!")
            return

        player = player.lower()
        if player not in ['a', 'b']:
            await ctx.send("Use `!ask a question` or `!ask b question`")
            return

        session.questions_asked += 1
        remaining = session.max_questions - session.questions_asked

        target = session.players[player]

        if target == 'AI':
            # AI response
            response = await self.bot.ai_handler.get_response(question)
            await self.send_response(session, player.upper(), response)
        else:
            # Human response
            await target.send(f"**Question:** {question}\nReply to this DM with your answer!")

        if remaining > 0:
            await ctx.send(f"Questions remaining: {remaining}")
        else:
            await ctx.send("That was your final question! Use `!guess a` or `!guess b` to make your choice!")

    async def send_response(self, session, player_label, response):
        # Add delay to seem more human
        delay = random.uniform(2.0, 4.0)
        await asyncio.sleep(delay)

        await session.channel.send(f"**Player {player_label}:** {response}")

    async def handle_guess(self, ctx, guess):
        if ctx.channel.id not in self.active_games:
            await ctx.send("No active game in this channel!")
            return

        session = self.active_games[ctx.channel.id]

        if ctx.author.id != session.interrogator.id:
            await ctx.send("Only the interrogator can make the guess!")
            return

        if session.questions_asked < session.max_questions:
            await ctx.send(f"You still have {session.max_questions - session.questions_asked} questions left! Ask more or use `!guess` anyway.")

        guess = guess.lower()
        if guess not in ['a', 'b']:
            await ctx.send("Use `!guess a` or `!guess b`")
            return

        # Determine who was the AI
        ai_player = 'a' if session.players['a'] == 'AI' else 'b'
        human_player = 'a' if ai_player == 'b' else 'b'

        # Create result message
        if guess == ai_player:
            result_msg = f"**Correct!** Player {guess.upper()} was indeed the AI!"
        else:
            result_msg = f"**Wrong!** Player {guess.upper()} was human. Player {ai_player.upper()} was the AI!"

        result_msg += f"\n\n**Results:**\nPlayer {ai_player.upper()}: AI\nPlayer {human_player.upper()}: {session.human_player.mention}\n"

        await ctx.send(result_msg)

        # End the game
        del self.active_games[ctx.channel.id]

    async def end_game(self, ctx):
        if ctx.channel.id not in self.active_games:
            await ctx.send("No active game in this channel!")
            return

        session = self.active_games[ctx.channel.id]

        if ctx.author.id != session.interrogator.id:
            await ctx.send("Only the interrogator can end the game!")
            return

        # Reveal the answer
        ai_player = 'a' if session.players['a'] == 'AI' else 'b'
        human_player = 'a' if ai_player == 'b' else 'b'

        end_msg = f"**Game Ended**\nThe game was ended early.\n\n**Reveal:**\nPlayer {ai_player.upper()}: AI\nPlayer {human_player.upper()}: {session.human_player.mention}\n**Questions asked:** {session.questions_asked}/{session.max_questions}"

        await ctx.send(end_msg)
        del self.active_games[ctx.channel.id]

    async def handle_dm_response(self, message):
        # Find which game this human is part of
        for session in self.active_games.values():
            if message.author.id == session.human_player.id:
                label = 'A' if session.players['a'] == message.author else 'B'
                await self.send_response(session, label, message.content)
                return True
        return False