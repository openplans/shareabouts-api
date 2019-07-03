#-*- coding:utf-8 -*-

from django.test import TestCase
from nose.tools import istest
from sa_api_v2.renderers import GeoJSONRenderer

class TestGeoJSONRenderer (TestCase):

#    def test_(self):
#        renderer = GeoJSONRenderer()
#        data = {
#          u'updated_datetime': u'2013-05-01T20:41:34.097Z',
#          u'created_datetime': u'2013-05-01T20:41:34.097Z',
#          u'geometry': u'POINT (2.0000000000000000 3.0000000000000000)',
#          u'dataset': 1,
#          u'visible': True,
#          u'submitter_name': u'Mjumbe',
#          u'data': u'{"name": "K-Mart", "type": "ATM"}',
#          u'id': 1
#        }
#        renderer.render(data)

    def test_no_data(self):
        renderer = GeoJSONRenderer()
        data = None

        result = renderer.render(data)
        self.assertEqual(result, b'')

# class TestCSVRenderer (TestCase):

#     def test_tablize_a_list_with_no_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([])
#         self.assertEqual(flat, [])

#     def test_tablize_a_list_with_atomic_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([1, 2, 'hello'])
#         self.assertEqual(flat, [[''     ],
#                                 [1      ],
#                                 [2      ],
#                                 ['hello']])


#     def test_tablize_a_list_with_list_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([[1, 2, 3],
#                                  [4, 5],
#                                  [6, 7, [8, 9]]])
#         self.assertEqual(flat, [['0' , '1' , '2'  , '2.0' , '2.1'],
#                                 [1   , 2   , 3    , None  , None ],
#                                 [4   , 5   , None , None  , None ],
#                                 [6   , 7   , None , 8     , 9    ]])

#     def test_tablize_a_list_with_dictionary_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([{'a': 1, 'b': 2},
#                                  {'b': 3, 'c': {'x': 4, 'y': 5}}])
#         self.assertEqual(flat, [['a' , 'b' , 'c.x' , 'c.y' ],
#                                 [1   , 2   , None  , None  ],
#                                 [None, 3   , 4     , 5     ]])

#     def test_tablize_a_list_with_mixed_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([{'a': 1, 'b': 2},
#                                  {'b': 3, 'c': [4, 5]},
#                                  6])
#         self.assertEqual(flat, [[''  , 'a' , 'b' , 'c.0' , 'c.1'],
#                                 [None, 1   , 2   , None  , None ],
#                                 [None, None, 3   , 4     , 5    ],
#                                 [6   , None, None, None  , None ]])

#     def test_tablize_a_list_with_unicode_elements(self):
#         renderer = CSVRenderer(None)

#         flat = renderer.tablize([{u'a': 1, u'b': u'hello\u2014goodbye'}])
#         self.assertEqual(flat, [[u'a', u'b'            ],
#                                 [1   , u'hello—goodbye']])

#     def test_render_a_list_with_unicode_elements(self):
#         renderer = CSVRenderer(None)

#         dump = renderer.render([{u'a': 1, u'b': u'hello\u2014goodbye', u'c': 'http://example.com/'}])
#         self.assertEqual(dump, (u'a,b,c\r\n1,hello—goodbye,http://example.com/\r\n').encode('utf-8'))

