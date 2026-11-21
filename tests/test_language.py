import unittest
from unittest.mock import patch
from personal_lite import i18n

class LanguageTests(unittest.TestCase):
    @patch('os.name', 'posix')
    @patch('locale.getlocale', return_value=('ru_RU','UTF-8'))
    def test_russian_system_locale(self, *_):
        self.assertEqual(i18n.detect_system_language(), 'ru')

    @patch('os.name', 'posix')
    @patch('locale.getlocale', return_value=('en_US','UTF-8'))
    def test_english_system_locale(self, *_):
        self.assertEqual(i18n.detect_system_language(), 'en')

if __name__ == '__main__': unittest.main()
