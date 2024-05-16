"""Contains prompts for location extractor."""

location_extractor_prompt = f"""\
Your task is to extract location information from the conversation with the user.
Here is the conversation transcript, delineated by triple backticks:
```
{{message_history}}
```

You need to know country, city, state or province, street address, and zip code.
If it is a well known city you can try to guess the country.
Analyze the conversation transcript carefully and extract the location information as a single line in the
name value pair format without any explanations.
"""

location_brevity_instructions = "very short and to the point"
