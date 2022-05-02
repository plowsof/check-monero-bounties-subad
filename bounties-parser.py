import requests
import pprint 
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
import csv 

addr_total = {}

def get_bounty_address(data):
    global addr_total, unknown
    totals = []
    for post in data:
        #print(f"title: {post['title']}\nid: {post['id']}")
        comments = requests.get(f"https://bounties.monero.social/api/v1/posts/{post['id']}/comments").json()
        for comment in comments:
            if comment["user"]["name"] == "Monero Bounties Bot":
                #print(comment["content"])
                words = comment["content"].split()
                for word in words:
                    if len(word) == 95:
                        donation_address = word
                        #print(f"title: {post['title']}\nid: {post['id']}\naddress: {donation_address}")
                        try:
                            if addr_total[donation_address]:   
                                addr_total[donation_address]["title"] = post["title"]
                        except:
                            pass
                        #check for the spammed addresses / don't break
                        #break

def get_posts(endpoint):
    info = requests.get(endpoint)
    data = info.json()
    get_bounty_address(data)

#get transfers / subaddress balances
rpc_connection = AuthServiceProxy(service_url="http://127.0.0.1:18085/json_rpc")
params = {"in": True}
info = rpc_connection.get_transfers(params)
for transfer in info["in"]:
    address = transfer["address"]
    amount = transfer["amount"]
    data = {
    "amount": amount,
    "title": ""
    }
    try:
        if addr_total[address]:
            addr_total[address]["amount"] += data["amount"]
    except:
        addr_total[address] = data

get_posts("https://bounties.monero.social/api/v1/posts")
get_posts("https://bounties.monero.social/api/v1/posts?view=completed")
get_posts("https://bounties.monero.social/api/v1/posts?view=planned")
get_posts("https://bounties.monero.social/api/v1/posts?view=started")
get_posts("https://bounties.monero.social/api/v1/posts?view=declined")



with open("bounty-totals.csv", "w+") as f:
    #f.write("subaddress,amount,title\n")
    for addr in addr_total:
        if not addr_total[addr]["title"]:
            print(addr_total[addr]["amount"])
            print(addr)
        amnt = addr_total[addr]["amount"] * (10 ** -12)
        print(amnt)
        f.write(f"{addr},{amnt},\"{addr_total[addr]['title']}\"\n")



with open('bounty-totals.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    sortedlist = sorted(csv_reader, key=lambda row: float(row[1]), reverse=True)
    pprint.pprint(sortedlist)



with open('bounty-totals.csv', "w+") as f:
    f.write("subaddress,amount,title")
    write = csv.writer(f)
    write.writerows(sortedlist)
