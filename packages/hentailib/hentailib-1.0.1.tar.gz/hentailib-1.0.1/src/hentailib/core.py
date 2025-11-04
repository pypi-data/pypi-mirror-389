

import requests
from random import choice
from typing import Optional, List


from .logger import get_logger, setup_logging

__debug_name__ = "hentailib"
__hentailib_debug__ = False


class Rule34Api:
    """Class Rule34Api used for store api key and use other classes

        Attributes:
            api_key (str): Api key from Rule34Api
            base_url (str): Base url for requests
            _utils (Utils): Utils class instance

    """

    def __init__(self, api_key: str, user_id: str, base_url: str = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index", debug_mode=__hentailib_debug__):
        """Initializes Rule34Api class with the given parameters.

        Args:
            api_key: Api key from Rule34Api
            base_url: Base url for requests. Default is "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"

        """

        if not api_key or not user_id:
            raise ValueError("API key and user ID are required")

        setup_logging(debug_mode)
        self.logger = get_logger(__debug_name__)

        self.api_key = api_key
        self.user_id = user_id
        self.base_url = base_url.rstrip('?&')
        self._utils = Utils(self)
        self.session = requests.Session()


    @property
    def utils(self):
        """



        """
        return self._utils

    def get_title(self, page_id: int) -> 'Title':
        """

        Args:
            page_id: Page id

        Returns:
            Title: Contains information about the requested title

        """
        if int(page_id) <= 0:
            raise ValueError("page_id must be positive")
        return Title(page_id, self)

    def _check_api_error(self, response):
        if "Missing authentication" in response:
            self.logger.error("API authentication failed")
            raise ApiKeyError("Invalid API credentials")
        if not response:
            self.logger.warning("Empty response from API")
            raise NotFoundError("Empty response from API")


class Utils:
    """Class Utils contains various utilities for working with rule34.

    Attributes:
        site_api (Rule34Api): Api Class for use a Rule34 Api

    """

    def __init__(self, site_api: Rule34Api):
        """Initializes Utils with the given parameters.

        Args:
            site_api (Rule34Api): Api Class for use a Rule34 Api
        """
        self.site_api = site_api
        self.logger = get_logger(__debug_name__)

    def get_random_page(self, tags: str, limit=100, do_autocomplete=True) -> Optional['Title']:
        """Get a random page from Rule34 with given tags

        Args:
            tags (str): Tags used for searching
            limit (int): The number of pages from which random selection will be made. Default is 100
            do_autocomplete (bool): Will autocomplete from the site be used

        Returns:
            Title: Page from Rule34
        """
        try:
            if do_autocomplete:
                tags = self.autocomplete_multiple_tags(tags)

            params = {
                "limit": limit,
                "tags": tags,
                "json": 1,
                "api_key": self.site_api.api_key,
                "user_id": self.site_api.user_id,

            }

            response = self.site_api.session.get(self.site_api.base_url,
                                    params=params, timeout=10)
            self.site_api._check_api_error(response.json())


            response.raise_for_status()
            data = response.json()
            data = choice(data)
            if not data:
                raise NotFoundError(f"No pages found with tags: {tags}")
            page_id = data["id"]
            self.logger.info("Successfully get page with id: " + str(page_id))
            return Title(page_id, self.site_api)


        except requests.exceptions.Timeout:
            self.logger.warning("Request timeout")
            raise PageLoadError("Request timeout")
        except requests.exceptions.HTTPError as e:
            self.logger.warning("HTTP status error")
            raise ApiKeyError("HTTP status error")

    def get_pages_by_tags(self, tags: List[str]) -> List['Title']:
        pass


    def autocomplete_single_tag(self, text: str, ranking=0) -> str:
        """Autocompletes one tag(without spaces) by Rule34 autocomplete

        Args:
            text: Single tag
            ranking: Which tag rank from zero will be used

        Returns:
            str: autocompleted tag
        """

        attrs = ""
        if text.startswith("-"):
            attrs = "-"
            text = text[1:]

        response = self.site_api.session.get(
            "https://api.rule34.xxx/autocomplete.php",
            params={"q": text},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if not data or ranking >= len(data):
            self.logger.warning(f"No autocomplete results for tag: {text}")
            return attrs + text

        return attrs + data[ranking]["value"]

    def autocomplete_multiple_tags(self, tags: str):
        if not tags or not tags.strip():
            return ""

        split_tags = tags.split()
        autocompleted_tags = list()
        for tag in split_tags:
            try:
                completed_tag = self.autocomplete_single_tag(tag)
                autocompleted_tags.append(completed_tag)
            except Exception as e:
                self.logger.warning("Exception with autocompleted tag: " + str(e))
                pass

        self.logger.info("Successfully autocompleted multiple tags")
        return " ".join(autocompleted_tags)



class Title:
    """A class containing information about a specific title

    Attributes:
        site_api (Rule34Api): Api Class for use a Rule34 Api
        id (int): Page id
        url (str): Url link to picture
        width (int): Image width
        height (int): Image height
        owner (str): Image uploader
        score (int): Score of the post
        source (str): Source of the picture
        tags (str): Tags

    """

    def __init__(self, page_id: int, site_api: Rule34Api):
        """Initializes Title with the given parameters.

        Calls __get_data() to request title data.

            Args:
                site_api (Rule34Api): Api Class for use a Rule34 Api
                page_id (int): Page id
        """

        self.site_api = site_api
        self.id = page_id
        self.url = None
        self.width = None
        self.height = None
        self.owner = None
        self.score = None
        self.source = None
        self.tags = None
        self.logger = get_logger(__debug_name__)

        self._get_data()

    def _get_data(self):
        """Get data from Rule34Api

        """
        try:
            params = {
                "limit": 1,
                "id": self.id,
                "json": 1,
                "api_key": self.site_api.api_key,
                "user_id": self.site_api.user_id,

            }

            response = self.site_api.session.get(self.site_api.base_url,
                                    params=params, timeout=10)
            self.site_api._check_api_error(response.json())

            response.raise_for_status()
            data = response.json()

            if not data:
                raise NotFoundError(f"No data found for page ID: {self.id}")

            self.url = data[0]["file_url"]
            self.width = data[0]["width"]
            self.height = data[0]["height"]
            self.owner = data[0]["owner"]
            self.score = data[0]["score"]
            self.source = data[0]["source"]
            self.tags = data[0]["tags"]

        except requests.exceptions.HTTPError as e:
            self.logger.warning("HTTPError")
            raise HTTPStatusError(str(e))
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Can't load page with id: {self.id}")
            raise PageLoadError(f"Can't load page {self.id}: {e}")
        except KeyError as e:
            self.logger.warning(f"KeyError: {e}")
            raise PageLoadError(f"KeyError {e}")

        self.logger.info("Get data from Rule34Api successfully")


class PageLoadError(Exception):
    """Exception class for loading page errors


    """
    def __init__(self, message="An unexpected custom error occurred."):
        self.message = message
        super().__init__(self.message)

class ApiKeyError(Exception):
    def __init__(self, message="Api key is wrong"):
        self.message = message
        super().__init__(self.message)

class HTTPStatusError(Exception):
    def __init__(self, message="HTTPStatusError"):
        self.message = message
        super().__init__(self.message)

class NotFoundError(Exception):
    def __init__(self, message="NotFoundError"):
        self.message = message
        super().__init__(self.message)



