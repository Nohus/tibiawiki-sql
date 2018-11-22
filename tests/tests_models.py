import sqlite3
import unittest

from tests import load_resource
from tibiawikisql import Article, models, schema


class TestWikiApi(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        schema.create_tables(self.conn)

    def testAchievement(self):
        article = Article(1, "Demonic Barkeeper", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_achievement.txt"))
        achievement = models.Achievement.from_article(article)
        self.assertIsInstance(achievement, models.Achievement)

        achievement.insert(self.conn)
        db_achievement = models.Achievement.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_achievement, models.Achievement)
        self.assertEqual(db_achievement.name, achievement.name)

        db_achievement = models.Achievement.get_by_field(self.conn, "name", "demonic barkeeper", use_like=True)
        self.assertIsInstance(db_achievement, models.Achievement)

    def testCharm(self):
        for charm in models.charm.charms:
            charm.insert(self.conn)

        charm = models.Charm.get_by_field(self.conn, "name", "dodge", use_like=True)

        self.assertIsInstance(charm, models.Charm)
        self.assertIsInstance(charm.points, int)

    def testCreature(self):
        article = Article(1, "Demon", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_creature.txt"))
        creature = models.Creature.from_article(article)
        self.assertIsInstance(creature, models.Creature)

        creature.insert(self.conn)
        db_creature = models.Creature.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_creature, models.Creature)
        self.assertEqual(db_creature.name, creature.name)
        self.assertEqual(db_creature.modifier_earth, creature.modifier_earth)
        self.assertGreater(len(db_creature.loot), 0)

        db_creature = models.Creature.get_by_field(self.conn, "name", "demon", use_like=True)
        self.assertIsInstance(db_creature, models.Creature)

    def testHouse(self):
        article = Article(1, "Crystal Glance", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_house.txt"))
        house = models.House.from_article(article)
        self.assertIsInstance(house, models.House)

        house.insert(self.conn)
        db_house = models.House.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_house, models.House)
        self.assertEqual(db_house.name, house.name)

        models.House.get_by_field(self.conn, "house_id", 55302)
        self.assertIsInstance(db_house, models.House)

    def testImbuement(self):
        article = Article(1, "Powerful Strike", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_imbuement.txt"))
        imbuement = models.Imbuement.from_article(article)
        self.assertIsInstance(imbuement, models.Imbuement)

        imbuement.insert(self.conn)
        db_imbuement = models.Imbuement.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_imbuement, models.Imbuement)
        self.assertEqual(db_imbuement.name, imbuement.name)
        self.assertEqual(db_imbuement.tier, imbuement.tier)
        self.assertGreater(len(db_imbuement.materials), 0)

        db_imbuement = models.Imbuement.get_by_field(self.conn, "name", "powerful strike", use_like=True)
        self.assertIsInstance(db_imbuement, models.Imbuement)

    def testItem(self):
        article = Article(1, "Fire Sword", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_item.txt"))
        item = models.Item.from_article(article)
        self.assertIsInstance(item, models.Item)

        item.insert(self.conn)
        db_item = models.Item.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_item, models.Item)
        self.assertEqual(db_item.name, item.name)
        self.assertGreater(len(db_item.attributes), 0)

        db_item = models.Item.get_by_field(self.conn, "name", "fire sword", use_like=True)
        self.assertIsInstance(db_item, models.Item)

    def testKey(self):
        article = Article(1, "Key 3940", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_key.txt"))
        key = models.Key.from_article(article)
        self.assertIsInstance(key, models.Key)

        key.insert(self.conn)
        db_key = models.Key.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_key, models.Key)
        self.assertEqual(db_key.name, key.name)

        db_key = models.Key.get_by_field(self.conn, "number", 3940)
        self.assertIsInstance(db_key, models.Key)

    def testNpc(self):
        article = Article(1, "Yaman", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_npc.txt"))
        npc = models.Npc.from_article(article)
        self.assertIsInstance(npc, models.Npc)

        npc.insert(self.conn)
        db_npc = models.Npc.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_npc, models.Npc)
        self.assertEqual(db_npc.name, npc.name)

        article = Article(2, "Captain Bluebear", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_npc_travel.txt"))
        npc = models.Npc.from_article(article)
        self.assertIsInstance(npc, models.Npc)
        self.assertGreater(len(npc.destinations), 0)

        article = Article(3, "Shalmar", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_npc_spells.txt"))
        npc = models.Npc.from_article(article)
        self.assertIsInstance(npc, models.Npc)

    def testQuest(self):
        article = Article(1, "The Annihilator Quest", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_quest.txt"))
        quest = models.Quest.from_article(article)
        self.assertIsInstance(quest, models.Quest)

        quest.insert(self.conn)
        db_quest = models.Quest.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_quest, models.Quest)
        self.assertEqual(db_quest.name, quest.name)

    def testSpell(self):
        article = Article(1, "The Annihilator Quest", timestamp="2018-08-20T04:33:15Z",
                          content=load_resource("content_spell.txt"))
        spell = models.Spell.from_article(article)
        self.assertIsInstance(spell, models.Spell)

        spell.insert(self.conn)
        db_spell = models.Spell.get_by_field(self.conn, "article_id", 1)

        self.assertIsInstance(db_spell, models.Spell)
        self.assertEqual(db_spell.name, spell.name)