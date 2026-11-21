import unittest
from unittest.mock import patch
from personal_lite import core

class SystemDetailsTests(unittest.TestCase):
    @patch.object(core, 'IS_WINDOWS', False)
    def test_fallback_only_requested_keys(self):
        info=core.system_info()
        self.assertEqual(list(info), ['Windows','Редакция','Версия','Процессор','Видеокарта','Объём ОЗУ'])
        self.assertNotIn('Сборка',info)
        self.assertNotIn('Поддержка FIELD',info)

    @patch.object(core, 'IS_WINDOWS', True)
    @patch.object(core, 'windows_compatibility',return_value={'family':'11','release':'25H2'})
    @patch.object(core, 'native_windows_details',return_value={'edition':'Microsoft Windows 11 Pro','cpu':'AMD Ryzen 5 5600 6-Core Processor','gpu':['NVIDIA GeForce RTX 3060'],'ram':17179869184})
    def test_cpu_gpu_and_ram(self, *_):
        info=core.system_info()
        self.assertEqual(info['Процессор'],'AMD Ryzen 5 5600 6-Core Processor')
        self.assertEqual(info['Видеокарта'],'NVIDIA GeForce RTX 3060')
        self.assertEqual(info['Объём ОЗУ'],'16.0 ГБ')
        self.assertEqual(info['Версия'],'25H2')

    @patch.object(core, 'IS_WINDOWS', True)
    @patch.object(core, 'windows_compatibility',return_value={'family':'11','release':'25H2'})
    @patch.object(core, 'native_windows_details',return_value={'edition':'Майкрософт Windows 11 Pro','cpu':'Intel Core i5','gpu':['Intel UHD Graphics'],'ram':8589934592})
    def test_microsoft_brand_is_english(self, *_):
        self.assertEqual(core.system_info()['Редакция'], 'Microsoft Windows 11 Pro')

if __name__=='__main__': unittest.main()
