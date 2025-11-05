import unittest
from datetime import datetime

from bankline_parser.data_services import enums, models

vhl_row = (
    'VOL1                                 ****830000                '
    '                3                                                '
)
fhl_row = (
    'HDR1 A876543Z0001                      F     01 06032          '
    '    060320                                                       '
)
uhl_row = (
    'UHL1 06032876543    00000000         000              Datalink '
    'Test File                                                          '
)
data_record = (
    '8765438765432101112345678418953000000000006086                 '
    ' 123456                               06032                      '
)
balance_record = (
    '123456671753150Y1              0000 000000038510000C0000000000000'
    '00C000000056571776C000000038474276C 04036                      '
)
utl_row = (
    'UTL10000554186444000066690384400000150000010                   '
    '                                                                 '
)


class DataServicesRowsTestCase(unittest.TestCase):
    def test_volume_header_label(self):
        vhl = models.VolumeHeaderLabel(vhl_row)
        self.assertEqual(vhl.label_identifier, 'VOL1')
        self.assertEqual(vhl.volume_serial_number, None)
        self.assertEqual(vhl.owner_identification, '****830000')
        self.assertEqual(vhl.label_standard_level, 3)

    def test_file_header_label(self):
        fhl = models.FileHeaderLabel(fhl_row)
        self.assertEqual(fhl.label_identifier, 'HDR1')
        self.assertEqual(fhl.file_identifier, 'A876543Z')
        self.assertEqual(fhl.file_sequence_number, 1)
        self.assertEqual(fhl.record_format, 'F')
        self.assertEqual(fhl.creation_date, datetime.strptime('06032', '%y%j'))
        self.assertEqual(fhl.expiration_date, datetime.strptime('06032', '%y%j'))
        self.assertEqual(fhl.copy_indicator, None)

    def test_user_header_level(self):
        uhl = models.UserHeaderLabel(uhl_row)
        self.assertEqual(uhl.label_identifier, 'UHL1')
        self.assertEqual(uhl.processing_date, datetime.strptime('06032', '%y%j'))
        self.assertEqual(uhl.branch_sort_code, '876543')
        self.assertEqual(uhl.currency_code, None)
        self.assertEqual(uhl.work_code, None)
        self.assertEqual(uhl.file_number, None)
        self.assertEqual(uhl.customer_name, 'Datalink Test File')

    def test_data_record(self):
        dr = models.DataRecord(data_record)
        self.assertEqual(dr.branch_sort_code, '876543')
        self.assertEqual(dr.branch_account_number, '87654321')
        self.assertEqual(dr.type_of_account_code, None)
        self.assertEqual(dr.transaction_code, enums.TransactionCode.debit_cheque)
        self.assertEqual(dr.originators_sort_code, '123456')
        self.assertEqual(dr.originators_account_number, '78418953')
        self.assertEqual(dr.originators_reference, None)
        self.assertEqual(dr.amount, 6086)
        self.assertEqual(dr.transaction_description, None)
        self.assertEqual(dr.reference_number, '123456            ')
        self.assertEqual(dr.date, datetime.strptime('06032', '%y%j'))

    def test_balance_record(self):
        br = models.BalanceRecord(balance_record)
        self.assertEqual(br.branch_sort_code, '123456')
        self.assertEqual(br.branch_account_number, '67175315')
        self.assertEqual(br.type_of_account_code, None)
        self.assertEqual(br.transaction_code, enums.TransactionCode.balance_record)
        self.assertEqual(br.ledger_balance, 38510000)
        self.assertEqual(br.ledger_balance_type, enums.BalanceType.credit)
        self.assertEqual(br.cleared_balance, 0)
        self.assertEqual(br.cleared_balance_type, enums.BalanceType.credit)
        self.assertEqual(br.recorded_ledger_balance, 56571776)
        self.assertEqual(br.recorded_ledger_balance_type, enums.BalanceType.credit)
        self.assertEqual(br.recorded_cleared_balance, 38474276)
        self.assertEqual(br.recorded_cleared_balance_type, enums.BalanceType.credit)
        self.assertEqual(br.date, datetime.strptime('04036', '%y%j'))

    def test_user_trailer_label(self):
        utl = models.UserTrailerLabel(utl_row)
        self.assertEqual(utl.label_identifier, 'UTL1')
        self.assertEqual(utl.monetary_total_debit_items, 554186444)
        self.assertEqual(utl.monetary_total_credit_items, 666903844)
        self.assertEqual(utl.count_debit_items, 15)
        self.assertEqual(utl.count_credit_items, 10)
        self.assertEqual(utl.count_balance_records, None)
