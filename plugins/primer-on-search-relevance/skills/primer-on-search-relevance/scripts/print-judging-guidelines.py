"""Prints the model, the word count of each prompt and the guidelines prompt verbatim, from the recording's manifest. The prose's point rests on the rules at the end of that prompt."""
from lib.recorded import manifest

recording = manifest("llm-judgments")             # the recording's model, settings and both prompts, verbatim
short, guidelines = recording["prompts"]["short"], recording["prompts"]["guidelines"]

print("model:", recording["model"])
print("what the model saw:", recording["sees"])
print("words in the short prompt:", len(short.split()))
print("words in the guidelines prompt:", len(guidelines.split()))
print()
print(guidelines)
