# 2026_Feb_codeOff
code for the challenge in Feb
File	Purpose
main.py	Console loop: reads input, calls chat(), prints reply. Exits on quit/exit/bye/q.

router.py	Azure OpenAI chat with tool calling: KB lookup, check_inventory, get_item_price. Reads API settings from config.json. Uses your endpoint and API version.

inventory_db.py	Ensures inventory.db exists (or recreates from inventory_setup.sql if missing/corrupted). check_inventory(item_name, size), get_price(item_name), prices in GBP (£).

config.example.json	Template for API key and Azure settings (endpoint, API version, deployment).

knowledge_base.txt	Static company info (address, hours, delivery, returns, contact) used for KB answers.

requirements.txt	openai>=1.0.0

.gitignore	Ignores config.json so the key isn’t committed.

Behaviour
KB: Company questions are answered from knowledge_base.txt via the search_knowledge_base tool.
DB: Stock/price questions use check_inventory and get_item_price against inventory.db (same schema as your SQL).
Fallback: If the model doesn’t use any tool, the reply is: "I'm sorry, I cannot answer your query at the moment."
Currency/locale: System prompt instructs UK English and all prices in GBP (£).


How to run
Install deps
   cd "c:\Users\VerlekarV\Downloads\GCOFeb26Chatbot-main\version2_chatbot"   py -m pip install -r requirements.txt
Run
   py main.py
