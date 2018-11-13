import abc
import sqlite3

from tibiawikisql import database
from tibiawikisql.api import Article


def parse_attributes(content):
    """
    Parses the attributes of an Infobox template.

    Parameters
    ----------
    content: :class:`str`
        A string containing an Infobox template.

    Returns
    -------
    :class:`dict[str, str]`:
        A dictionary with every attribute as key.
    """
    attributes = dict()
    depth = 0
    parse_value = False
    attribute = ""
    value = ""
    for i in range(len(content)):
        if content[i] == '{' or content[i] == '[':
            depth += 1
            if depth >= 3:
                if parse_value:
                    value = value + content[i]
                else:
                    attribute = attribute + content[i]
        elif content[i] == '}' or content[i] == ']':
            if depth >= 3:
                if parse_value:
                    value = value + content[i]
                else:
                    attribute = attribute + content[i]
            if depth == 2:
                attributes[attribute.strip()] = value.strip()
                parse_value = False
                attribute = ""
                value = ""
            depth -= 1
        elif content[i] == '=' and depth == 2:
            parse_value = True
        elif content[i] == '|' and depth == 2:
            attributes[attribute.strip()] = value.strip()
            parse_value = False
            attribute = ""
            value = ""
        elif parse_value:
            value = value + content[i]
        else:
            attribute = attribute + content[i]
    return dict((k, v.strip()) for k, v in attributes.items() if v.strip())


class Parseable(Article, metaclass=abc.ABCMeta):
    """An abstract base class with the common parsing operations.

    This class is inherited by Models that are parsed directly from a TibiaWiki article.

    Classes implementing this must override :py:attr:`map`

    Attributes
    ----------
    article_id: :class:`int`
        The id of the  containing article.
    title: :class:`str`
        The title of the containing article.
    timestamp: :class:`int`
        The last time the containing article was edited.
    raw_attributes: :class:`dict`
        A dictionary containing attributes that couldn't be parsed.
    """
    _map = None
    """map: :class:`dict`: A dictionary mapping the article's attributes to object attributes."""
    _pattern = None
    """:class:`re.Pattern`: A compiled pattern to filter out articles by their content."""

    @classmethod
    def from_article(cls, article):
        """
        Parses an article into a TibiaWiki model.

        Parameters
        ----------
        article: :class:`api.Article`
            The article from where the model is parsed.

        Returns
        -------
        :class:`Type[abc.Parseable]`
            An inherited model object for the current article.
        """
        if cls._map is None:
            raise NotImplementedError("Inherited class must override map")

        if article is None or (cls._pattern and not cls._pattern.search(article.content)):
            return None
        row = {"article_id": article.article_id, "timestamp": article.timestamp, "title": article.title, "attributes": {}}
        attributes = parse_attributes(article.content)
        row["raw_attributes"] = {}
        for attribute, value in attributes.items():
            if attribute not in cls._map:
                row["raw_attributes"][attribute] = value
                continue
            column, func = cls._map[attribute]
            row[column] = func(value)
        return cls(**row)


class Row(metaclass=abc.ABCMeta):
    """
    An abstract base class implemented to indicate that the Model represents a SQL row.

    Attributes
    ----------
    table: :class:`database.Table`
        The SQL table where this model is stored.
    """
    table = None

    def __init__(self, **kwargs):
        for c in self.table.columns:
            value = kwargs.get(c.name, c.default)
            # SQLite Booleans are actually stored as 0 or 1, so we convert to true boolean.
            if isinstance(c.column_type, database.Boolean):
                value = bool(value)
            setattr(self, c.name, value)
        if kwargs.get("raw_attributes"):
            self.raw_attributes = kwargs.get("raw_attributes")

    def __init_subclass__(cls, table=None):
        cls.table = table

    def __repr__(self):
        key = "title"
        value = getattr(self, key, "")
        if not value:
            key = "name"
            value = getattr(self, key, "")
        return "%s (article_id=%d,%s=%r)" % (self.__class__.__name__, getattr(self, "article_id", 0), key, value)

    def insert(self, c):
        """
        Inserts the current model into its respective database table.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A cursor or connection of the database.
        """
        rows = {}
        for column in self.table.columns:
            try:
                value = getattr(self, column.name)
                if value == column.default:
                    continue
                rows[column.name] = value
            except AttributeError:
                continue
        self.table.insert(c, **rows)

    @classmethod
    def from_row(cls, row):
        """
        Returns an instance of the model from a row or dictionary.

        Parameters
        ----------
        row: :class:`dict`, :class:`sqlite3.Row`
            A dict representing a row or a Row object.

        Returns
        -------
        :class:`cls`:
            An instance of the class, based on the row.
        """
        if isinstance(row, sqlite3.Row):
            row = dict(row)
        return cls(**row)

    @classmethod
    def _get_by_field(cls, c, field, value, use_like=False):
        operator = "LIKE" if use_like else "="
        query = "SELECT * FROM %s WHERE %s %s ? LIMIT 1" % (cls.table.__tablename__, field, operator)
        c = c.execute(query, (value,))
        c.row_factory = sqlite3.Row
        row = c.fetchone()
        if row is None:
            return None
        return cls.from_row(row)


