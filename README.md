# chat-app

How to run?
    
    + python3 -m venv venv #you can change to python virsion you're using
    + source venv/bin/activate
    + pip install -r requirements.txt 
    + python3 main.py

how to see meseges in another output:
    + python3 meseges.py

to acsses the site go to:
    [localhost:3000](http://localhost:3000)

if you whant to chat with your friends you can install ngrok and run this command:
    
    1. Create an ngrok account
        + Go to: https://ngrok.com
        + Sign up (free account is enough)
        + After signing up, you’ll get an Auth Token from your dashboard.

    2. Download ngrok
        + Go to: https://ngrok.com/download
        + Download for your OS (Windows, macOS, Linux, etc.)
        + Unzip the file and put ngrok in an easy-to-access location.
    
    3. Install ngrok (optional for CLI usage)
        For Linux/macOS:
            + sudo mv ngrok /usr/local/bin
            + chmod +x /usr/local/bin/ngrok
        For Windows: Just double-click or run ngrok.exe from Command Prompt or PowerShell.
    
    4. Connect your account (Auth Token):
        + ngrok config add-authtoken <YOUR_AUTHTOKEN>

    5. then run the folowing command after you run the main.py:
        + ngrok http 3000
