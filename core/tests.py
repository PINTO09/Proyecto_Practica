from django.test import SimpleTestCase

from core.management.commands.load_schema import split_sql_statements


class SqlSplitterTests(SimpleTestCase):
    def test_split_sql_statements_respects_dollar_quoted_blocks(self):
        sql = """
        CREATE FUNCTION ejemplo() RETURNS void AS $$
        BEGIN
            INSERT INTO tabla VALUES (1);
        END;
        $$ LANGUAGE plpgsql;

        CREATE TABLE otro(id INT);
        """

        statements = split_sql_statements(sql)

        self.assertEqual(len(statements), 2)
        self.assertIn('CREATE FUNCTION ejemplo()', statements[0])
        self.assertIn('CREATE TABLE otro(id INT);', statements[1])
