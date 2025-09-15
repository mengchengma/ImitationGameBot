import google.generativeai as genai
import random


class ai:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.system_prompt = """
        You are playing the Turing Test. Act like a normal human in casual conversation.

        Instructions:
        - Use casual, conversational language
        - Make occasional typos or informal grammar
        - Keep responses short (1-3 sentences)
        - Show personality and opinions

        You're a 22-year-old college student studying computer science.
        You like video games, movies, and hanging out with friends.
        """

    async def get_response(self, question):
        try:
            full_prompt = f"{self.system_prompt}\n\nQuestion: {question}\n\nResponse:"
            response = self.model.generate_content(full_prompt)
            text = response.text

            # Add human-like touches
            if random.random() < 0.3:
                text = text.lower()

            return text

        except Exception as e:
            print(f"AI Error: {e}")
            return "sorry, can you repeat that?"