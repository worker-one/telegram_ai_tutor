from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram_ai_tutor.api.bot import start_bot
from telegram_ai_tutor.db.database import create_tables
import os

# Create the HTML file
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Hello World</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>Welcome to my local server.</p>
</body>
</html>
"""

def create_html_file():
    with open("hello.html", "w") as file:
        file.write(html_content)
    print("hello.html created successfully.")

# Serve the HTML file
class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/hello.html':
            self.path = 'hello.html'
        return SimpleHTTPRequestHandler.do_GET(self)

def serve_html_file():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
    print("Serving on port 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    # Step 1: Create tables
    create_tables()
    
    # Step 2: Create the hello.html file
    create_html_file()

    # Step 4: Serve the HTML file
    serve_html_file()
    
    # Step 3: Start the bot and serve the HTML file on a different thread
    start_bot()
    
    
