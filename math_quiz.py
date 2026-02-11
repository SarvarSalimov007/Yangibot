import random

class MathQuiz:
    def __init__(self):
        self.operators = ['+', '-', '*', '/']

    def generate_question(self):
        """
        Generates a random math question and 3 options.
        Returns: (question_text, options, correct_answer)
        """
        op = random.choice(self.operators)
        if op == '*':
            num1 = random.randint(2, 12)
            num2 = random.randint(2, 12)
            correct = num1 * num2
        elif op == '/':
            num2 = random.randint(2, 10)
            correct = random.randint(2, 12)
            num1 = num2 * correct # Ensure integer result
        elif op == '+':
            num1 = random.randint(10, 100)
            num2 = random.randint(10, 100)
            correct = num1 + num2
        else: # subtraction
            num1 = random.randint(10, 100)
            num2 = random.randint(10, 100)
            if num1 < num2: num1, num2 = num2, num1
            correct = num1 - num2

        question = f"{num1} {op if op != '/' else ':'} {num2} = ?"
        
        # Generate 2 wrong answers
        wrong_offsets = [-2, -1, 1, 2, 5, 10, -5, -10]
        random.shuffle(wrong_offsets)
        
        wrong1 = correct + wrong_offsets[0]
        wrong2 = correct + wrong_offsets[1]
        
        # Ensure they are natural numbers and unique
        if wrong1 <= 0: wrong1 = correct + 3
        if wrong2 <= 0 or wrong2 == wrong1: wrong2 = correct + 7
        
        options = [correct, wrong1, wrong2]
        random.shuffle(options)
        
        # Map labels A, B, C to values
        labels = ['A', 'B', 'C']
        labeled_options = {labels[i]: options[i] for i in range(3)}
        
        # Find which label is correct
        correct_label = [k for k, v in labeled_options.items() if v == correct][0]
        
        return question, labeled_options, correct_label
