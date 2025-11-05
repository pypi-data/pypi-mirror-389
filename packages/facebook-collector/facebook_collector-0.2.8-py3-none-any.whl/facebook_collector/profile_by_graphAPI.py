from facebook_collector.constant import FacebookConstants
import requests


class UserInfoHandler():

    API_USER_INFO = "https://graph.facebook.com/v12.0/{username}/"
    def __init__(self, api_key):
        """
        Initialize the collector with an API key and configuration.

        Args:
            api_key (str): Your RapidAPI key for TikTok API
            country_code (str): The country code to filter posts by (default: "US")
            max_post_by_hashtag (int): Maximum number of posts to collect per hashtag (default: 100)
            max_hashtag_post_retry (int): Maximum number of retries for hashtag post collection (default: 3)
            max_profile_retry (int): Maximum number of retries for profile collection (default: 3)
        """
        self.api_key = api_key

    def get_user_info(self, username):
        url = self.API_USER_INFO.format(username=username)
        post_data = None
        try:
            response = requests.get(url, params={'access_token': self.api_key, 'fields': FacebookConstants.PROFILE_QUERY_FIELDS})

            data = response.json()
            if data and data.get("id"):
                profile_info = {
                    "user_id": data.get("id"),
                    "full_name": data.get("name"),
                    "username": data.get("username"),
                    "num_follower": data.get("followers_count"),
                    "num_friends": None,
                    "num_following": None,
                    "bio": data.get("about"),
                }
            else:
                profile_info = None
        except Exception as e:
            print("Load profile error", e)
        return profile_info

if __name__ == '__main__':
    handler = UserInfoHandler(api_key="1784198495144876|949e7fb42e7bc13a4dd3cf4d8f138afa")
    user_info = handler.get_user_info("okkknh")
    print(user_info)

