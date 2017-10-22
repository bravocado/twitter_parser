#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, os, sys, random, time, argparse, socket, re, codecs, requests
from twython import Twython
from twython import TwythonError
from twython import TwythonStreamer
import pandas as pd
from furl import furl
from datetime import datetime


# =============
# GLOBAL VARIABLES
# =============
consumer_key = ''
consumer_key_secret = ''
access_token = ''
access_token_secret = ''

tokens = []
key_sequence = 0
used_keys = []
token = []

# later modify header
# client_args = {
# 	'headers': {
# 		'User-Agent': "Meteor Morning"
# 	},
# 	'timeout': 300,
# }

# =============
# DATA VARIABLES
# =============
data_labels = ['user_id', 'user_is_verified', 'user_is_protected', 'user_screen_name', 'user_name', 'user_created_at',
			   'user_followers_count', 'user_statuses_count', 'user_following_count', 'user_location','user_utc_offset',
			   'user_profile_image_url', 'user_profile_banner_url', 'user_profile_background_image_url',
			   'user_description', 'user_time_zone', 'user_profile_url',
			   'tweet_id', 'tweet_created_at', 'tweet_lang', 'tweet_text', 'tweet_source', 'tweet_possibly_sensitive',
			   'tweet_coordinates', 'tweet_coordinates_long', 'tweet_coordinates_lat',
			   'tweet_geo', 'tweet_geo_long', 'tweet_geo_lat', 'tweet_place_country', 'tweet_place_name',
			   'tweet_retweeted', 'tweet_favorited', 'tweet_retweet_count', 'tweet_favorite_count',
			   'tweet_is_quote_status', 'tweet_quoted_status_id', 'tweet_in_reply_to_status_id', 'tweet_in_reply_to_screen_name',
			   'tweet_in_reply_to_user_id', 'tweet_symbols', 'tweet_user_mentions_id', 'tweet_user_mentions_screen_name',
			   'tweet_user_mentions_name', 'tweet_hashtags', 'tweet_media_type', 'tweet_media_id',
			   'tweet_media_monetizable', 'tweet_media_url'
				]
post_data = []
stream_data = []
stream_stopper = 5

# =============
# QUICK FIX
# =============
# cursor_ids = []


# =============
# MAIN
# =============
def main():
	parser = argparse.ArgumentParser(description='Twitter Crawler')
	parser.add_argument("-t", "--querytype", type=str, default='search',
					help="API type you want to use")
	parser.add_argument("-q", "--query", type=str, default=None,
					help="keyword query")
	parser.add_argument("-c", "--count", type=int, default=15,
					help="count search. max 100")
	parser.add_argument("-a", "--authentication", type=str, default='./auth.json',
					help="JSON auth file location")
	args = parser.parse_args()
	args_dict = vars(args)

	# key generator
	apiRotator =  keyRotator()
	apiRotator.authentication(authentication=args.authentication,
							key_sequence=key_sequence)

	# assign class to variable
	twCrawler = Crawler()

	# calling crawl function from class
	twCrawler.crawl(querytype=args.querytype,
					query=args.query,
					count=args.count,
					authentication=args.authentication)

# ==========================
# STREAMER CLASS
# ==========================
class Streamer(TwythonStreamer):
	"""
		Streamer class
	"""
	def on_success(self, data):
		print("from user: " + str(data["user"].get("screen_name")))
		# print("date: " + str(data.get("created_at")))
		created_at = data.get("created_at")
		unix_time = time.mktime(time.strptime(created_at,"%a %b %d %H:%M:%S +0000 %Y")) + 25200 # quickhack for display only (Jakarta time)
		# when = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
		when = time.strftime("(UTC+7) %D %H:%M", time.localtime(int(unix_time)))
		print("date: " + str(when))
		if data.get("full_text"):
			print(data.get("full_text"))
		else:
			print(data.get("text"))
		print("\n==========================\n")
		stream_data.append(data)
		if len(stream_data) == stream_stopper:
			self.disconnect()
		else:
			pass

	def on_error(self, status_code, data):
		print("error code: " + str(status_code))
		if status_code == 420:
			print("limit..")
			self.disconnect()
		elif status_code == 401:
			self.disconnect()
		else:
			self.disconnect()

# ==========================
# KEY ROTATOR CLASS
# ==========================

class keyRotator(object):
	# def __init__(self):
	# 	print("loading authentication file.....")

	# authenticator
	def authentication(self, authentication, key_sequence):
		auth_json = open(authentication)
		auth_file = json.load(auth_json)
		# append to tokens
		for i in auth_file.values():
			tokens.append([
						i["consumer_key"],
						i["consumer_key_secret"],
						i["access_token"],
						i["access_token_secret"]
						])
		# print(tokens[key_sequence])
		token = tokens[len(used_keys)]
		consumer_key = token[0]
		consumer_key_secret = token[1]
		access_token = token[2]
		access_token_secret = token[3]
		return consumer_key, consumer_key_secret, access_token, access_token_secret

	# rotator
	def rotator(self, sequence):
		token = tokens[sequence]
		consumer_key = token[0]
		consumer_key_secret = token[1]
		access_token = token[2]
		access_token_secret = token[3]
		# tokens[:] = []
		return consumer_key, consumer_key_secret, access_token, access_token_secret

# ==========================
# CRAWLER CLASS
# ==========================
class Crawler(object):
	"""
		Crawler class
	"""

	# initial
	def __init__(self):
		# when load normal json, disable
		print("...")

	# own cursor reader
	def cursorReader(self, query, count, max_id):
		result_type = "mixed"
		n = 2 # the deep of loop for checking cursor
		for i in range(0, n):
			print("searching with max_id parameter: " + str(max_id))
			result = self._tw.search(q=query,
									max_id=max_id,
									count=count,
									result_type=result_type,
									tweet_mode="extended")
			# print(result["search_metadata"])
			metadata = result["search_metadata"].get("next_results")
			if metadata:
				max_id = furl(metadata).args['max_id']
				print("\n======================================\n")
				print("found new max_id: " + str(max_id))
				return max_id
				break
			else:
				print("can't find max_id in metadata... retrying..")
				print("searching with since_id parameter: " + str(max_id))
				result = self._tw.search(q=query,
										since_id=max_id,
										count=count,
										result_type=result_type,
										tweet_mode="extended")
				max_id = result['statuses'][-1].get("id")
				print("retying using tweet id: " + str(max_id))
				time.sleep(random.randint(5,10))
			# last check
			if i == n-1:
				result = self._tw.search(q=query,
										count=count,
										result_type=result_type,
										tweet_mode="extended")
				max_id = result['statuses'][0].get("id")
				print("udahan mz, kaga nemu apa-apa... pake ini aje.." + str(max_id) + " atulah.. :(")
				return max_id
				break
			else:
				pass

	# search handling
	def searchHandler(self, query, count, querytype):
		sequence = 0
		max_id = 0
		result_type = "mixed"

		while True:
			print("current sequence: " + str(sequence))

			randomizer = random.randint(0, len(tokens)-1)
			keys = keyRotator().rotator(sequence=randomizer)
			consumer_key, consumer_key_secret, access_token, access_token_secret = keys
			print("using key: " + str(consumer_key) + "\n")
			try:
				self._tw_auth = Twython(consumer_key, consumer_key_secret, oauth_version=2)
				OAUTH2_ACCESS_TOKEN = self._tw_auth.obtain_access_token()
				self._tw = Twython(consumer_key, access_token=OAUTH2_ACCESS_TOKEN)
			except TwythonError as e:
				print("error on Twython!")

			result = self._tw.search(q=query,
									max_id=max_id,
									count=count,
									result_type=result_type,
									tweet_mode="extended")

			print("preprocessing data...")
			self.preprocessingData(result, query, sequence, querytype)
			print("producing csv...")
			self.produceCsv(post_data, query, querytype)
			print("current API rate limit: " + str(self._tw.get_lastfunction_header('x-rate-limit-remaining')))

			# metadata finder
			metadata = result["search_metadata"].get("next_results")
			if metadata:
				max_id_finder = self.cursorReader(query, count, max_id)
				max_id = max_id_finder
			else:
				print("oops.. no max_id again.. \nlatest max_id: " + str(max_id))
				created_at = result["statuses"][-1].get("created_at")
				unix_time = time.mktime(time.strptime(created_at,"%a %b %d %H:%M:%S +0000 %Y")) + 25200 # quickhack Jakarta timezone
				when = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d')
				print("latest tweet created at: " + str(when))
				break

			# adding new sequence
			sequence+=1

			print("sleeping...")
			time.sleep(random.randint(1,5))

	def streamHandler(self, querytype, query):
		randomizer = random.randint(0, len(tokens)-1)
		keys = keyRotator().rotator(sequence=randomizer)
		consumer_key, consumer_key_secret, access_token, access_token_secret = keys
		print("using key: " + str(consumer_key) + "\n")
		try:
			self._tw_stream = Streamer(app_key=consumer_key,
									app_secret=consumer_key_secret,
									oauth_token=access_token,
									oauth_token_secret=access_token_secret,
									chunk_size=stream_stopper, retry_in=300)
			self._tw_stream.statuses.filter(track=query, tweet_mode="extended")
		except requests.ConnectionError:
			print("connection error..")
			sys.exit(0)
		if len(stream_data) == stream_stopper:
			for i in stream_data:
				self.jsonCruncher(i)
			stream_data[:] = []
			self.produceCsv(post_data, query, querytype)
			print("\n==========================\n")
		else:
			pass

	# ==========================
	# MAIN ENGINE
	# ==========================
	def crawl(self, querytype, query, count, authentication):
		if querytype == "search":
			# todos: loop moved here
			self.searchHandler(querytype=querytype,
							query=query,
							count=count)
			# DEBUG
			# result = self._tw.search(q=query, count=count, result_type="mixed", tweet_mode="extended")
			# print(result["statuses"])
			# result = self._tw.show_status(id=815411895343587330)
		elif querytype == "stream":
			while True:
				self.streamHandler(querytype=querytype,
								query=query)

		else:
			print("Your API type not found in this function..")
	# ==========================
	# END MAIN ENGINE
	# ==========================


	# preprocessing data
	def preprocessingData(self, data, query, sequence, querytype):
		raw_statuses = data['statuses']

		self.saveRawJson(data, query, sequence, querytype)

		for statuses in raw_statuses:
			self.jsonCruncher(statuses)

	# json specialist chruncher
	def jsonCruncher(self, data):
			temp_data = []

			# user
			temp_data.append(data["user"].get("id")) # user_id
			temp_data.append(data["user"].get("verified")) # user is verified
			temp_data.append(data["user"].get("protected")) # user is protected
			temp_data.append(data["user"].get("screen_name")) # user screen_name
			temp_data.append(data["user"].get("name")) # user name
			temp_data.append(data["user"].get("created_at")) # user created_at
			temp_data.append(data["user"].get("followers_count")) # user followers_count
			temp_data.append(data["user"].get("statuses_count")) # user statuses_count
			temp_data.append(data["user"].get("friends_count")) # user following_count
			temp_data.append(data["user"].get("location")) # user location
			temp_data.append(data["user"].get("utc_offset")) # user utc_offset
			temp_data.append(data["user"].get("profile_image_url")) # user profile_image_url
			temp_data.append(data["user"].get("profile_banner_url")) # user profile_banner_url
			temp_data.append(data["user"].get("profile_background_image_url")) # user profile_background_image_url
			temp_data.append(data["user"].get("description")) # user description
			temp_data.append(data["user"].get("time_zone")) # user time_zone
			temp_data.append(data["user"].get("url")) # user url (profile_url)
			
			# tweet
			temp_data.append(data.get("id")) # tweet id (status_id)
			temp_data.append(data.get("created_at")) # tweet created_at
			temp_data.append(data.get("lang")) # tweet lang
			if data.get("full_text"):
				temp_data.append(data.get("full_text")) # tweet text if 280 char
			else:
				temp_data.append(data.get("text")) # tweet text if 140 char
			temp_data.append(data.get("source")) # tweet source
			temp_data.append(data.get("possibly_sensitive")) # tweet possibly_sensitive
			if data.get("coordinates"):
				longitude, latitude = data["coordinates"].get("coordinates")
				temp_data.append(str(longitude)+", "+str(latitude)) # tweet coordinates joined
				temp_data.append(longitude) # tweet_coordinates_long
				temp_data.append(latitude) # tweet_coordinates_lat
			else:
				temp_data.append("None") # set to none -- # tweet coordinates joined
				temp_data.append("None") # set to none -- # tweet_coordinates_long
				temp_data.append("None") # set to none -- # tweet_coordinates_at
			if data.get("geo"):
				longitude, latitude = data["geo"].get("coordinates")
				temp_data.append(str(longitude)+", "+str(latitude)) # tweet geo joined
				temp_data.append(longitude) # tweet_geo_long
				temp_data.append(latitude) # tweet_geo_lat
			else:
				temp_data.append("None") # set to none -- # tweet geo joined
				temp_data.append("None") # set to none -- # tweet_geo_long
				temp_data.append("None") # set to none -- # tweet_geo_at
			if data.get('place'):
				temp_data.append(data['place'].get("country")) # tweet place country
				temp_data.append(data['place'].get("name")) # tweet place name
			else:
				temp_data.append("None") # set to none
				temp_data.append("None") # set to none
			temp_data.append(data.get("retweeted")) # tweet retweeted
			temp_data.append(data.get("favorited")) # tweet favorited
			temp_data.append(data.get("retweet_count")) # tweet retweet_count
			temp_data.append(data.get("favorite_count")) # tweet favorite_count
			temp_data.append(data.get("is_quote_status")) # tweet favorite_count
			if data.get("quoted_status_id"):
				temp_data.append(data.get("quoted_status_id")) # tweet qouted_status_id
			else:
				temp_data.append("None") # if not qouting, set to none
			temp_data.append(data.get("in_reply_to_status_id")) # tweet in_reply_to_status_id
			temp_data.append(data.get("in_reply_to_screen_name")) # tweet in_reply_to_screen_name
			temp_data.append(data.get("in_reply_to_user_id")) # tweet in_reply_to_user_id
			
			# tweet entities - symbols
			if data["entities"].get("symbols"):
				tweet_entities_symbols_list = []
				for i in data["entities"].get("symbols"):
					tweet_entities_symbols_list.append(i.get("text")) # extract text to list
				tweet_entities_symbols = ", ".join(tweet_entities_symbols_list) # join it
				temp_data.append(tweet_entities_symbols) # append it to temp_data
			else:
				temp_data.append("None") # empty symbols -- set to none
			# tweet entities - user_mentions
			if data["entities"].get("user_mentions"):
				tweet_entities_user_mentions_id_list = []
				tweet_entities_user_mentions_screen_name_list = []
				tweet_entities_user_mentions_name_list = []
				for i in data["entities"].get("user_mentions"):
					tweet_entities_user_mentions_id_list.append(str(i.get("id")))
					tweet_entities_user_mentions_screen_name_list.append(i.get("screen_name"))
					tweet_entities_user_mentions_name_list.append(i.get("name"))
				tweet_entities_user_mentions_id = ", ".join(tweet_entities_user_mentions_id_list) # extract id user_mentions
				tweet_entities_user_mentions_screen_name = ", ".join(tweet_entities_user_mentions_screen_name_list) # extract screen_name user_mentions
				tweet_entities_user_mentions_name = ", ".join(tweet_entities_user_mentions_name_list) # extract name user_mentions
				temp_data.append(tweet_entities_user_mentions_id) # append entities_id to temp_data
				temp_data.append(tweet_entities_user_mentions_screen_name) # append entities_screen_name to temp_data
				temp_data.append(tweet_entities_user_mentions_name) # append entities_name to temp_data
			else:
				temp_data.append("None") # empty user_mentions_id set to none
				temp_data.append("None") # empty user_mentions_screen_name set to none
				temp_data.append("None") # empty user_mentions_name set to none
			# tweet entities - hashtag
			if data["entities"].get("hashtags"):
				tweet_entities_hashtags_list = []
				for i in data["entities"].get("hashtags"):
					tweet_entities_hashtags_list.append(i.get("text")) # extract hashtags
				tweet_entities_hashtags = ", ".join(tweet_entities_hashtags_list) # join to new string
				temp_data.append(tweet_entities_hashtags) # append it to temp_data
			else:
				temp_data.append("None") # empty hashtags
					
			# tweet media
			if data.get("extended_entities"): # check whenever extended_entities exist or not
				medias = data["extended_entities"]["media"]
				# temp list
				tweet_extended_entitites_media_type_list = []
				tweet_extended_entitites_media_id_list = []
				tweet_extended_entitites_media_monetizable_list = []
				tweet_extended_entitites_media_urls_list = []
				# tweet_extended_entities_media_video_duration_millis_list = []
				# look up
				for media in medias:
					tweet_extended_entitites_media_type_list.append(media.get("type")) # extract media_type
					tweet_extended_entitites_media_id_list.append(str(media.get("id"))) # extract media_id
					tweet_extended_entitites_media_monetizable_list.append(str(media.get("monetizable"))) # extract media_monetizable
					tweet_extended_entitites_media_urls_list.append(str(media.get("media_url"))) # extract media_url
				# joins
				tweet_extended_entitites_media_type = ", ".join(tweet_extended_entitites_media_type_list)
				tweet_extended_entitites_media_id = ", ".join(tweet_extended_entitites_media_id_list)
				tweet_extended_entitites_media_monetizable = ", ".join(tweet_extended_entitites_media_monetizable_list)
				tweet_extended_entitites_media_urls = ", ".join(tweet_extended_entitites_media_urls_list)
				# append
				temp_data.append(tweet_extended_entitites_media_type) # append tweet_extended_entitites_media_type
				temp_data.append(tweet_extended_entitites_media_id) # append tweet_extended_entitites_media_id
				temp_data.append(tweet_extended_entitites_media_monetizable) # append tweet_extended_entitites_media_monetizable
				temp_data.append(tweet_extended_entitites_media_urls) # append tweet_extended_entitites_media_urls
				
			else:
				temp_data.append("None") # empty tweet_extended_entitites_media_type set to none
				temp_data.append("None") # empty tweet_extended_entitites_media_id set to none
				temp_data.append("None") # empty tweet_extended_entitites_media_monetizable set to none
				temp_data.append("None") # empty tweet_extended_entitites_media_urls set to none
			
			# clean up
			temp_data_replaced = ["None" if v is None else v for v in temp_data]
			
			# send it to post_data
			post_data.append(temp_data_replaced)


	# create csv
	def produceCsv(self, data, query, querytype):
		df = pd.DataFrame.from_records(data, columns=data_labels)

		if query.startswith("#"):
			filename = "hashtag-" + query.replace("#", "")
		elif query.startswith("@"):
			filename = "user-" + query.replace("@", "")
		elif " " in query == True:
			print("ada spasi..")
			filename = str(query.replace(" ", "_"))
		elif " " in query:
			filename = str(query.replace(" ", "_").replace(",", ""))
		else:
			filename = "keyword-" + query
		if querytype == "search":
			filename = str(querytype) + "_" + str(filename)
		elif querytype == "stream":
			filename = str(querytype) + "_" + str(filename)
		else:
			filename = filename
		dir_path = './result'
		today = time.strftime("%Y_%m_%d")
		fullfilename = filename +  '-' + today + '.csv'
		filepath = os.path.join(dir_path, fullfilename)
		if os.path.isfile(filepath):
			# when result csv exist
			df.to_csv(filepath, mode="a", header=False, index=False, encoding="utf-8-sig", line_terminator="\r\n")
			print("appending to exisiting csv file at: " + str(filepath))
			print("cleaning up temporary data...")
			post_data[:] = []
		else:
			# when result csv NOT exist
			df.to_csv(filepath, index=False, encoding="utf-8-sig", line_terminator="\r\n")
			print("writing new csv file at: " + str(filepath))
			print("cleaning up temporary data...")
			post_data[:] = []


	# save raw json file
	def saveRawJson(self, data, query, sequence, querytype):
		today = time.strftime("%Y_%m_%d")
		if query.startswith("#"):
			filename = "hashtag-" + query.replace("#", "")
		elif query.startswith("@"):
			filename = "user-" + query.replace("@", "")
		elif " " in query:
			filename = str(query.replace(" ", "_").replace(",", ""))
		else:
			filename = "keyword-" + query
		if querytype == "search":
			filename = str(querytype) + "_" + str(filename)
		elif querytype == "stream":
			filename = str(querytype) + "_" + str(filename)
		else:
			filename = filename
		dir_path = os.path.join('./data', filename)
		fullfilename = filename + '-' + today + '-' + str(sequence) + ".json"
		file_path = os.path.join(dir_path, fullfilename)
		# check dirs
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)
		else:
			pass
		# writer get ready
		file_writer = open(file_path, "w")
		file_appender = open(file_path, "a")
		raw_json = json.dumps(data)
		# writer on action
		if os.path.isfile(file_path):
			file_appender.write(raw_json.decode("utf-8"))
		else:
			file_writer.write(raw_json.decode("utf-8"))




if __name__ == "__main__":
	main()