"""Own exceptions for webscraper."""


class NoQuotes(Exception):
    """Used when there are no fares for search parameters."""
    pass


class UnsupportedQuery(Exception):
    """Used when search parameters are wrong."""
    pass
