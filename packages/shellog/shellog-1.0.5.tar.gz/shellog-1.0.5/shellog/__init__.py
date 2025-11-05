"""
shellog.

A Python package to get notifications about the logs of a process.
"""

__version__ = "1.0.5"
__author__ = 'Daniele Margiotta'
__credits__ = 'Reveal s.r.l.'

import requests
import os

class Bot:
    def __init__(self, server_url=None):
        """
        Initialize the Shellog Bot
        
        Args:
            server_url (str, optional): Custom backend server URL. 
                                       Defaults to environment variable SHELLOG_SERVER_URL
                                       or 'http://localhost:5005' if not set.
        """
        if server_url:
            self.server_url = server_url
        else:
            self.server_url = os.environ.get('SHELLOG_SERVER_URL', 'http://localhost:5005')
        
        self.chat_id = []

    def sendMessage(self, text: str):
        """
        Send a message to all registered chat IDs
        
        Args:
            text (str): The message to send
            
        Returns:
            dict: Response from the server with results
            
        Raises:
            Exception: If the request fails or server returns an error
        """
        if not self.chat_id:
            raise ValueError("No chat IDs registered. Use addChatId() first.")
        
        if not text:
            raise ValueError("Message text cannot be empty.")
        
        try:
            response = requests.post(
                f"{self.server_url}/api/send_message",
                json={
                    'chat_ids': self.chat_id,
                    'text': text
                },
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'shellog/1.0.5'
                },
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get('error', 'Unknown error')
                raise Exception(f"Server error: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Cannot connect to Shellog server at {self.server_url}. "
                "Make sure the server is running or set SHELLOG_SERVER_URL environment variable."
            )
        except requests.exceptions.Timeout:
            raise Exception("Request to Shellog server timed out.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
            
    def addChatId(self, id: str):
        """Add a single chat ID"""
        if id not in self.chat_id:
            self.chat_id.append(str(id))
    
    def addListChatIds(self, ids):
        """Add multiple chat IDs from a list"""
        for id in ids:
            if id not in self.chat_id:
                self.chat_id.append(str(id))
    
    def removeChatId(self, id: str):
        """Remove a single chat ID"""
        if id in self.chat_id:
            self.chat_id.remove(str(id))

    def removeListChatIds(self, ids):
        """Remove multiple chat IDs from a list"""
        for id in ids:
            if id in self.chat_id:
                self.chat_id.remove(str(id))
    
    def clearChatId(self):
        """Clear all registered chat IDs"""
        self.chat_id.clear()

# Legacy support - deprecated
bot = Bot()

