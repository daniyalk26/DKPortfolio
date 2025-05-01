from transformers import pipeline
question_answerer = pipeline("question-answering", model='distilbert-base-cased-distilled-squad')

context = r"""
I want to transfer $50, I want to transfer to 123, I want to transfer from 456
"""

result = question_answerer(question="Which account do you want to transfer to",     context=context)
print(f"Answer: '{result['answer']}', score: {round(result['score'], 4)}, start: {result['start']}, end: {result['end']}")