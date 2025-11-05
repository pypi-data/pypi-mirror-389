import unittest

from bankline_parser.data_services import parse
from bankline_parser.data_services.exceptions import ParseError

from .test_models import vhl_row


class DataServicesParserTestCase(unittest.TestCase):
    def test_nwb_testfile_successful_parse(self):
        with open('tests/data/testfile_nwb') as f:
            output = parse(f)

        self.assertTrue(output.is_valid())
        self.assertEqual(len(output.accounts), 1)
        self.assertEqual(len(output.account.records), 29)
        self.assertEqual(
            output.account.user_trailer_label.monetary_total_debit_items,
            278225388,
        )
        self.assertEqual(
            output.account.user_trailer_label.monetary_total_credit_items,
            105598692,
        )

    def test_rbs_testfile_successful_parse(self):
        with open('tests/data/testfile_rbs') as f:
            output = parse(f)

        self.assertTrue(output.is_valid())
        self.assertEqual(len(output.accounts), 1)
        self.assertEqual(len(output.account.records), 25)
        self.assertEqual(
            output.account.user_trailer_label.monetary_total_debit_items,
            554186444,
        )
        self.assertEqual(
            output.account.user_trailer_label.monetary_total_credit_items,
            666903844,
        )

    def test_empty_file_fails(self):
        try:
            parse([])
            self.fail()
        except ParseError:
            pass

    def test_no_accounts_fails(self):
        try:
            parse([vhl_row])
            self.fail()
        except ParseError:
            pass
