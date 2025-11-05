import unittest

from bankline_parser.data_services import enums, fields
from bankline_parser.data_services.exceptions import ParseError


class DataServicesFieldsTestCase(unittest.TestCase):
    def test_text_field(self):
        row = 'amazing'
        text_field = fields.TextField(0, 7)
        self.assertEqual(text_field.parse(row), 'amazing')

    def test_text_field_with_padding(self):
        row = '   amazing'
        text_field = fields.TextField(0, 10)
        self.assertEqual(text_field.parse(row), 'amazing')

    def test_text_field_with_padding_left_justified(self):
        row = 'amazing   '
        text_field = fields.TextField(0, 10, justification='l')
        self.assertEqual(text_field.parse(row), 'amazing')

    def test_text_field_left_justified_left_padding_not_removed(self):
        row = '   amazing'
        text_field = fields.TextField(0, 10, justification='l')
        self.assertEqual(text_field.parse(row), '   amazing')

    def test_numeric_field(self):
        row = 'otherstuff000064'
        numeric_field = fields.NumericField(10, 16)
        self.assertEqual(numeric_field.parse(row), 64)

    def test_numeric_field_nonnumeric_value_fails(self):
        row = 'h67'
        numeric_field = fields.NumericField(0, 3)
        try:
            numeric_field.parse(row)
            self.fail()
        except ParseError:
            pass

    def test_enum_field(self):
        row = 'gggggD000000'
        enum_field = fields.EnumField(5, 6, enums.BalanceType)
        self.assertEqual(enum_field.parse(row), enums.BalanceType.debit)

    def test_static_field(self):
        row = 'hello'
        static_field = fields.StaticField(0, 6, 'hello')
        self.assertEqual(static_field.parse(row), 'hello')

    def test_static_field_trim_padding(self):
        row = '   hello'
        static_field = fields.StaticField(0, 9, 'hello')
        self.assertEqual(static_field.parse(row), 'hello')

    def test_static_field_include_padding(self):
        row = '   hello'
        static_field = fields.StaticField(0, 9, '   hello', pad_char=None)
        self.assertEqual(static_field.parse(row), '   hello')

    def test_static_field_incorrect_value_fails(self):
        row = 'herro'
        static_field = fields.StaticField(0, 6, 'hello')
        try:
            static_field.parse(row)
            self.fail()
        except ParseError:
            pass
