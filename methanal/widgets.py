"""
Utility widgets designed to operate outside of forms.
"""
import time
from warnings import warn

from zope.interface import implements

from epsilon.structlike import record
from epsilon.extime import FixedOffset, Time

from twisted.internet.defer import maybeDeferred
from twisted.python.components import registerAdapter
from twisted.python.versions import Version
from twisted.python.deprecate import deprecated

from axiom.item import SQLAttribute

from nevow.inevow import IAthenaTransportable
from nevow.tags import invisible
from nevow.athena import expose, LiveElement
from nevow.page import renderer

from xmantissa.ixmantissa import IWebTranslator, IColumn as mantissaIColumn
from xmantissa.webtheme import ThemedElement

from methanal.imethanal import IColumn
from methanal.util import getArgsDict
from methanal.view import (liveFormFromAttributes, containerFromAttributes,
    ObjectSelectInput, SimpleForm, FormInput, LiveForm, SubmitAction,
    ActionButton, ActionContainer)
from methanal.model import Value
from methanal.errors import InvalidIdentifier



class TimeTransportable(object):
    """
    An C{IAthenaTransportable} implementation for L{Time} instances.
    """
    implements(IAthenaTransportable)

    jsClass = u'Methanal.Util.Time.fromTimestamp'


    def __init__(self, time):
        self.time = time


    def getInitialArguments(self):
        return [self.time.asPOSIXTimestamp() * 1000]

registerAdapter(TimeTransportable, Time, IAthenaTransportable)



class AttributeColumn(object):
    """
    An L{methanal.imethanal.IColumn} provider for Axiom attributes.

    @type attribute: L{axiom.attributes.SQLAttribute}

    @type attributeID: C{str}
    @param attributeID: Attribute column identifier, defaults to the attribute
        name
    """
    implements(IColumn)

    def __init__(self, attribute, attributeID=None, title=None):
        self.attribute = attribute
        if attributeID is None:
            attributeID = attribute.attrname
        self.attributeID = attributeID
        if title is None:
            title = getattr(self.attribute, 'doc', None)
            if not title:
                title = unicode(attributeID, 'ascii')
        self.title = title


    # IColumn

    def extractValue(self, model, item):
        """
        Extract a simple value for this column from a given item, suitable for
        serialization via Athena's client-communication layer.

        This implementation differs from the one in Mantissa in that it uses
        C{getattr}, instead of C{__get__}, thus allowing it to work on items
        wrapped in a C{SharedProxy}.

        @param model: The query list object requesting the value

        @param item: An instance of the class that this L{AttributeColumn}'s
            L{attribute} was taken from, to retrieve the value from

        @return: A value of an attribute of C{item}, of a type dependent upon
            this L{AttributeColumn}'s L{attribute}
        """
        return getattr(item, self.attribute.attrname)


    def extractLink(self, model, item):
        webTranslator = IWebTranslator(item.store, None)
        if webTranslator is not None:
            return unicode(webTranslator.toWebID(item), 'ascii')
        return None


    def getType(self):
        return type(self.attribute).__name__

registerAdapter(AttributeColumn, SQLAttribute, IColumn)



class LinkColumn(object):
    """
    Provide a custom link for an existing L{IColumn}.

    @type column: L{IColumn}
    @ivar column: Existing column to provide a custom link for

    @ivar extractLink: A callable matching the signature of
        L{IColumn.extractLink}
    """
    implements(IColumn)

    def __init__(self, column, extractLink):
        self._column = column
        self.extractLink = extractLink
        self.extractValue = self._column.extractValue
        self.getType = self._column.getType
        self.attributeID = self._column.attributeID
        self.title = self._column.title



class Row(object):
    """
    A L{Table} row.

    @ivar id: Row identifier

    @type cells: Mapping of C{unicode} to L{Cell}
    @ivar cells: Mapping of column identifiers to cell objects
    """
    def __init__(self, item, index, table):
        self.id = index
        self.cells = dict()
        for column in table.columns:
            columnID = unicode(column.attributeID, 'ascii')
            value = column.extractValue(table, item)
            link = column.extractLink(table, item)
            self.cells[columnID] = Cell(value, link)



class RowTransportable(record('row')):
    """
    An C{IAthenaTransportable} implementation for L{Row} instances.
    """
    implements(IAthenaTransportable)

    jsClass = u'Methanal.Widgets.Row'

    def getInitialArguments(self):
        return [self.row.id, self.row.cells]

registerAdapter(RowTransportable, Row, IAthenaTransportable)



class Cell(object):
    """
    A L{Table} cell.

    @ivar value: Cell value

    @type link: C{unicode}
    @ivar link: Hyperlink for the cell, or C{None} if the cell is not
        hyperlinked
    """
    def __init__(self, value, link):
        self.value = value
        self.link = link



class CellTransportable(record('cell')):
    """
    An C{IAthenaTransportable} implementation for L{Cell} instances.
    """
    implements(IAthenaTransportable)

    jsClass = u'Methanal.Widgets.Cell'

    def getInitialArguments(self):
        return [self.cell.value, self.cell.link]

registerAdapter(CellTransportable, Cell, IAthenaTransportable)



class ColumnTransportable(record('column')):
    """
    An C{IAthenaTransportable} implementation for L{IColumn}.
    """
    implements(IAthenaTransportable)

    columnTypes = {
        'text': u'Methanal.Widgets.TextColumn',
        'integer': u'Methanal.Widgets.IntegerColumn',
        'ieee754_double': u'Methanal.Widgets.FloatColumn',
        'boolean': u'Methanal.Widgets.BooleanColumn',
        'timestamp': u'Methanal.Widgets.TimestampColumn'}

    @property
    def jsClass(self):
        """
        Determine the Javascript class name based on the column type.
        """
        columnType = self.column.getType()
        if columnType is None:
            columnType = 'text'
        return self.columnTypes.get(columnType)


    def getInitialArguments(self):
        columnID = unicode(self.column.attributeID, 'ascii')
        columnType = self.column.getType()
        if columnType is not None:
            columnType = unicode(columnType, 'ascii')
        return [columnID, self.column.title, columnType]

registerAdapter(ColumnTransportable, IColumn, IAthenaTransportable)



class Table(ThemedElement):
    """
    Tabulate data with column values derived from Items.

    @type items: C{sequence} of C{axiom.item.Item}

    @type columns: C{sequence} of C{methanal.imethanal.IColumn}
    """
    jsClass = u'Methanal.Widgets.Table'
    fragmentName = 'methanal-table'


    def __init__(self, items, columns, **kw):
        super(Table, self).__init__(**kw)
        self.items = list(items)
        self.columns = [IColumn(column) for column in columns]


    def getInitialArguments(self):
        return [getArgsDict(self)]


    def getArgs(self):
        return {u'columns': self.columns,
                u'rows': [Row(item, index, self)
                          for index, item in enumerate(self.items)]}


    @expose
    def performAction(self, name, rowIndex):
        method = getattr(self, 'action_' + name)
        item = self.items[rowIndex]
        return method(item)



class QueryList(ThemedElement):
    """
    A widget that displays data tabulated according to a set of columns.

    Actions are supported too.
    """
    jsClass = u'Methanal.Widgets.QueryList'
    fragmentName = 'methanal-table'

    def __init__(self, rows, columns, webTranslator=None, timezone=None, **kw):
        warn('QueryList is deprecated, use methanal.widgets.Table instead')
        super(QueryList, self).__init__(**kw)

        self.rows = list(rows)
        def _adapt(col):
            try:
                return IColumn(col)
            except TypeError:
                col = mantissaIColumn(col)

            warn('use methanal.imethanal.IColumn instead of '
                 'xmantissa.ixmantissa.IColumn', DeprecationWarning, 2)
            return col

        columns = (_adapt(col) for col in columns)
        self.columns = [(col.attributeID.decode('ascii'), col)
                        for col in columns]
        self.webTranslator = webTranslator

        if timezone is None:
            hour, minute = divmod(time.timezone, -3600)
            timezone = FixedOffset(hour, minute)
            warn('not passing in timezone is deprecated', DeprecationWarning, 2)

        self.timezone = timezone


    def dictifyItem(self, item, index):
        def _formatValue(value):
            if isinstance(value, Time):
                return value.asDatetime(self.timezone).strftime(
                    '%a, %d %h %Y %H:%M:%S').decode('ascii')
            return value

        if isinstance(item, tuple):
            link, item = item
        else:
            if self.webTranslator is None:
                self.webTranslator = IWebTranslator(item.store)
            link = unicode(self.webTranslator.toWebID(item), 'ascii')

        d = dict((cid, _formatValue(col.extractValue(self, item)))
                 for (cid, col) in self.columns)
        d[u'__link__'] = link
        d[u'__id__'] = index

        return d


    def getInitialArguments(self):
        return [getArgsDict(self)]


    def getArgs(self):
        IDs = []
        aliases = {}
        for cid, col in self.columns:
            IDs.append(cid)
            if isinstance(col, AttributeColumn):
                alias = col.attribute.doc
            else:
                alias = col
            aliases[cid] = unicode(alias)

        return {u'columnIDs':     IDs,
                u'columnAliases': aliases,
                u'rows':          [self.dictifyItem(row, i)
                                   for i, row in enumerate(self.rows)]}


    @expose
    def performAction(self, name, rowIndex):
        method = getattr(self, 'action_' + name)
        item = self.rows[rowIndex]
        return method(item)



class FilterList(ThemedElement):
    """
    A filtering search widget.

    Essentially just a form that results in a server-side call, on submission,
    and a result widget.

    One particularly common application is a search widget: A form containing
    inputs representing fields to filter by, which, when submitted, results in
    a server-side database query and a QueryList widget.
    """
    jsClass = u'Methanal.Widgets.FilterList'
    fragmentName = 'methanal-filter-list'

    def __init__(self, form, resultWidget, title, **kw):
        """
        Initialise the filter widget.

        @type form: C{methanal.view.LiveForm}
        @param form: Form to display for filter inputs, the form's
            C{submitSuccess} client method will be passed the result
            widget; considering deriving client objects from
            C{Methanal.Widgets.FilterListForm}

        @type resultWidget: C{callable}
        @param resultWidget: A callable passed the result of C{form}'s
            callback and expected to return a renderable representing the
            filter results

        @type title: C{unicode}
        @param title: A title to display along with the filter widget
        """
        super(FilterList, self).__init__(**kw)
        self.form = form
        self.form.setFragmentParent(self)
        self.resultWidget = resultWidget
        self.title = title

        self.originalCallback = self.form.model.callback
        self.form.model.callback = self.filterCallback


    def filterCallback(self, **kw):
        """
        Handle form submission.

        Call the original form callback and create the result widget.

        @rtype: C{Deferred}
        """
        def makeResultWidget(data):
            w = self.resultWidget(data)
            w.setFragmentParent(self)
            return w

        return maybeDeferred(self.originalCallback, **kw
            ).addCallback(makeResultWidget)


    @renderer
    def formTitle(self, req, tag):
        return tag[self.title]


    @renderer
    def filterForm(self, req, tag):
        return tag[self.form]



class SimpleFilterList(FilterList):
    """
    A simple L{FilterList} implementation.

    Intended to generate a C{LiveForm} from a sequence of attributes, call a
    user-specified callback and display the results in a L{QueryList} with the
    desired columns.
    """
    def __init__(self, store, filterAttrs, callback, resultColumns,
                 timezone=None, webTranslator=None, **kw):
        """
        Initialise the filter widget.

        @type store: C{axiom.store.Store}
        @param store: Store that the specified attributes reside in

        @type filterAttrs: C{sequence} of Axiom attributes
        @param filterAttrs: The attributes to provide form inputs for the
            attributes to filter on

        @type callback: C{callable} returning an C{iterable} of
            C{axiom.item.Item}s
        @param callback: The callable that is triggered when the filter form
            is submitted, passed parameters named according to the
            attribute names specified by the attributes in L{filterAttrs},
            returning result items

        @type resultColumns: C{list} of L{methanal.imethanal.IColumn}
        @param resultColumns: Columns for display in the result widget

        @type timezone: C{tzinfo}
        @param timezone: Timezone used for displaying timestamps.

        @type webTranslator: L{xmantissa.ixmantissa.IWebTranslator}
        @param webTranslator: The translator used for linking items.
        """
        form = liveFormFromAttributes(store=store,
                                      attributes=filterAttrs,
                                      callback=callback,
                                      doc=u'Filter',
                                      timezone=timezone)
        form.jsClass = u'Methanal.Widgets.FilterListForm'

        resultWidget = lambda rows: QueryList(rows=rows,
                                              columns=resultColumns,
                                              webTranslator=webTranslator,
                                              timezone=timezone)

        super(SimpleFilterList, self).__init__(form=form,
                                               resultWidget=resultWidget,
                                               **kw)



class Rollup(ThemedElement):
    jsClass = u'Methanal.Widgets.Rollup'

    def __init__(self, fragmentParent=None, label=None):
        super(Rollup, self).__init__(fragmentParent=fragmentParent)
        self.label = label or u''
        self._rollupFactory = None


    def _getRollupFactory(self):
        if self._rollupFactory is None:
            self._rollupFactory = self.getDocFactory('methanal-rollup')
        return self._rollupFactory


    def makeRollup(self, summary, content):
        rollupFactory = self._getRollupFactory()
        rollupContent = invisible[
            rollupFactory.load(preprocessors=LiveElement.preprocessors)]
        rollupContent.fillSlots('label', self.label)
        rollupContent.fillSlots('summary', summary)
        rollupContent.fillSlots('content', content)
        return rollupContent


    @renderer
    def rollup(self, req, tag):
        summary = tag.onePattern('summary')
        content = tag.onePattern('content')
        tag[self.makeRollup(summary, content)]
        return self.liveElement(req, tag)



class SimpleRollup(Rollup):
    fragmentName = 'methanal-simple-rollup'

    def __init__(self, content=None, **kw):
        super(SimpleRollup, self).__init__(**kw)
        self.content = content


    def getInitialArguments(self):
        params = self.getParams()
        return [params]


    def getParams(self):
        return {}


    @renderer
    def rollup(self, req, tag):
        summary = tag.onePattern('summary')
        tag[self.makeRollup(summary, self.content)]
        return self.liveElement(req, tag)



class Lookup(FormInput):
    fragmentName = 'methanal-lookup'
    jsClass = u'Methanal.Widgets.Lookup'

    def __init__(self, form, populator, describer, objects=None, **kw):
        if objects is None:
            objects = []

        super(Lookup, self).__init__(**kw)

        self.form = form
        self.form.setFragmentParent(self)
        self.populator = populator
        self.describer = describer
        self.objects = objects


    @expose
    def populate(self, *a):
        self.objects = list(self.populator(*a))
        return list(enumerate(self.describer(o) for o in self.objects))


    @renderer
    def filterForm(self, req, tag):
        return tag[self.form]



class SimpleLookup(Lookup):
    def __init__(self, store, filterAttrs, timezone=None, **kw):
        fact = lambda model: SimpleForm(store=store, model=model)
        form = containerFromAttributes(containerFactory=fact,
                                       store=store,
                                       attributes=filterAttrs,
                                       callback=None,
                                       doc=None,
                                       timezone=timezone)
        form.jsClass = u'Methanal.Widgets.SimpleLookupForm'

        super(SimpleLookup, self).__init__(form=form, **kw)

        form.model.params['__results'] = Value(name='__results', doc=u'Result')

        values = [(o, self.describer(o)) for o in self.objects]
        ObjectSelectInput(parent=form, name='__results', values=values)



class ModalDialog(ThemedElement):
    """
    Modal dialog widget.

    @type title: C{unicode}
    @ivar title: Dialog title

    @type content: C{nevow.athena.LiveElement}
    @ivar content: Athena widget to serve as the content for the dialog
    """
    jsClass = u'Methanal.Widgets.ModalDialog'
    fragmentName = 'methanal-modal-dialog'

    def __init__(self, title, content, **kw):
        super(ModalDialog, self).__init__(**kw)
        self.title = title
        self.content = content


    @renderer
    def dialogTitle(self, req, tag):
        return tag[self.title]


    @renderer
    def dialogContent(self, req, tag):
        self.content.setFragmentParent(self)
        return tag[self.content]



class CancelAction(ActionButton):
    """
    Form action for dismissing a dialog.
    """
    jsClass = u'Methanal.Widgets.CancelAction'
    defaultName = u'Cancel'
    allowViewOnly = True



class ModalDialogForm(LiveForm):
    """
    L{methanal.view.LiveForm} for L{methanal.widgets.ModalDialog}.
    """
    jsClass = u'Methanal.Widgets.ModalDialogForm'

    def __init__(self, actions=None, **kw):
        if actions is None:
            actions = ActionContainer(
                actions=[SubmitAction(name=u'OK'), CancelAction()])
        super(ModalDialogForm, self).__init__(actions=actions, **kw)



class TabView(ThemedElement):
    """
    A tab container, visually displayed as a horizontal tab bar.

    Only one sub-container can be visible at a time.

    @type tabs: C{list} of L{methanal.widgets.Tab}
    @ivar tabs: Tabs to manage.

    @type topLevel: C{bool}
    @ivar topLevel: Is this a top-level TabView? Top-level TabViews will use
        the fragment part of the current URL to track which tab is selected,
        this behaviour supercedes L{Tab.selected}.

    @type _tabsByID: C{dict} mapping C{unicode} to L{methanal.widgets.Tab}
    @ivar _tabsByID: Mapping of unique tab IDs to tabs currently being managed.

    @type _tabGroups: C{dict} mapping C{unicode} to
        L{methanal.widgets.TabGroup}
    @ivar _tabGroups: Mapping of tab group identifiers to tab groups.
    """
    fragmentName = 'methanal-tab-view'
    jsClass = u'Methanal.Widgets.TabView'

    def __init__(self, tabs, topLevel=False, **kw):
        """
        @type  tabs: C{list} of L{methanal.widgets.Tab} or
            L{methanal.widgets.TabGroup}.
        @param tabs: Tab or tab groups to manage.
        """
        super(TabView, self).__init__(**kw)
        self._tabsByID = {}
        self._tabGroups = {}
        self.tabs = []
        self.topLevel = topLevel

        for tabOrGroup in tabs:
            if isinstance(tabOrGroup, TabGroup):
                self._manageGroup(tabOrGroup)
                for tab in tabOrGroup.tabs:
                    self._manageTab(tab)
            else:
                self._manageTab(tabOrGroup)


    def __repr__(self):
        return '<%s topLevel=%r tabs=%r>' % (
            type(self).__name__,
            self.topLevel,
            self.tabs)


    def _manageGroup(self, group):
        """
        Begin managing a L{methanal.widgets.TabGroup}.

        Tabs contained in a group are B{not} managed automatically,
        L{_manageTab} should be called for each tab.
        """
        self._tabGroups[group.id] = group


    def _manageTab(self, tab, overwrite=False):
        """
        Begin managing a L{methanal.widgets.Tab} widget.

        If a tab identifier is already being managed it is released before
        managing the new widget.
        """
        if tab.id in self._tabsByID:
            self._releaseTab(self.getTab(tab.id))
        self._tabsByID[tab.id] = tab
        self.tabs.append(tab)
        group = self._tabGroups.get(tab.group)
        if group is not None:
            group._manageTab(tab)


    def _releaseTab(self, tab):
        """
        Stop managing a L{methanal.widgets.Tab} widget.
        """
        if tab not in self.tabs:
            raise ValueError(
                '%r is not managed by %r' % (tab.id, self))
        del self._tabsByID[tab.id]
        self.tabs.remove(tab)
        group = self._tabGroups.get(tab.group)
        if group is not None:
            group._releaseTab(tab)


    def getTab(self, id):
        """
        Get a L{methanal.widgets.Tab} by its unique identifier.
        """
        tab = self._tabsByID.get(id)
        if tab is None:
            raise InvalidIdentifier(
                u'%r is not a valid tab identifier in %r' % (id, self))
        return tab


    def getTabIDs(self):
        """
        Get a C{list} of all the tab IDs in the group.
        """
        return [tab.id for tab in self.tabs]


    def getGroup(self, id):
        """
        Get a L{methanal.widgets.TabGroup} by its unique identifier.
        """
        group = self._tabGroups.get(id)
        if group is None:
            raise InvalidIdentifier(
                u'%r is not a valid group identifier in %r' % (id, self))
        return group


    @deprecated(Version('methanal', 0, 2, 1))
    def appendTab(self, tab):
        """
        Append a L{methanal.widgets.Tab} widget.

        @return: A C{Deferred} that fires when the widget has been inserted on
            the client side.
        """
        return self.updateTabs([tab])


    def updateTabs(self, tabs, tabsToRemove=None):
        """
        Update many L{methanal.widgets.Tab} widgets.

        All tab widgets are passed to the client side, updated there (or
        appended if they didn't previously exist) and added to the relevant
        groups. Use L{methanal.widgets.TabGroup.mergeGroups} to simulate adding
        to an existing group.

        @return: A C{Deferred} that fires when the widgets have been updated on
            the client side.
        """
        for tab in tabs:
            self._manageTab(tab)
            tab.setFragmentParent(self)

        tabIDsToRemove = []
        if tabsToRemove is not None:
            tabIDsToRemove = [tab.id for tab in tabsToRemove]

        return self.callRemote(
            '_updateTabsFromServer', tabs, tabIDsToRemove, self._tabGroups)


    appendTabs = deprecated(Version('methanal', 0, 2, 1))(updateTabs)


    def removeTabs(self, tabs):
        """
        Remove many L{methanal.widgets.Tab} widgets.

        Empty groups, caused by removing all contained tabs, are removed too.

        @return: A C{Deferred} that fires when the widget has been removed on
            the client side.
        """
        tabIDs = []
        for tab in tabs:
            tabIDs.append(tab.id)
            self._releaseTab(tab)

        return self.callRemote('_removeTabsFromServer', tabIDs, self._tabGroups)


    def updateGroup(self, group):
        """
        Update a L{methanal.widgets.TabGroup} and its tabs.

        Tabs specified in C{group} will replace those previously specified by
        another group of the same name.

        @return: A C{Deferred} that fires when the widgets have been inserted on
            the client side.
        """
        try:
            oldGroup = self.getGroup(group.id)
        except InvalidIdentifier:
            oldGroup = None

        tabsToRemove = []
        if oldGroup is not None:
            tabsToRemove = map(
                self.getTab,
                set(oldGroup.getTabIDs()) - set(group.getTabIDs()))
            for tab in tabsToRemove:
                self._releaseTab(tab)

        self._manageGroup(group)
        return self.updateTabs(group.tabs, tabsToRemove)


    appendGroup = deprecated(Version('methanal', 0, 2, 1))(updateGroup)


    def getInitialArguments(self):
        return [
            dict.fromkeys(self._tabsByID.iterkeys(), True),
            self._tabGroups,
            self.topLevel]


    @renderer
    def tabContents(self, req, tag):
        def _tabs():
            for tab in self.tabs:
                tab.setFragmentParent(self)
                yield tab

        return tag[_tabs()]



class TabGroup(object):
    """
    Visually group labels of L{methanal.widgets.Tab}s together.

    @type id: C{unicode}
    @ivar id: Unique identifier.

    @type title: C{unicode}
    @ivar title: Title of the group, used by L{methanal.widgets.TabView} when
        constructing the tab list.

    @type tabs: C{list} of L{methanal.widgets.Tab}
    @ivar tabs: Tabs to group together.
    """
    implements(IAthenaTransportable)

    jsClass = u'Methanal.Widgets.TabGroup'

    def __init__(self, id, title, tabs):
        self.id = id
        self.title = title
        self.tabs = []
        for tab in tabs:
            self._manageTab(tab)


    def __repr__(self):
        return '<%s id=%r title=%r tabs=%r>' % (
            type(self).__name__,
            self.id,
            self.title,
            self.tabs)


    def _manageTab(self, tab):
        """
        Manage a L{methanal.widgets.Tab} widget.
        """
        if tab not in self.tabs:
            self.tabs.append(tab)
            tab.group = self.id


    def _releaseTab(self, tab):
        """
        Stop managing a L{methanal.widgets.Tab} widget.
        """
        if tab in self.tabs:
            self.tabs.remove(tab)
            tab.group = None


    def getTabIDs(self):
        """
        Get a C{list} of all the tab IDs in the group.
        """
        return [tab.id for tab in self.tabs]


    @classmethod
    def mergeGroups(cls, old, new):
        """
        Merge two L{methanal.widgets.TabGroup}s together.
        """
        return cls(new.id, new.title, old.tabs + new.tabs)


    # IAthenaTransportable

    def getInitialArguments(self):
        return [self.id, self.title, self.getTabIDs()]



class Tab(ThemedElement):
    """
    A content container, intended to be passed to L{TabView}.

    @type id: C{unicode}
    @ivar id: Unique identifier for this container.

    @type title: C{unicode}
    @ivar title: Title of the container, used by L{TabView} when constructing
        the tab list.

    @ivar contentFactory: C{callable} taking no arguments that returns a widget
        to use for the tab content

    @type selected: C{bool}
    @ivar selected: Is this container to be selected initially? Defaults to
        C{False}.

    @type group: C{unicode}
    @ivar group: Identifier of the group this tab belongs to, or C{None} for no
        grouping. Defaults to C{None}.
    """
    fragmentName = 'methanal-tab'

    def __init__(self, id, title, contentFactory, selected=False, group=None,
                 **kw):
        super(Tab, self).__init__(**kw)

        self.id = id
        self.title = title
        self.contentFactory = contentFactory
        self.selected = selected
        self.group = group


    def __repr__(self):
        return '<%s id=%r title=%r selected=%r group=%r>' % (
            type(self).__name__,
            self.id,
            self.title,
            self.selected,
            self.group)


    def getInitialArguments(self):
        return [getArgsDict(self)]


    def getArgs(self):
        return {u'id': self.id,
                u'title': self.title,
                u'selected': self.selected,
                u'group': self.group}


    @expose
    def getContent(self):
        content = self.contentFactory()
        content.setFragmentParent(self)
        return content


    @renderer
    def tabContent(self, req, tag):
        return tag



class StaticTab(Tab):
    """
    Static content tab container.

    Content is inserted at render time and doesn't change or reload.
    """
    jsClass = u'Methanal.Widgets.StaticTab'

    def __init__(self, content=None, **kw):
        """
        @type  content: C{nevow.athena.LiveElement}
        @param content: Optional static content to use. Either C{content} or
            L{contentFactory} must be specified.
        """
        if content is not None:
            kw['contentFactory'] = lambda: content
        super(StaticTab, self).__init__(**kw)


    @renderer
    def tabContent(self, req, tag):
        return tag[self.getContent()]


    def updateRemoteContent(self):
        pass



class DynamicTab(Tab):
    """
    Dynamic content tab container.

    Content is only requested, from the server, and inserted once the tab
    widget has been inserted into the document on the client side.
    """
    jsClass = u'Methanal.Widgets.DynamicTab'



class DemandTab(Tab):
    """
    On-demand content tab container.

    Content is only requested, from the server, and inserted when the tab is
    selected. Selecting the tab always retrieves new content; selecting the tab
    before a previous fetch attempt has completed will result in that data
    being discarded and a new fetch occurring.
    """
    jsClass = u'Methanal.Widgets.DemandTab'

    def updateRemoteContent(self):
        """
        Force the remote content to be updated.
        """
        return self.callRemote('_setContentFromWidgetInfo', self.getContent())
