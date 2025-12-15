import requests
from pprint import pprint
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
import csv 
from collections import defaultdict
import json
import sqlite3
import re
from decimal import Decimal, ROUND_HALF_UP

DB_FILE = "bounties.db"
addr_total = defaultdict(dict)

def get_bounty_addresses():
    global addr_total, unknown
    info = requests.get("https://bounties.monero.social/api/v1/posts?view=recent&limit=1").json()
    max_posts = info[0]['id']
    totals = []
    for x in range(1,max_posts+1):
        print(x)
        try: # if post is deleted this will error and continue to next
            post_json = requests.get(f"https://bounties.monero.social/api/v1/posts/{x}").json()
        except:
            continue
        title = post_json["title"]
        comments = requests.get(f"https://bounties.monero.social/api/v1/posts/{x}/comments").json()
        for comment in comments:
            donation_address = False
            if comment["user"]["name"] == "Monero Bounties Bot":
                words = comment["content"].split()
                for word in words:
                    if len(word) == 95:
                        donation_address = word
                    # [xxx](monero:84cF4zQbTA1) 
                    if "monero:" in word: # markdown
                        donation_address = word.split("monero:")[1].replace(")","")
                if donation_address:
                    addr_total[donation_address]["title"] = title
                    addr_total[donation_address].setdefault("amount", 0)
                    addr_total[donation_address]["post"] = x

def extract_claimed_amount_xmr(title):
    """
    '1.213ɱ | Develop Nym Monero Transaction Broadcaster'
    Returns Decimal('1.213') or None
    """
    if not title:
        return None
    m = re.search(r"([\d.]+)\s*ɱ", title)
    if not m:
        return None
    return Decimal(m.group(1))

def atomic_to_xmr_3dp(atomic):
    xmr = Decimal(atomic) / Decimal(10**12)
    return xmr.quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)

def main():
    global DB_FILE, addr_total

    get_bounty_addresses()

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(addr_total, f)
    
    # get transfers / subaddress balances
    rpc_connection = AuthServiceProxy(service_url="http://127.0.0.1:18085/json_rpc")
    params = {"in": True}
    info = rpc_connection.get_transfers(params)
    for transfer in info["in"]:
        address = transfer["address"]
        amount = transfer["amount"]
        addr_total[address].setdefault("title", "none")
        addr_total[address].setdefault("amount", 0)
        addr_total[address]["amount"] += amount

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bounty_addresses (
        post_id INTEGER,
        title TEXT,
        address TEXT,
        amount INTEGER,
        PRIMARY KEY (post_id, address)
    )
    """)

    for addr, data in addr_total.items():
        cur.execute(
            """
            INSERT INTO bounty_addresses (post_id, title, address, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(post_id, address) DO UPDATE SET
                title = excluded.title,
                amount = excluded.amount
            """,
            (
                data.get("post"),
                data.get("title"),
                addr,
                data.get("amount", 0)
            )
        )

    conn.commit()

    cur.execute("""
    SELECT
        post_id,
        title,
        SUM(amount) AS total_received_atomic
    FROM bounty_addresses
    GROUP BY post_id, title
    """)

    rows = cur.fetchall()

    mismatches = []

    for post_id, title, total_atomic in rows:
        claimed_xmr = extract_claimed_amount_xmr(title)
        if claimed_xmr is None:
            continue

        received_xmr = atomic_to_xmr_3dp(total_atomic)

        if received_xmr != claimed_xmr:
            mismatches.append((
                post_id,
                title,
                str(total_atomic),
                str(claimed_xmr),
                str(received_xmr),
                str(received_xmr - claimed_xmr)
            ))

    with open("bounty-mismatches.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id",
            "title",
            "total_atomic",
            "claimed_xmr",
            "received_xmr",
            "delta_xmr"
        ])
        for row in mismatches:
            writer.writerow(row)

    conn.close()

    #len(mismatches)
main()
