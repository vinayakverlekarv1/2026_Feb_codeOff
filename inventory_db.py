"""SQLite inventory queries. All prices in GBP (£)."""
import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")
SETUP_SQL_PATH = os.path.join(os.path.dirname(__file__), "inventory_setup.sql")


def ensure_inventory_db(db_path: str | None = None) -> None:
    """Create inventory.db from inventory_setup.sql if the DB file does not exist or is corrupted."""
    p = db_path or DEFAULT_DB_PATH
    if os.path.exists(p):
        try:
            conn = sqlite3.connect(p)
            conn.execute("SELECT 1 FROM product_inventory LIMIT 1")
            conn.close()
            return
        except sqlite3.Error:
            try:
                os.remove(p)
            except OSError:
                pass
    if not os.path.exists(SETUP_SQL_PATH):
        return
    with open(SETUP_SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = sqlite3.connect(p)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _get_connection(db_path: str | None = None):
    ensure_inventory_db(db_path)
    p = db_path or DEFAULT_DB_PATH
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"Inventory database not found at {p}. "
            "Run: sqlite3 inventory.db < inventory_setup.sql"
        )
    return sqlite3.connect(p)


def check_inventory(item_name: str, size: str, db_path: str | None = None) -> dict | None:
    """Get stock count and price for an item/size. Returns dict or None if not found."""
    size = size.strip().upper()
    conn = _get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT item_name, size, stock_count, price_gbp FROM product_inventory "
            "WHERE LOWER(TRIM(item_name)) = LOWER(TRIM(?)) AND UPPER(TRIM(size)) = ?",
            (item_name.strip(), size),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "item_name": row[0],
            "size": row[1],
            "stock_count": row[2],
            "price_gbp": float(row[3]),
        }
    finally:
        conn.close()


def get_price(item_name: str, db_path: str | None = None) -> dict | None:
    """Get price for an item (any size). Returns dict or None."""
    conn = _get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT item_name, price_gbp FROM product_inventory "
            "WHERE LOWER(TRIM(item_name)) = LOWER(TRIM(?)) LIMIT 1",
            (item_name.strip(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"item_name": row[0], "price_gbp": float(row[1])}
    finally:
        conn.close()


def format_price_gbp(price_gbp: float) -> str:
    """Format price in GBP, e.g. £25.00."""
    return f"£{price_gbp:.2f}"
