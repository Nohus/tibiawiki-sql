import re
import sqlite3

from tibiawikisql import schema
from tibiawikisql.models import abc
from tibiawikisql.utils import parse_boolean, parse_integer, clean_links, parse_min_max, int_pattern

creature_loot_pattern = re.compile(r"\|{{Loot Item\|(?:([\d?+-]+)\|)?([^}|]+)")


def parse_maximum_integer(value):
    """
    From a string, finds the highest integer found.

    Parameters
    ----------
    value: :class:`str`
        The string containing integers.

    Returns
    -------
    :class:`int`, optional:
        The highest number found, or None if no number is found.
    """
    if value is None:
        return None
    matches = int_pattern.findall(value)
    try:
        return max(list(map(int, matches)))
    except ValueError:
        return None


def parse_loot(value):
    """
    Gets every item drop entry of a creature's drops.

    Parameters
    ----------
    value: :class:`str`
        A string containing item drops.

    Returns
    -------
    tuple:
        A tuple containing the amounts and the item name.
    """
    return creature_loot_pattern.findall(value)


def parse_monster_walks(value):
    """
    Matches the values against a regex to filter typos or bad data on the wiki.
    Element names followed by any character that is not a comma will be considered unknown and will not be returned.

    Examples\:
        - ``Poison?, fire`` will return ``fire``.
        - ``Poison?, fire.`` will return neither.
        - ``Poison, earth, fire?, [[ice]]`` will return ``poison,earth``.
        - ``No``, ``--``, ``>``, or ``None`` will return ``None``.

    Parameters
    ----------
    value: :class:`str`
        The string containing possible field types.

    Returns
    -------
    :class:`str`, optional
        A list of field types, separated by commas.
    """
    regex = re.compile(r"(physical)(,|$)|(holy)(,|$)|(death)(,|$)|(fire)(,|$)|(ice)(,|$)|(energy)(,|$)|(earth)(,|$)|"
                       r"(poison)(,|$)")
    content = ""
    for match in re.finditer(regex, value.lower().strip()):
        content += match.group()
    if not content:
        return None
    return content


class Creature(abc.Row, abc.Parseable, table=schema.Creature):
    """Represents a creature.

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
    article: :class:`str`
        The article that goes before the name when looking at the creature.
    name: :class:`str`
        The name of the creature, as displayed in-game.
    class: :class:`str`
        The creature's classification.
    type: :class:`str`
        The creature's type.
    bestiary_class: :class:`str`
        The creature's bestiary class, if applicable.
    bestiary_level: :class:`str`
        The creature's bestiary level, from 'Trivial' to 'Hard'
    bestiary_occurrence: :class:`str`
        The creature's bestiary occurrence, from 'Common'  to 'Very Rare'.
    hitpoints: :class:`int`
        The creature's hitpoints, may be `None` if unknown.
    experience: :class:`int`
        Experience points yielded by the creature. Might be `None` if unknown.
    armor: :class:`int`
        The creature's armor value.
    speed: :class:`int`
        The creature's speed value.
    max_damage: :class:`int`
        The maximum amount of damage the creature can do in a single turn.
    summon_cost: :class:`int`
        The mana needed to summon this creature. 0 if not summonable.
    convince_cost: :class:`int`
        The mana needed to convince this creature. 0 if not convincible.
    illusionable: :class:`bool`
        Whether the creature can be illusioned into using `Creature Illusion`.
    pushable: :class:`bool`
        Whether the creature can be pushed or not.
    sees_invisible: :class:`bool`
        Whether the creature can see invisible players or not.
    paralyzable: :class:`bool`
        Whether the creature can be paralyzed or not.
    boss: :class:`bool`
        Whether the creature is a boss or not.
    modifier_physical: :class:`int`
        The percentage of damage received of physical damage. ``None`` if unknown.
    modifier_earth: :class:`int`
        The percentage of damage received of earth damage. ``None`` if unknown.
    modifier_fire: :class:`int`
        The percentage of damage received of fire damage. ``None`` if unknown.
    modifier_energy: :class:`int`
        The percentage of damage received of energy damage. ``None`` if unknown.
    modifier_ice: :class:`int`
        The percentage of damage received of ice damage. ``None`` if unknown.
    modifier_death: :class:`int`
        The percentage of damage received of death damage. ``None`` if unknown.
    modifier_holy: :class:`int`
        The percentage of damage received of holy damage. ``None`` if unknown.
    modifier_drown: :class:`int`
        The percentage of damage received of drown damage. ``None`` if unknown.
    modifier_lifedrain: :class:`int`
        The percentage of damage received of life drain damage. ``None`` if unknown.
    abilities: :class:`str`
        A brief description of the creature's abilities.
    walks_through: :class:`str`
        The field types the creature will walk through, separated by commas.
    walks_around: :class:`str`
        The field types the creature will walk around, separated by commas.
    version: :class:`str`
        The client version where this creature was first implemented.
    image: :class:`bytes`
        The creature's image in bytes.
    loot: list of :class:`CreatureDrop`
        The items dropped by this creature.
    """
    _map = {
        "article": ("article", lambda x: x),
        "name": ("name", lambda x: x),
        "actualname": ("name", lambda x: x),
        "creatureclass": ("class", lambda x: x),
        "bestiaryclass": ("bestiary_class", lambda x: x),
        "bestiarylevel": ("bestiary_level", lambda x: x),
        "occurrence": ("bestiary_occurrence", lambda x: x),
        "primarytype": ("type", lambda x: x),
        "hp": ("hitpoints", lambda x: parse_integer(x, None)),
        "exp": ("experience", lambda x: parse_integer(x, None)),
        "armor": ("armor", lambda x: parse_integer(x, None)),
        "speed": ("speed", lambda x: parse_integer(x, None)),
        "maxdmg": ("max_damage", parse_maximum_integer),
        "summon": ("summon_cost", parse_integer),
        "convince": ("convince_cost", parse_integer),
        "illusionable": ("illusionable", parse_boolean),
        "pushable": ("pushable", parse_boolean),
        "senseinvis": ("sees_invisible", parse_boolean),
        "paraimmune": ("paralysable", lambda x: not parse_boolean(x, None)),
        "isboss": ("boss", parse_boolean),
        "physicalDmgMod": ("modifier_physical", parse_integer),
        "earthDmgMod": ("modifier_earth", parse_integer),
        "fireDmgMod": ("modifier_fire", parse_integer),
        "iceDmgMod": ("modifier_ice", parse_integer),
        "energyDmgMod": ("modifier_energy", parse_integer),
        "deathDmgMod": ("modifier_death", parse_integer),
        "holyDmgMod": ("modifier_holy", parse_integer),
        "drownDmgMod": ("modifier_drown", parse_integer),
        "hpDrainDmgMod": ("modifier_hpdrain", parse_integer),
        "abilities": ("abilities", clean_links),
        "walksthrough": ("walks_through", parse_monster_walks),
        "walksaround": ("walks_around", parse_monster_walks),
        "implemented": ("version", lambda x: x)
    }
    _pattern = re.compile(r"Infobox[\s_]Creature")
    __slots__ = ("article_id", "title", "timestamp", "raw_attribute", "article", "name", "class", "type",
                 "bestiary_level", "bestiary_class", "bestiary_occurrence", "hitpoints", "experience", "armor", "speed",
                 "max_damage", "summon_cost", "convince_cost", "illusionable", "pushable", "sees_invisible",
                 "paralyzable", "boss", "modifier_pyhsical", "modifier_earth", "modifier_fire", "modifier_energy",
                 "modifier_ice", "modifier_death", "modifier_holy", "modifier_lifedrain", "modifier_drown", "abilities",
                 "walks_through", "walks_around", "version", "image", "loot")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_article(cls, article):
        """
        Parses an article into a TibiaWiki model.

        This method is overridden to parse extra attributes like loot.

        Parameters
        ----------
        article: :class:`api.Article`
            The article from where the model is parsed.

        Returns
        -------
        :class:`Creature`
            The creature represented by the current article.
        """
        creature = super().from_article(article)
        if creature is None:
            return None
        if "loot" in creature.raw_attributes:
            loot = parse_loot(creature.raw_attributes["loot"])
            loot_items = []
            for amounts, item in loot:
                if not amounts:
                    _min, _max = 0, 1
                else:
                    _min, _max = parse_min_max(amounts)
                loot_items.append(CreatureDrop(creature_id=creature.article_id, item_name=item, min=_min, max=_max))
            creature.loot = loot_items
        return creature

    def insert(self, c):
        """
        Inserts the current model into its respective database.

        This method is overridden to insert elements of child rows.

        Parameters
        ----------
        c: Union[:class:`sqlite3.Cursor`, :class:`sqlite3.Connection`]
            A cursor or connection of the database.
        """
        super().insert(c)
        for attribute in getattr(self, "loot", []):
            attribute.insert(c)

    @classmethod
    def _get_by_field(cls, c, field, value, use_like=False):
        creature = super()._get_by_field(c, field, value, use_like)
        if creature is None:
            return None
        creature.loot = CreatureDrop.get_by_creature_id(c, creature.article_id)
        return creature

    @classmethod
    def get_by_article_id(cls, c, article_id):
        """
        Gets a creature by its article id.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A connection or cursor of the database.
        article_id: :class:`int`
            The article id to look for.

        Returns
        -------
        :class:`Creature`
            The creature matching the ID, if any.
        """
        return cls._get_by_field(c, "article_id", article_id)

    @classmethod
    def get_by_name(cls, c, name):
        """
        Gets an creature by its name.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A connection or cursor of the database.
        name: :class:`str`
            The name to look for. Case insensitive.

        Returns
        -------
        :class:`Creature`
            The creature matching the name, if any.
        """
        return cls._get_by_field(c, "name", name, True)


class CreatureDrop(abc.Row, table=schema.CreatureDrop):
    """
    Represents an item dropped by a creature.

    Attributes
    ----------
    creature_id: :class:`int`
        The article id of the creature the drop belongs to.
    creature_name: :class:`str`
        The name of the creature that drops the item.
    item_id: :class:`int`
        The article id of the item.
    item_name: :class:`str`
        The name of the dropped item.
    min: :class:`int`
        The minimum possible amount of the dropped item.
    max: :class:`int`
        The maximum possible amount of the dropped item.
    chance: :class:`float`
        The chance percentage of getting this item dropped by this creature.
    """
    __slots__ = ("creature_id", "creature_name", "item_id", "item_name", "min", "max", "chance")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.item_name = kwargs.get("item_name")
        self.creature_name = kwargs.get("creature_name")

    def __repr__(self):
        attributes = []
        for attr in self.__slots__:
            try:
                v = getattr(self, attr)
                if v is None:
                    continue
                attributes.append("%s=%r" % (attr, v))
            except AttributeError:
                pass
        return "{0.__class__.__name__}({1})".format(self, ",".join(attributes))

    def insert(self, c):
        """Inserts the current model into its respective database.

        Overridden to insert using a subquery to get the item's id from the name.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A cursor or connection of the database.
        """
        if getattr(self, "item_id", None):
            super().insert(c)
        else:
            query = f"""INSERT INTO {self.table.__tablename__}(creature_id, item_id, min, max)
                        VALUES(?, (SELECT article_id from item WHERE title = ?), ?, ?)"""
            c.execute(query, (self.creature_id, self.item_name, self.min, self.max))

    @classmethod
    def _get_all_by_field(cls, c, field, value, use_like=False):
        operator = "LIKE" if use_like else "="
        query = """SELECT %s.*, item.name as item_name, creature.name as creature_name FROM %s
                   LEFT JOIN creature ON creature.article_id = creature_id
                   LEFT JOIN item ON item.article_id = item_id
                   WHERE %s %s ?""" % (cls.table.__tablename__, cls.table.__tablename__, field, operator)
        c = c.execute(query, (value,))
        c.row_factory = sqlite3.Row
        results = []
        for row in c.fetchall():
            result = cls.from_row(row)
            if result:
                results.append(result)
        return results

    @classmethod
    def get_by_creature_id(cls, c, creature_id):
        """
        Gets all drops matching the creature's id.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A connection or cursor of the database.
        creature_id: :class:`int`
            The article id of the creature.

        Returns
        -------
        list of :class:`CreatureDrop`
            A list of the creature's drops.
        """
        return cls._get_all_by_field(c, "creature_id", creature_id)

    @classmethod
    def get_by_item_id(cls, c, item_id):
        """
        Gets all drops matching the item's id.

        Parameters
        ----------
        c: :class:`sqlite3.Cursor`, :class:`sqlite3.Connection`
            A connection or cursor of the database.
        item_id: :class:`int`
            The article id of the item.

        Returns
        -------
        list of :class:`CreatureDrop`
            A list of the creatures that drop the item.
        """
        return cls._get_all_by_field(c, "item_id", item_id)


