from backend.orchestration.intent import IntentClassifier

history = [
    {'role': 'user', 'content': 'to jumira hotel from DIFC, I want to leave now.'},
    {'role': 'assistant', 'content': 'Would you like me to book a ride for you? Just say "yes book it" or choose a different option.'}
]

classifier = IntentClassifier()

print("Without history:")
intent_no_hist = classifier.classify('yes book it')
print(intent_no_hist.model_dump())

print("\nWith history:")
intent_with_hist = classifier.classify('yes book it', history=history)
print(intent_with_hist.model_dump())
