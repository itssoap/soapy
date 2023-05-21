import random
from redis import Redis

def hashfunc() -> str:
    """
    Always returns a new random Hash.
    A random hash is generated, if this hash has already been generated,
    then a new hash is generated
    """

    radicals = ['ba', 'be', 'bi', 'bo', 'bu', 
                'ca', 'ce', 'ci', 'co', 'cu', 
                'da', 'de', 'di', 'do', 'du', 
                'fa', 'fe', 'fi', 'fo', 'fu', 
                'ga', 'ge', 'gi', 'go', 'gu', 
                'ha', 'he', 'hi', 'ho', 'hu', 
                'ja', 'je', 'ji', 'jo', 'ju', 
                'ka', 'ke', 'ki', 'ko', 'ku', 
                'la', 'le', 'li', 'lo', 'lu', 
                'ma', 'me', 'mi', 'mo', 'mu', 
                'na', 'ne', 'ni', 'no', 'nu', 
                'pa', 'pe', 'pi', 'po', 'pu', 
                'qa', 'qe', 'qi', 'qo', 'qu', 
                'ra', 're', 'ri', 'ro', 'ru', 
                'sa', 'se', 'si', 'so', 'su', 
                'ta', 'te', 'ti', 'to', 'tu', 
                'va', 've', 'vi', 'vo', 'vu', 
                'wa', 'we', 'wi', 'wo', 'wu', 
                'xa', 'xe', 'xi', 'xo', 'xu', 
                'ya', 'ye', 'yi', 'yo', 'yu', 
                'za', 'ze', 'zi', 'zo', 'zu']

    while(1):
        hash = ''.join([radicals[x] for x in random.choices(range(len(radicals)), k=5)])
        if redischeck(hash) is False:
            break

    return redisadd(hash)

def redischeck(hash: str) -> bool:
    redis = Redis(host="localhost", port=6379)
    redis.sadd("hashpool", "initial")
    return redis.sismember("hashpool", hash)

def redisadd(hash: str) -> str:
    redis = Redis(host="localhost", port=6379)
    redis.sadd("hashpool", hash)
    return hash