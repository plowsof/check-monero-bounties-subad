import requests
import json 
import time
cookies = {
			"user_session_id":"imn0tab0tloljk", 
			"auth":"hunter2" # if you can see my password and not ******* please report it. i paid someone to upgrade my github account to auto filter passwords.
		  }

def comment(comment):
	global cookies
	data = {
	    "content": f"{comment}",
	    "attachments": []
	}
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

	r = requests.post('https://bounties.monero.social/api/v1/posts/38/comments', data=json.dumps(data), cookies=cookies,headers=headers)
	return r

def delete_comment(num):
	global cookies
	r = requests.delete(f"https://bounties.monero.social/api/v1/posts/38/comments/{num}",cookies=cookies)


r = comment("im not a bot lol jk")
if r.status_code == 200:
	print("We posted a comment, sleep 10 seconds then delete it")
	get_id = json.loads(r._content.decode("utf-8"))
	time.sleep(10)
	delete_comment(get_id["id"])
	print("goodbye comment")


