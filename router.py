"""LLM router with function calling: KB, inventory, fallback. UK English, prices in GBP (£)."""
import json
import os
from openai import AzureOpenAI

from knowledge_base import search_knowledge_base
from inventory_db import check_inventory, get_price, format_price_gbp

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_DEPLOYMENT = "gpt-4o-mini"

AZURE_ENDPOINT_DEFAULT = "https://greatcodeoff.openai.azure.com/"
AZURE_API_VERSION_DEFAULT = "2025-01-01-preview"


def _load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _get(key: str, default: str = "") -> str:
    val = _load_config().get(key) or default
    return (val or "").strip()


AZURE_ENDPOINT = _get("azure_openai_endpoint") or AZURE_ENDPOINT_DEFAULT
AZURE_API_VERSION = _get("azure_api_version") or AZURE_API_VERSION_DEFAULT
OPENAI_API_KEY = _get("openai_api_key") or _get("OPENAI_API_KEY")
AZURE_DEPLOYMENT = _get("azure_deployment") or DEFAULT_DEPLOYMENT

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the company knowledge base for: address, location, office hours, delivery policy, next-day delivery cost, returns policy, contact email or phone. Use for any question about TechGear UK company information.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check stock level and price for a product in a specific size. Use for questions like 'Is X available in size Y?', 'How many X in size Y?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Product name, e.g. 'Waterproof Commuter Jacket', 'Tech-Knit Hoodie', 'Dry-Fit Running Tee'"},
                    "size": {"type": "string", "description": "Size: S, M, L, or XL"},
                },
                "required": ["item_name", "size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_item_price",
            "description": "Get the price of a product in GBP. Use for questions like 'What is the price of X?', 'How much is X?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Product name, e.g. 'Dry-Fit Running Tee', 'Tech-Knit Hoodie', 'Waterproof Commuter Jacket'"},
                },
                "required": ["item_name"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a helpful customer service chatbot for TechGear UK. Use UK English only.

- Company information (address, office hours, delivery, returns, contact): call search_knowledge_base and answer from that content only. Format all prices in GBP (£).
- Product stock for a specific item and size: call check_inventory with item_name and size. If stock_count is 0, say out of stock; otherwise state stock and price in £.
- Product price only: call get_item_price. Reply with the price in GBP, e.g. £25.00.

Always use the tools when the question is about company info or inventory. Answer briefly in UK English. All prices must be in GBP (£).
If the question is not about TechGear UK or their products/inventory, do not call any tool."""

FALLBACK_MESSAGE = "I'm sorry, I cannot answer your query at the moment."


def _run_tool(name: str, arguments: dict) -> str:
    if name == "search_knowledge_base":
        return search_knowledge_base("")
    if name == "check_inventory":
        item = arguments.get("item_name", "").strip()
        size = arguments.get("size", "").strip()
        if not item or not size:
            return "Error: item_name and size are required."
        result = check_inventory(item, size)
        if result is None:
            return "No such product or size found."
        stock = result["stock_count"]
        price_str = format_price_gbp(result["price_gbp"])
        if stock == 0:
            return f"Out of stock. Price: {price_str}"
        return f"In stock: {stock}. Price: {price_str}"
    if name == "get_item_price":
        item = arguments.get("item_name", "").strip()
        if not item:
            return "Error: item_name is required."
        result = get_price(item)
        if result is None:
            return "Product not found."
        return f"Price: {format_price_gbp(result['price_gbp'])}"
    return "Unknown tool."


def chat(user_message: str, model: str | None = None) -> str:
    """Send user message to LLM with tools. Execute tool calls and return final answer. If no tool was used, return fallback."""
    if not OPENAI_API_KEY:
        return (
            "Error: API key not found. Copy config.example.json to config.json and set openai_api_key to your Azure key."
        )

    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=OPENAI_API_KEY,
        api_version=AZURE_API_VERSION,
    )
    deployment = model or AZURE_DEPLOYMENT
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    tool_used = False

    while True:
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            tool_used = True
            messages.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _run_tool(name, args)
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
            continue

        text = (msg.content or "").strip()
        if not tool_used:
            return FALLBACK_MESSAGE
        return text if text else FALLBACK_MESSAGE
