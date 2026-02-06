import random

class BoxingGame:
    def __init__(self):
        self.moves = {
            "jab": {"beats": "cross", "loses_to": "block", "emoji": "🥊"},
            "cross": {"beats": "block", "loses_to": "jab", "emoji": "💥"},
            "block": {"beats": "jab", "loses_to": "cross", "emoji": "🛡"}
        }

    def get_bot_move(self):
        """Randomly selects a move for the bot."""
        return random.choice(list(self.moves.keys()))

    def get_result(self, player_move, bot_move):
        """
        Determines the winner.
        Returns: 'win', 'lose', or 'draw'
        """
        if player_move == bot_move:
            return "draw"
        
        if self.moves[player_move]["beats"] == bot_move:
            return "win"
        
        return "lose"

    def format_result_message(self, player_move, bot_move, result):
        """Returns a stylish result message."""
        p_emoji = self.moves[player_move]["emoji"]
        b_emoji = self.moves[bot_move]["emoji"]
        
        msg = f"<b>Siz:</b> {p_emoji}  🆚  {b_emoji} <b>Bot</b>\n\n"
        
        if result == "win":
            msg += "🏆 <b>G'ALABA!</b> Siz kuchli zarba berdingiz!"
        elif result == "lose":
            msg += "💀 <b>MAG'LUBIYAT...</b> Bot sizni nokaut qildi!"
        else:
            msg += "🤝 <b>DURANG!</b> Ikkala tomon ham teng keldi."
            
        return msg
