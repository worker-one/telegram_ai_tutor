import json


def extract_json_from_text(text):
    text = text.replace("\'", "\"")
    # Find the first '{' character
    start = text.find('{')
    if start == -1:
        print("No JSON block found in the text.")
        return None

    # Use a stack to track nested braces
    stack = []
    for i in range(start, len(text)):
        if text[i] == '{':
            stack.append(i)
        elif text[i] == '}':
            stack.pop()
            if not stack:
                end = i + 1
                break
    else:
        print("No complete JSON block found in the text.")
        return None

    json_str = text[start:end]
    try:
        # Convert JSON string to dictionary
        json_dict = json.loads(json_str)
        return json_dict
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
