## Gather Data on Twitter

Libs:
- Twython

I need to gather data on Twitter for my research project. So I build this tool on top of Twython.

Abilities:
- Streaming
- Search
- Get Followers
- Get Following
- Get User Timeline
- Rotating auth keys
- Cursoring

### Setting
- rename the `auth.sample.json` file to `auth.json`
- fill it with your own token
- ready to go!

### Run
- Make sure you install all the requirements by running `pip install -r requirements.txt`
- Then just use the `main.py` script
- for options, see below

### Options

```
optional arguments:
  -h, --help            show this help message and exit
  -t QUERYTYPE, --querytype QUERYTYPE
                        API type you want to use. Available: search, stream, followers, following, user_timeline
  -q QUERY, --query QUERY
                        keyword query
  -c COUNT, --count COUNT
                        For search querytype maximum 100
  -a AUTHENTICATION, --authentication AUTHENTICATION
                        JSON auth file location
  -l LANGUAGE, --language LANGUAGE
                        search language preference. ex: id
  -g GEOCODE, --geocode GEOCODE
                        search geocode preference. ex: 37.781157 -122.398720
                        1mi
  -rs RESULT_TYPE, --result_type RESULT_TYPE
                        search result_type preference. available options:
                        mixed, recent, popular
  -f FOLLOW, --follow FOLLOW
                        indicating the users whose Tweets should be delivered
                        on the stream.
  -u UNTIL, --until UNTIL
                        Returns tweets created before the given date. Format:
                        YYYY-MM-DD
```
