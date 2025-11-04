from bs4 import BeautifulSoup
import re
from facebook_collector.graphql_handler import FacebookGraphQLCollector
from facebook_collector.utils import convert_to_number, _extract_facebook_username


class FacebookProfileCollector:
    def __init__(self, cookie):
        """
        Initialize the collector with cookie
        :param cookie: Facebook cookie string
        """
        self.cookie = cookie
        self.collector = None

    def setup(self):
        """
        Setup the Selenium collector
        """
        self.collector = FacebookGraphQLCollector(self.cookie)

    def extract_profile_info(self, html_content, username, user_id):
        """
        Extract profile information from HTML content
        :param html_content: HTML content of the profile page
        :param file_name: Username from URL
        :return: Dictionary containing profile information
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract username from URL

        # Extract full name
        name_raw = soup.findAll('h1',
                                class_="html-h1 xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1vvkbs x1heor9g x1qlqyl8 x1pd3egz x1a2a7pz")
        full_name = (name_raw[1]).text if name_raw else None
        if full_name == "Notifications" and name_raw:
            full_name = name_raw[2].text

        # Extract followers count
        data_raw = soup.find_all('a',
                                 class_="x1i10hfl xjbqb8w x1ejq31n x18oe1m7 x1sy0etr xstzfhl x972fbf x10w94by x1qhh985 x14e42zd x9f619 x1ypdohk xt0psk2 x3ct3a4 xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xkrqix3 x1sur9pj xi81zsa x1s688f")

        # Pattern to match different types of connections
        patterns = {
            'followers': r'(\d+(?:\.\d+)?[KkMm]?)\s+followers',
            'friends': r'(\d+(?:\.\d+)?[KkMm]?)\s+friends',
            'following': r'(\d+(?:\.\d+)?[KkMm]?)\s+following'
        }

        # Store all connection counts
        connections = {}

        for i in data_raw:
            text = i.text.lower()
            for conn_type, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    connections[conn_type] = match.group(1)
                    break

        # Extract bio
        bio_raw = soup.find('span',
                            class_="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xo1l8bm xzsf02u")
        if bio_raw is None:
            bio_raw = soup.find('span',
                                class_="x6zurak x18bv5gf x184q3qc xqxll94 x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x193iq5w xeuugli x13faqbe x1vvkbs x1lliihq xzsf02u xlh3980 xvmahel x1x9mg3 xo1l8bm")
        bio = bio_raw.text if bio_raw else None

        return {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "num_follower": convert_to_number(connections.get('followers')) if connections.get('followers') else None,
            "num_friends": convert_to_number(connections.get('friends')) if connections.get('friends') else None,
            "num_following": convert_to_number(connections.get('following')) if connections.get('following') else None,
            "bio": bio
        }

    def get_profile_info(self, profile_url):
        """
        Get profile information using Selenium and GraphQL handler
        :param profile_url: Facebook profile URL
        :return: Dictionary containing profile information
        """
        if not self.collector:
            self.setup()

        try:
            # Navigate to profile page
            self.collector.navigate_to_url(profile_url)
            redirected_url = self.collector.driver.current_url
            # Get page source after navigation
            html_content = self.collector.driver.page_source

            # Extract profile information
            profile_info = self.extract_profile_info(html_content, _extract_facebook_username(redirected_url),
                                                     profile_url.rstrip('/').split('/')[-1])

            return profile_info
        except Exception as e:
            print(f"Error getting profile info: {str(e)}")
            return None

    def close(self):
        """
        Close the Selenium collector
        """
        if self.collector:
            self.collector.close()
            self.collector = None


if __name__ == '__main__':
    # Example usage
    cookie = "sb=O7BCZ76WW9WsEOdAYM6yzAAv; ps_l=1; ps_n=1; datr=4045aJ-fPaeH6aGaf6gIKB-x; c_user=100011101573199; ar_debug=1; fr=1oAmemdUCuM1yKiq9.AWeQdZXU7BBNfjYVLg1yjThNFnvEU6NxNKguDhe-JCSNPhg38Qk.Bo-wDD..AAA.0.0.Bo-wDD.AWeMzh8RPvRoe17BIRjCvBuTGl8; xs=13%3Al5jL5h73bSu2WA%3A2%3A1748586223%3A-1%3A-1%3A%3AAcWp2KifPmGjI-VlPIgILdswRHptHoD98VEmNzGTdZlb; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1761281102624%2C%22v%22%3A1%7D; wd=874x966"
    collector = FacebookProfileCollector(cookie)
    usernames = ["krisannguerrero", "61567893097086", "aj.nid.leaf", "techscienceinfo"]
    for i in usernames:
        profile_url = f"https://www.facebook.com/{i}"
        profile_info = collector.get_profile_info(profile_url)

        if profile_info:
            print("Profile Information:", profile_info)
        else:
            print("Failed to retrieve profile information for", i)
    # profile_url = "https://www.facebook.com/krisannguerrero"  # Replace with the desired profile URL
    # profile_info = collector.get_profile_info(profile_url)

    # if profile_info:
    #     print("Profile Information:", profile_info)
    # else:
    #     print("Failed to retrieve profile information.")

    collector.close()
