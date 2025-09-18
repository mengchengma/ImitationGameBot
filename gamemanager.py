import asyncio
import random
import discord

class GameSession:
    def __init__(self, channel, interrogator):
        self.channel = channel
        self.interrogator = interrogator
        self.players = {}  # keys: 'a', 'b' -> either discord.Member or 'AI'
        self.game_active = False
        self.human_player = None
        self.questions_asked = 0
        self.max_questions = 6


class gamemanager:
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # channel.id -> GameSession
        self.waiting_players = []  # list of discord.Member

    async def add_player(self, ctx):
        # Check by user ID instead of user object
        player_ids = [player.id for player in self.waiting_players]

        if ctx.author.id not in player_ids:
            self.waiting_players.append(ctx.author)
            await ctx.send(f"{ctx.author.mention} added to queue. Players waiting: {len(self.waiting_players)}")
        else:
            await ctx.send("You're already in the queue!")

    async def start_game(self, ctx):
        # Need at least one other player besides the interrogator
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
        await session.channel.send(
            "**Game Started!** One of Player A or Player B is an AI. Ask questions to figure out which!\n\n"
            "**How to play:** Type `!ask your question` to ask the same question to both players (or `!ask a your question` / `!ask b your question` to target a specific player).\n"
            "You have 6 questions, then use `!guess a` or `!guess b`"
        )

        # DM instructions to the interrogator
        try:
            await session.interrogator.send(
                "You are the **Interrogator**. Use `!ask question` to ask the same question to both players. You can also target a specific player with `!ask a question` or `!ask b question`.\n"
                "After 6 questions, use `!guess a` or `!guess b` to make your final choice!"
            )
        except Exception:
            pass

        # Find human player label and DM them
        human_label = 'A' if session.players['a'] != 'AI' else 'B'
        try:
            await session.human_player.send(f"You are **Player {human_label}**. Respond naturally when questioned!")
        except Exception:
            pass

        session.game_active = True

    async def handle_question(self, ctx, player, question):
        if ctx.channel.id not in self.active_games:
            await ctx.send("No active game in this channel!")
            return

        session = self.active_games[ctx.channel.id]

        if ctx.author.id != session.interrogator.id:
            await ctx.send("Only the interrogator can ask questions!")
            return

        if session.questions_asked >= session.max_questions:
            await ctx.send(f"You've already asked {session.max_questions} questions! Use `!guess a` or `!guess b` to make your final choice!")
            return

        # Determine targets: None/empty means broadcast to both players
        if not player:
            targets = ['a', 'b']
        else:
            player = player.lower()
            if player not in ['a', 'b']:
                await ctx.send("Usage: `!ask question` or `!ask a question` / `!ask b question`")
                return
            targets = [player]

        # Count this as one question regardless of how many targets
        session.questions_asked += 1
        remaining = session.max_questions - session.questions_asked

        # Send to each target then AI will respond, humans will receive a DM to reply
        for t in targets:
            target_obj = session.players[t]
            if target_obj == 'AI':
                try:
                    response = await self.bot.ai_handler.get_response(question)
                except Exception as e:
                    response = "(AI failed to respond)"
                    print(f"AI error when answering question: {e}")

                await self.send_response(session, t.upper(), response)
            else:
                # Human response via DM
                try:
                    await target_obj.send(f"**Question:** {question}\nReply to this DM with your answer!")
                except Exception as e:
                    print(f"Failed to DM human player: {e}")

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

        end_msg = (
            f"**Game Ended**\nThe game was ended early.\n\n**Reveal:**\nPlayer {ai_player.upper()}: AI\n"
            f"Player {human_player.upper()}: {session.human_player.mention}\n**Questions asked:** {session.questions_asked}/{session.max_questions}"
        )

        await ctx.send(end_msg)
        del self.active_games[ctx.channel.id]

    async def handle_dm_response(self, message):
        # Find which game this human is part of
        for session in self.active_games.values():
            if session.human_player and message.author.id == session.human_player.id:
                label = 'A' if session.players['a'] == message.author else 'B'
                await self.send_response(session, label, message.content)
                return True
        return False