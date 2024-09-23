import re


def extract_and_save_html(text, output_filename="output.html"):
    # Define a regular expression pattern to extract the HTML block
    html_pattern = re.compile(r"<html.*?>.*?</html>", re.DOTALL | re.IGNORECASE)

    # Search for the HTML block in the given text
    html_match = html_pattern.search(text)

    if html_match:
        # Extract the HTML content
        html_content = html_match.group(0)
        print(html_content)
        # Save the HTML content to a file
        with open(output_filename, "w", encoding="utf-8") as file:
            file.write(html_content)

        return True
    else:
        raise ValueError("No HTML block found in the given text.")

