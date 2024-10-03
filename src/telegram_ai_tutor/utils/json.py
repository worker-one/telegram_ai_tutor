import json
import re


def extract_json_from_text(text):
    text = text.replace("'", '"')
    # Find the JSON block using regex
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)

    if json_match:
        json_str = json_match.group(1)
        try:
            # Parse the JSON string
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            print("Error: Invalid JSON format")
            return None
    else:
        print("Error: No JSON block found")
        return None


# def extract_json_from_text(text):
#     print(text)
#     text = text.replace("'", '"')
#     # Find the first '{' character

#     if "```" in text:
#         result = extract_code_block(text)
#         if result is None:
#             pass

#     start = text.find('{')
#     if start == -1:
#         print("No JSON block found in the text.")
#         return None

#     # Use a stack to track nested braces
#     stack = []
#     for i in range(start, len(text)):
#         if text[i] == '{':
#             stack.append(i)
#         elif text[i] == '}':
#             stack.pop()
#             if not stack:
#                 end = i + 1
#                 break
#     else:
#         print("No complete JSON block found in the text.")
#         return None

#     json_str = text[start:end]
#     print(json_str)
#     try:
#         # Convert JSON string to dictionary
#         json_dict = json.loads(json_str)
#         return json_dict
#     except json.JSONDecodeError as e:
#         print(f"Error decoding JSON: {e}")
#         return None
