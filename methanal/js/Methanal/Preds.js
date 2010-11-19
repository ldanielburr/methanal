// import Methanal.Util



/**
 * Gather the results of functions and combine them.
 *
 * @type  c: C{Function} taking one C{Array} parameter
 * @param c: Combining function.
 *
 * @type  fs: C{Array} of C{Function}s
 * @param fs: Functions to gather the results of. Each function is called with
 *     the same arguments.
 *
 * @rtype: C{Function} taking varargs.
 * @return: Function that can be called, with varargs, to perform the combining.
 */
Methanal.Preds.combine = function combine(c, fs) {
    return function _combine(/*...*/) {
        var vs = [];
        for (var i = 0; i < fs.length; ++i) {
            vs.push(fs[i].apply(null, arguments));
        }
        return c(vs);
    };
};



/**
 * Logically AND values together.
 *
 * @type  values: C{Array} of C{Boolean}.
 */
Methanal.Preds.AND = function AND(values) {
    return Methanal.Util.reduce(
        function _and(a, b) { return a && b; }, values);
};

Methanal.Preds.intersection = Methanal.Preds.AND;



/**
 * Logically OR values together.
 *
 * @type  values: C{Array} of C{Boolean}.
 */
Methanal.Preds.OR = function OR(values) {
    return Methanal.Util.reduce(
        function _or(a, b) { return a || b; }, values);
};

Methanal.Preds.union = Methanal.Preds.OR;



/**
 * Logically XOR values together.
 *
 * @type  values: C{Array} of C{Boolean}.
 */
Methanal.Preds.XOR = function XOR(values) {
    return Methanal.Util.reduce(
        function _xor(a, b) { return !!(a ^ b); }, values);
};

Methanal.Preds.difference = Methanal.Preds.XOR;



/**
 * Predicate is inverted.
 */
Methanal.Preds.invert = function (p) {
    return function (/*...*/) {
        return !p.apply(null, arguments);
    };
};



/**
 * Value is C{true} when evaluated as a boolean.
 */
Methanal.Preds.isTrue = function isTrue(value) {
    return !!value;
};



/**
 * Value is C{false} when evaluated as a boolean.
 */
Methanal.Preds.isFalse = function isFalse(value) {
    return !value;
};



/**
 * Value is identical to C{is}.
 */
Methanal.Preds.valueIs = function valueIs(is, value) {
    return value === is;
};



/**
 * Value is defined and has non-zero, positive length.
 */
Methanal.Preds.hasLength = function hasLength(value) {
    return Methanal.Preds.isTrue(value) && value.length > 0;
};



/**
 * Value is not defined or has zero length.
 */
Methanal.Preds.empty = function empty(value) {
    return Methanal.Preds.isFalse(value) || value.length === 0;
};



/**
 * Value has a length of exactly C{n}.
 */
Methanal.Preds.lengthOf = function lengthOf(n, value) {
    return value != null && value.length === n;
};



/**
 * Value has a length of at least C{n}.
 */
Methanal.Preds.lengthAtLeast = function lengthAtLeast(n, value) {
    return value != null && value.length >= n;
};



/**
 * Value has a length of at most C{n}.
 */
Methanal.Preds.lengthAtMost = function lengthAtMost(n, value) {
    return value != null && value.length <= n;
};



/**
 * Value is not null.
 */
Methanal.Preds.notNull = function notNull(value) {
    return value !== null;
};



/**
 * Value is within a given range.
 *
 * @type  a: C{number}
 * @param a: The lower-bound inclusive value of the range
 *
 * @type  b: C{number}
 * @param b: The upper-bound inclusive value of the range
 */
Methanal.Preds.between = function between(a, b, value) {
    return value >= a && value <= b;
};



/**
 * Value is less than C{n}.
 */
Methanal.Preds.lessThan = function lessThan(n, value) {
    return value < n;
};



/**
 * Value is not greater than (or, less than or equal to) C{n}.
 */
Methanal.Preds.notGreaterThan = function notGreaterThan(n, value) {
    return value <= n;
};



/**
 * Value is greater than C{n}.
 */
Methanal.Preds.greaterThan = function greaterThan(n, value) {
    return value > n;
};



/**
 * Value is not less than (or, greater than or equal to) C{n}.
 */
Methanal.Preds.notLessThan = function notLessThan(n, value) {
    return value >= n;
};



/**
 * Value is one of a given set.
 *
 * @type  values: C{Array}
 * @param values: Acceptable values
 */
Methanal.Preds.oneOf = function oneOf(values, value) {
    return Methanal.Util.arrayIndexOf(values, value) !== -1;
};



/**
 * Value contains only characters matching a regular expression character
 * class.
 *
 * @type expn: C{String}
 */
Methanal.Preds.isChars = function isChars(expn, value) {
    var filterExpn = new RegExp('^(' + expn + ')+$');
    return filterExpn.test(value);
};



/**
 * Value matches a regular expression.
 *
 * @type expn: C{RegExp}
 */
Methanal.Preds.regex = function regex(expn, value) {
    return expn.test(value);
};



/**
 * Value is within a timedelta and a start date.
 *
 * @type timedelta: L{Methanal.Util.TimeDelta}
 *
 * @type start: L{Methanal.Util.Time}
 *
 * @type value: C{Date} or C{Number}
 */
Methanal.Preds.dateSince = function dateSince(timedelta, start, value) {
    var t = start.offset(timedelta).asDate();
    // Make some lives easier.
    if (value && !(value instanceof Date)) {
        value = new Date(value);
    }
    return timedelta.offset > 0 ? value > t : value < t;
};



/**
 * Value is within a timedelta and the current time.
 *
 * @type timedelta: L{Methanal.Util.TimeDelta}
 *
 * @type value: C{Date}
 */
Methanal.Preds.dateWithin = function dateWithin(timedelta, value) {
    return Methanal.Preds.dateSince(timedelta, Methanal.Util.Time(), value);
};



/**
 * Value is a future date.
 *
 * @type value: C{Date}
 */
Methanal.Preds.futureDate = function futureDate(value) {
    return (new Date()) <= value;
};



/**
 * Value is a past date.
 *
 * @type value: C{Date}
 */
Methanal.Preds.pastDate = Methanal.Preds.invert(Methanal.Preds.futureDate);
