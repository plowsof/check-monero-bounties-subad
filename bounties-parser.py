import requests
from pprint import pprint
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
import csv 
from collections import defaultdict
import json

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

#get transfers / subaddress balances
rpc_connection = AuthServiceProxy(service_url="http://127.0.0.1:18085/json_rpc")
params = {"in": True}
info = rpc_connection.get_transfers(params)
for transfer in info["in"]:
    address = transfer["address"]
    amount = transfer["amount"]
    addr_total[address].setdefault("title", "")
    addr_total[address].setdefault("amount", 0)
    addr_total[address]["amount"] += amount

get_bounty_addresses()

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(addr_total, f)

with open("bounty-totals.csv", "w+") as f:
    #f.write("subaddress,amount,title\n")
    for addr in addr_total:
        amnt = addr_total[addr]["amount"] * (10 ** -12)
        f.write(f"{addr},{amnt},\"{addr_total[addr]['title']}\"\n")

with open('bounty-totals.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    sortedlist = sorted(csv_reader, key=lambda row: float(row[1]), reverse=True)
    pprint(sortedlist)

with open('bounty-totals.csv', "w+") as f:
    f.write("subaddress,amount,title")
    write = csv.writer(f)
    write.writerows(sortedlist)
