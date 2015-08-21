import json
import sys
import requests
from mcstatus import MinecraftServer

# Install requests and mcstatus module

SLACK_HOOK_URL = '' # Slack-bot webhook URL/URI
CHANNEL_ID = '' # Slack Channel ID
CHANNEL_NAME = '\#minecraft'
SLACK_TOKEN = '' # Slack API token (for topic changing)

# Run with "python [script] [mojang_username] [mojang_password]"

def get_token(email, password):
    data = {
        'agent': {'name': 'Minecraft', 'version': "1.8.8"},
        'password': password,
        'username': email,
    }
    resp = requests.post('https://authserver.mojang.com/authenticate',
                         data=json.dumps(data))
    if resp.status_code != 200:
        raise Exception(resp.content)
    return {
        'username': json.loads(resp.content)['selectedProfile']['name'],
        'uuid': json.loads(resp.content)['selectedProfile']['id'],
        'access_token': json.loads(resp.content)['accessToken'],
    }
def get_ips(email, password):
    credentials = get_token(email, password)
    headers = {
        'Cookie': 'sid=token:{access_token}:{uuid};user={username};version=1'
                  .format(**credentials)
    }
    resp = requests.get('https://mcoapi.minecraft.net/worlds', headers=headers)
    return {
        server['name']: server['ip']
        for server in json.loads(resp.content)['servers']
    }
def get_players(address):
    if not address:
        return []
    print "Connecting to {}".format(address)
    server = MinecraftServer.lookup(address)
    resp = server.status()
    try:
        return [p.name for p in resp.players.sample]
    except TypeError:
        return []
def set_topic(topic):
    requests.post(
        'https://slack.com/api/channels.setTopic',
        params={
            'token': SLACK_TOKEN,
            'channel': CHANNEL_ID,
            'topic': topic,
        }
    )
def get_topic():
    resp = requests.post(
        'https://slack.com/api/channels.info',
        params={
            'token': SLACK_TOKEN,
            'channel': CHANNEL_ID,
        }
    )
    return json.loads(resp.content)['channel']['topic']['value']
if __name__ == '__main__':
    servers = get_ips(sys.argv[1], sys.argv[2])
    topics = []
    # Get Players
    for name, address in servers.iteritems():
        players = get_players(address)
        players = ", ".join(players) if players else "N/A"
        topics.append("{} - {}".format(name, players))
    # Update Topic
    new_topic = "; ".join(topics)
    #old_topic = get_topic()
    try:
        with open('topic.txt', 'rb') as f:
            old_topic = f.read()
    except IOError:
        old_topic = None
    if old_topic != new_topic:
        #set_topic(new_topic)
        requests.post(SLACK_HOOK_URL, data=json.dumps({
            "channel": CHANNEL_NAME,
            "text": new_topic,
        }))
    with open('topic.txt', 'wb') as f:
        f.write(new_topic)
