import unittest
import lxml.etree

from extracty import precedings

def doc(text):
    return lxml.etree.fromstring(text)

class PrecedingsTests(unittest.TestCase):

    def assertIterateOver(self, doc, xpath, tagnames, **kw):
        e = doc.xpath(xpath)[0]
        found = [x.tag for x in precedings(e, **kw)]
        self.assertEqual(tagnames, found)

    def test_flat(self):
        d = doc('''
        <doc>
            <a/>
            <b/>
            <c/>
            <d/>
        </doc>
        ''')
        self.assertIterateOver(d, '/doc/a', ['doc'])
        self.assertIterateOver(d, '/doc/b', ['a', 'doc'])
        self.assertIterateOver(d, '/doc/c', ['b', 'a', 'doc'])
        self.assertIterateOver(d, '/doc/d', ['c', 'b', 'a', 'doc'])

    def test_nested_siblings(self):
        d = doc('''
        <doc>
            <a/>
            <b>
                <b1/>
            </b>
            <c>
                <c1/>
            </c>
            <d/>
        </doc>
        ''')
        self.assertIterateOver(d, '/doc/a', ['doc'])
        self.assertIterateOver(d, '/doc/b', ['a', 'doc'])
        self.assertIterateOver(d, '/doc/b/b1', ['b', 'a', 'doc'])
        self.assertIterateOver(d, '/doc/c', ['b1', 'b', 'a', 'doc'])
        self.assertIterateOver(d, '/doc/c/c1', ['c', 'b1', 'b', 'a', 'doc'])
        self.assertIterateOver(d, '/doc/d', ['c1', 'c', 'b1', 'b', 'a', 'doc'])

    def test_before(self):
        d = doc('''
        <doc>
            <a/>
            <b>
                <b1/>
            </b>
            <c>
                <c1/>
            </c>
            <d/>
        </doc>
        ''')
        before = lambda x: x == d.xpath('/doc/b/b1')[0]
        self.assertIterateOver(d, '/doc/a', ['doc'], before=before)
        self.assertIterateOver(d, '/doc/b', ['a', 'doc'], before=before)
        self.assertIterateOver(d, '/doc/b/b1', ['b', 'a', 'doc'], before=before)
        self.assertIterateOver(d, '/doc/c', [], before=before)
        self.assertIterateOver(d, '/doc/c/c1', ['c'], before=before)
        self.assertIterateOver(d, '/doc/d', ['c1', 'c'], before=before)

    def test_skip(self):
        d = doc('''
        <doc>
            <a/>
            <b>
                <b1/>
            </b>
            <c>
                <c1/>
            </c>
            <d/>
        </doc>
        ''')
        skip = lambda x: x == d.xpath('/doc/b')[0]
        self.assertIterateOver(d, '/doc/a', ['doc'], skip=skip)
        self.assertIterateOver(d, '/doc/b', ['a', 'doc'], skip=skip)
        self.assertIterateOver(d, '/doc/b/b1', [], skip=skip)
        self.assertIterateOver(d, '/doc/c', ['a', 'doc'], skip=skip)
        self.assertIterateOver(d, '/doc/c/c1', ['c', 'a', 'doc'], skip=skip)
        self.assertIterateOver(d, '/doc/d', ['c1', 'c', 'a', 'doc'], skip=skip)
