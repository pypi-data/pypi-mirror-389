import json

version_json = '''
{
 "author": "RL",
 "date": 2024.08,
 "version":"1.6.0"
}
'''


def get_versions():
    return json.loads(version_json)
