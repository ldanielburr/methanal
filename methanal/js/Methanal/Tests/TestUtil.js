// import Divmod.UnitTest
// import Divmod.MockBrowser
// import Methanal.Util
// import Methanal.Tests.Util



Divmod.UnitTest.TestCase.subclass(Methanal.Tests.TestUtil, 'TestUtil').methods(
    /**
     * L{Methanal.Util.strToInt} converts a base-10 integer value, represented as a
     * C{String}, to an C{Integer}.
     */
    function test_strToInt(self) {
        var CASES = [
            ['1234', 1234],
            ['01234', 1234],
            ['001234', 1234],
            ['019', 19],
            ['123abc', undefined],
            ['abc123', undefined],
            ['0x123', undefined]];

        for (var i = 0; i < CASES.length; ++i) {
            var input = CASES[i][0];
            var expected = CASES[i][1];
            var actual = Methanal.Util.strToInt(input);
            self.assert(expected === actual, 'input = ' + input + ' :: expected = ' + expected + ' :: actual = ' + actual);
        }
    },


    /**
     * Applies a function of two arguments cumulatively to the elements of a
     * list from left to right, so as to reduce the list to a single value.
     */
    function test_reduce(self) {
        var reduce = Methanal.Util.reduce;

        function add(x, y) {
            return x + y;
        }

        function multiply(x, y) {
            return x * y;
        }

        self.assertIdentical(reduce(add, [1, 2, 3]), 6);
        self.assertIdentical(reduce(multiply, [1, 2, 3], 10), 60);
        self.assertThrows(Error, function () { return reduce(add, []); });
        self.assertIdentical(reduce(add, [], 10), 10);
        self.assertIdentical(reduce(add, [10]), 10);
    },


    /**
     * Test L{Methanal.Util._reprString} correctly escapes various whitespace
     * characters.
     */
    function test_reprString(self) {
        var s = '\r\n\f\b\t';
        var repr = Methanal.Util._reprString(s);
        var expected = "\"\\r\\n\\f\\b\\t\"";
        self.assertIdentical(repr, expected);
    },
    

    /**
     * Right justifying a string pads it with the first character of the fill
     * character parameter to the specified length.
     */
    function test_rjust(self) {
        var rjust = Methanal.Util.rjust;
        self.assertIdentical(rjust('a', 0), 'a');
        self.assertIdentical(rjust('a', 1), 'a');
        self.assertIdentical(rjust('a', 2), ' a');
        self.assertIdentical(rjust('a', 2, 'b'), 'ba');
        self.assertIdentical(rjust('a', 3, 'b'), 'bba');
        self.assertIdentical(rjust('a', 3, 'b'), 'bba');
        self.assertIdentical(rjust('a', 3, 'xy'), 'xxa');
        var s = 'a'
        self.assertIdentical(rjust(s, 2), ' a');
        self.assertIdentical(s, 'a');
    },


    /**
     * Applying a function over a sequence. Passing a non-function argument
     * throws an error.
     */
    function test_map(self) {
        var seq = [1, 2, 3];
        function square(n) {
            return n * n;
        }
        var result = Methanal.Util.map(square, seq);
        self.assertArraysEqual(result, [1, 4, 9]);

        self.assertThrows(Error,
            function () { Methanal.Util.map(null, seq); });
    },
    
    
    /**
     * Find the quotient and remainder of two numbers.
     */
    function test_divmod(self) {
        self.assertArraysEqual(
            Methanal.Util.divmod(12, 12),
            [1, 0]);
        self.assertArraysEqual(
            Methanal.Util.divmod(0, 12),
            [0, 0]);
        self.assertArraysEqual(
            Methanal.Util.divmod(1, 12),
            [0, 1]);
        self.assertArraysEqual(
            Methanal.Util.divmod(23, 12),
            [1, 11]);
    });



Divmod.UnitTest.TestCase.subclass(Methanal.Tests.TestUtil, 'TestStringSet').methods(
    /**
     * Supplying no parameters creates an empty set.
     */
    function test_empty(self) {
        var s = Methanal.Util.StringSet();
        s.each(function () {
            self.assert(false, 'Set is not empty');
        });
    },
    

    /**
     * L{Methanal.Util.StringSet.each} applies a function over all elements
     * of the set.
     */
    function test_each(self) {
        var called = 0;
        var values = ['a', 'b'];
        var s = Methanal.Util.StringSet(values);
        s.each(function (name) {
            var index = Methanal.Util.arrayIndexOf(values, name);
            self.assert(index !== -1, '"' + name + '" should be in the set!');
            values.splice(index, 1);
            called += 1;
        });
        self.assertIdentical(called, 2);
        self.assertIdentical(values.length, 0);
    },
    

    /**
     * L{Methanal.Util.StringSet.contains} correctly reports the presence of
     * a value in the set.
     */
    function test_contains(self) {
        var s = Methanal.Util.StringSet(['a', 'b']);
        self.assertIdentical(s.contains('a'), true);
        self.assertIdentical(s.contains('b'), true);
        self.assertIdentical(s.contains('c'), false);
    });



/**
 * Tests for L{Methanal.Util.Time}.
 *
 * @type _knownTime: L{Methanal.Util.Time}
 * @ivar _knownTime: A known point in time
 */
Divmod.UnitTest.TestCase.subclass(Methanal.Tests.TestUtil, 'TestTime').methods(
    function setUp(self) {
        self._knownTime = Methanal.Util.Time.fromDate(
            new Date(2009, 8, 6, 1, 36, 23, 2));
    },


    /**
     * L{Methanal.Util.TimeDelta} correctly specifies a given duration in
     * milliseconds.
     */
    function test_timedelta(self) {
        var td = Methanal.Util.TimeDelta({'days': 1});
        self.assertIdentical(td, 1000 * 3600 * 24);

        var td = Methanal.Util.TimeDelta({'days': -1});
        self.assertIdentical(td, 1000 * 3600 * -24);

        var td = Methanal.Util.TimeDelta({'days': 1,
                                          'hours': 2});
        self.assertIdentical(td, 1000 * 3600 * 26);

        var td = Methanal.Util.TimeDelta({'days': 1,
                                          'hours': 2,
                                          'minutes': 3});
        self.assertIdentical(td, 1000 * (3600 * 26 + 60 * 3));

        var td = Methanal.Util.TimeDelta({'days': 1,
                                          'hours': 2,
                                          'minutes': 3,
                                          'seconds': 4});
        self.assertIdentical(td, 1000 * (3600 * 26 + 60 * 3 + 4));

        var td = Methanal.Util.TimeDelta({'days': 1,
                                          'hours': 2,
                                          'minutes': 3,
                                          'seconds': 4,
                                          'milliseconds': 5});
        self.assertIdentical(td, 1000 * (3600 * 26 + 60 * 3 + 4) + 5);
    },


    /**
     * L{Methanal.Util.Time.guess} creates a L{Methanal.Util.Time} instance
     * when given an input format it can parse.
     */
    function test_guess(self) {
        function assertTimeParsed(data, timestamp) {
            var time = Methanal.Util.Time.guess(data);
            self.assertIdentical(time._oneDay, true);
            self.assertIdentical(time.asTimestamp(), timestamp);
        };

        assertTimeParsed('2009/9/1',   1251756000000);
        assertTimeParsed('2009.09.01', 1251756000000);
        assertTimeParsed('2009-09-01', 1251756000000);
        assertTimeParsed('1/9/2009',   1251756000000);
        assertTimeParsed('01.09.2009', 1251756000000);
        assertTimeParsed('01-09-2009', 1251756000000);
        assertTimeParsed('1/9/2009',   1251756000000);
        assertTimeParsed('29/2/2008',  1204236000000);
    },

    
    /**
     * L{Methanal.Util.Time.guess} throws L{Methanal.Util.TimeParseError} when
     * the input is not in any recognisable format, and reraises the original
     * exception if something other than L{Methanal.Util.TimeParseError} occurs.
     */
    function test_guessFailure(self) {
        function assertTimeParseError(data) {
            self.assertThrows(
                Methanal.Util.TimeParseError,
                function() { return Methanal.Util.Time.guess(data); });
        };

        assertTimeParseError('');
        assertTimeParseError('hello');
        assertTimeParseError('1/2/3');
        assertTimeParseError('2009/01');
        assertTimeParseError('2009/01');
        assertTimeParseError('2009/01/32');
        assertTimeParseError('2009/02/29');

        self.assertThrows(
            TypeError,
            function() { return Methanal.Util.Time.guess(undefined); });
    },


    /**
     * Create a L{Methanal.Util.Time} instance from a C{Date}.
     */
    function test_fromDate(self) {
        var d = new Date();
        var t = Methanal.Util.Time.fromDate(d);
        self.assertIdentical(t.asTimestamp(), d.getTime());
    },


    /**
     * Create a L{Methanal.Util.Time} instance from a valid relative time
     * reference, while invalid references throw
     * L{Methanal.Util.TimeParseError}.
     */
    function test_fromRelative(self) {
        var today = self._knownTime;

        var t = Methanal.Util.Time.fromRelative('tomorrow', today);
        self.assertIdentical(t.asHumanly(), 'Mon, 7 Sep 2009');
        var t = Methanal.Util.Time.fromRelative('yesterday', today);
        self.assertIdentical(t.asHumanly(), 'Sat, 5 Sep 2009');
        var t = Methanal.Util.Time.fromRelative('today', today);
        self.assertIdentical(t.asHumanly(), 'Sun, 6 Sep 2009');

        var t = Methanal.Util.Time.fromRelative('sun', today);
        self.assertIdentical(t.asHumanly(), 'Sun, 13 Sep 2009');
        var t = Methanal.Util.Time.fromRelative('mon', today);
        self.assertIdentical(t.asHumanly(), 'Mon, 7 Sep 2009');
        var t = Methanal.Util.Time.fromRelative('satur', today);
        self.assertIdentical(t.asHumanly(), 'Sat, 12 Sep 2009');

        self.assertThrows(
            Methanal.Util.TimeParseError,
            function() {
                return Methanal.Util.Time.fromRelative('', today);
            });
        self.assertThrows(
            Methanal.Util.TimeParseError,
            function() {
                return Methanal.Util.Time.fromRelative('hello', today);
            });
    },


    /**
     * Create a L{Methanal.Util.Time} instance from a timestamp in milliseconds.
     */
    function test_fromTimestamp(self) {
        var t = Methanal.Util.Time.fromTimestamp(1251759723000);
        self.assertIdentical(t.asHumanly(), 'Tue, 1 Sep 2009 01:02:03 am');
    },


    /**
     * L{Methanal.Util.Time.asDate} converts a Time into a C{Date} representing
     * the same time.
     */
    function test_asDate(self) {
        var t = Methanal.Util.Time();
        var d = t.asDate();
        self.assertIdentical(t.asTimestamp(), d.getTime());
    },


    /**
     * L{Methanal.Util.Time.asTimestamp} converts a Time into the number of
     * milliseconds elapsed since the epoch.
     */
    function test_asTimestamp(self) {
        self.assertIdentical(self._knownTime.asTimestamp(), 1252193783002);
    },


    /**
     * L{Methanal.Util.Time.asHumanly} converts a Time into a human-readable
     * string. Times that have been truncated to a date have an appropriately
     * accurate human-readable version.
     */
    function test_asHumanly(self) {
        self.assertIdentical(
            self._knownTime.asHumanly(), 'Sun, 6 Sep 2009 01:36:23 am');
        self.assertIdentical(
            self._knownTime.asHumanly(true), 'Sun, 6 Sep 2009 01:36:23');
        self.assertIdentical(
            self._knownTime.oneDay().asHumanly(), 'Sun, 6 Sep 2009');

        var t;

        t = Methanal.Util.Time.fromDate(new Date(2000, 0, 1, 0, 1, 2));
        self.assertIdentical(
            t.asHumanly(), 'Sat, 1 Jan 2000 12:01:02 am');
        self.assertIdentical(
            t.asHumanly(true), 'Sat, 1 Jan 2000 00:01:02');

        t = Methanal.Util.Time.fromDate(new Date(2000, 0, 1, 12, 13, 14));
        self.assertIdentical(
            t.asHumanly(), 'Sat, 1 Jan 2000 12:13:14 pm');
        self.assertIdentical(
            t.asHumanly(true), 'Sat, 1 Jan 2000 12:13:14');

        t = Methanal.Util.Time.fromDate(new Date(2000, 0, 1, 22, 23, 24));
        self.assertIdentical(
            t.asHumanly(), 'Sat, 1 Jan 2000 10:23:24 pm');
        self.assertIdentical(
            t.asHumanly(true), 'Sat, 1 Jan 2000 22:23:24');
    },


    /**
     * L{Methanal.Util.Time.oneDay} truncates a Time to only a date.
     */
    function test_oneDay(self) {
        var t = Methanal.Util.Time();
        var od = t.oneDay().asDate();
        t = t.asDate();
        self.assertIdentical(od.getFullYear(), t.getFullYear());
        self.assertIdentical(od.getMonth(), t.getMonth());
        self.assertIdentical(od.getDate(), t.getDate());
        self.assertIdentical(od.getHours(), 0);
        self.assertIdentical(od.getMinutes(), 0);
        self.assertIdentical(od.getSeconds(), 0);
        self.assertIdentical(od.getMilliseconds(), 0);
    },

    
    /**
     * L{Methanal.Util.Time.offset} offsets a Time by the given number of
     * milliseconds.
     */
    function test_offset(self) {
        var t = self._knownTime.offset(Methanal.Util.TimeDelta({'days': -1}));
        self.assertIdentical(t.asTimestamp(), 1252107383002);
        self.assertIdentical(t.oneDay().asHumanly(), 'Sat, 5 Sep 2009');

        var t = self._knownTime.offset(Methanal.Util.TimeDelta({'days': 1}));
        self.assertIdentical(t.asTimestamp(), 1252280183002);
        self.assertIdentical(t.oneDay().asHumanly(), 'Mon, 7 Sep 2009');
    });



/**
 * Tests for L{Methanal.Util.Throbber}.
 */
Divmod.UnitTest.TestCase.subclass(Methanal.Tests.TestUtil, 'TestThrobber').methods(
    function _createThrobber(self, toggleDisplay) {
        var idNodes = {
            'throbber': Methanal.Tests.Util.MockNode('foo')};
        var widget = Methanal.Tests.Util.MockWidget(idNodes);
        var throbber = Methanal.Util.Throbber(widget, toggleDisplay);
        return throbber;
    },


    /**
     * Creating a throbber finds a DOM node with the ID "throbber".
     */
    function test_create(self) {
        var throbber = self._createThrobber();
        self.assertIdentical(throbber._node.name, 'foo');
    },
    

    /**
     * Starting and stopping the throbber, under normal conditions, adjusts the
     * throbber node's visibility style.
     */
    function test_startStop(self) {
        var throbber = self._createThrobber();
        throbber.start();
        self.assertIdentical(throbber._node.style.visibility, 'visible');
        throbber.stop();
        self.assertIdentical(throbber._node.style.visibility, 'hidden');
    },


    /**
     * Specifying the C{toggleDisplay} augments the behaviour of the C{stop}
     * and C{start} methods.
     */
    function test_toggleDisplay(self) {
        var throbber = self._createThrobber('foo');
        throbber.start();
        self.assertIdentical(throbber._node.style.visibility, 'visible');
        self.assertIdentical(throbber._node.style.display, 'foo');
        throbber.stop();
        self.assertIdentical(throbber._node.style.visibility, 'hidden');
        self.assertIdentical(throbber._node.style.display, 'none');
    });



/**
 * Tests for L{Methanal.Util.DOMBuilder}.
 */
Divmod.UnitTest.TestCase.subclass(Methanal.Tests.TestUtil, 'TestDOMBuilder').methods(
    /**
     * Helper function for building a node using C{DOMBuilder}.
     */
    function _build(self/*, ...*/) {
        var T = Methanal.Util.DOMBuilder(document);
        var args = [];
        for (var i = 1; i < arguments.length; ++i) {
            args.push(arguments[i]);
        }
        return T.apply(null, args);
    },


    /**
     * Building an element with a tag name.
     */
    function test_element(self) {
        var node = self._build('foo');
        self.assertIdentical(node.tagName, 'FOO');
    },


    /**
     * Building an element with children that are strings results in text nodes.
     */
    function test_textChild(self) {
        var node = self._build('foo', {}, ['hello']);
        self.assertIdentical(node.childNodes.length, 1);
        self.assertIdentical(node.childNodes[0].nodeType, node.TEXT_NODE);
        self.assertIdentical(node.childNodes[0].nodeValue, 'hello');
    },


    /**
     * Passing an attribute mapping results in an element with the specified
     * attributes.
     */
    function test_attributes(self) {
        var node = self._build('foo',
            {'id':    'an_id',
             'class': 'a_class',
             'foo':   'bar'},
            ['hello']);

        self.assertIdentical(node.getAttribute('id'), 'an_id');
        self.assertIdentical(node.getAttribute('class'), 'a_class');
        self.assertIdentical(node.getAttribute('foo'), 'bar');
    });
