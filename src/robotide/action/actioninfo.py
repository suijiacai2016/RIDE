#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import wx
import re

from shortcut import Shortcut


def ActionInfoCollection(data, event_handler, container=None):
    """Parses the ``data`` into a list of `ActionInfo` and `SeparatorInfo` objects.

    The data is parsed based on the simple DSL documented below.

    :Parameters:
      data
        The data to be parsed into `ActionInfo` and `SeparatorInfo` objects.
      event_handler
        The event handler that implements the actions. See `finding handlers`_
        for more information.
      container
        the wxPython element containing the UI components associated with
        the `ActionInfo`.

    DSL syntax
    ----------
    ::

      [menu]
      name | documentation | shortcut | icon

    Fields
    ------

    menu
      The name of the menu under which the entries below it are inserted.
    name
      The name of the menu entry to be added. If name is ``---``, a
      `SeparatorInfo` object is created instead of an `ActionInfo` object.
      If name is post fixed with shortcuts between parenthesis and separated
      with ' or ', these shortcuts are parsed to machine local presentation
      and shown after the name. This can be used instead of shotrcut-element
      if you want to add shortcuts that you want to bind yourself and/or add
      several shortcuts.
    documentation
      Documentation for the action.
    shortcut
      Keyboard shortcut to invoke the action.
    icon
      Icon for the toolbar button.

    See the `ActionInfo` attributes with same/similar names for more
    information about the fields and their possible values. Three
    last fields are optional.

    Finding handlers
    ----------------

    The given ``event_handler`` must have handler methods that map to the
    specified action names. The mapping is done by prefixing the name with
    ``On``, removing spaces, and capitalizing all words. For example ``Save``
    and ``My Action`` must have handler methods ``OnSave`` and ``OnMyAction``,
    respectively. If name has content between parenthesis at the end, this
    content is ignored when creating handler mapping.

    Specifying container
    --------------------

    By default the given ``container`` is passed to the `ActionInfo.__init__`
    method directly. This can be altered by prefixing the ``name`` with an
    exclamation mark (e.g. ``!Save`` or ``!My Action``) to make that action
    global. With these actions the container given to the `ActionInfo.__init__`
    is always ``None``.

    Example
    -------
    ::

        [File]
        !&Open | Open file containing tests | Ctrl-O | ART_FILE_OPEN
        !Open &Resource | Open a resource file | Ctrl-R
        ---
        &Save | Save selected datafile | Ctrl-S | ART_FILE_SAVE

        [Tools]
        !Manage Plugins

        [Content]
        Content Assist (Ctrl-Space or Ctrl-Alt-Space) | Has two shortcuts.
    """

    menu = None
    actions = []
    for row in data.splitlines():
        row = row.strip()
        if not row:
            continue
        elif row.startswith('[') and row.endswith(']'):
            menu = row[1:-1].strip()
        else:
            actions.append(_create_action_info(event_handler, menu, container,
                                               row))
    return actions


def _create_action_info(eventhandler, menu, container, row):
    if row.startswith('---'):
        return SeparatorInfo(menu)
    tokens = [ t.strip() for t in row.split('|') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    eventhandler_name, name = _get_eventhandler_name_and_parsed_name(name)
    action = getattr(eventhandler, eventhandler_name)
    return ActionInfo(menu, name, action, container, shortcut, icon, doc)

def _get_eventhandler_name_and_parsed_name(name):
    eventhandler_name, name = _parse_shortcuts_from_name(name)
    return ('On%s' % eventhandler_name.replace(' ', '').replace('&', '') ,
            name)

def _parse_shortcuts_from_name(name):
    if '(' in name:
        eventhandler_name, shortcuts = name.split('(', 1)
        shortcuts = shortcuts.split(')')[0]
        elements = shortcuts.split(' or ')
        name = '%s (%s)' % (eventhandler_name,
                            ' or '.join(Shortcut(e).printable for e in elements))
        return eventhandler_name, name
    return name, name

class MenuInfo(object):
    """Base class for `ActionInfo` and `SeparatorInfo`."""

    def __init__(self):
        self.insertion_point = _InsertionPoint()

    def is_separator(self):
        return False

    def set_menu_position(self, before=None, after=None):
        """Sets the position of this menu entry.

        :Parameters:
          before
            Place this menu entry before the specified entry.
          after
            Place this menu entry after the specified entry.

        Use either ``before`` or ``after`` and give the name without the
        possible shortcut.
        """
        self.insertion_point = _InsertionPoint(before, after)


class ActionInfo(MenuInfo):
    """Used to create menu entries, keyboard shortcuts and/or toolbar buttons."""

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc=''):
        """Initializes information needed to create actions..

        :Parameters:
          menu_name
            The name of the menu where the new entry will be added. The menu is
            created if it does not exist.
          name
            The name of the new menu entry. The name may contain an accelerator
            key prefixed by an ampersand like ``New &Action``. If an accelerator
            is not specified, or the one requested is already taken, the next
            free key is selectd.
          action
            The callable which will be called when a user does any of the
            associated UI actions.
          container
            The wxPython element containing the UI components associated with
            the ``action``. When any of the registered UI actions is executed,
            the ``action`` is called only if the ``container`` or any of its
            child components has focus. It is possible to make the ``action``
            always active by using ``None`` as the ``container``.
          shortcut
            The keyboard shortcut associated to the ``action``. The ``shortcut``
            must be a string constructed from optional modifiers (``Ctrl, Shift,
            Alt``) and the actual shortcut key separating the parts with a hyphen.
            The shortcut key can be either a single character or any of the
            `wx keycodes`__ without the ``WXK_`` prefix. Examples: ``Ctrl-C``,
            ``Shight-Ctrl-6``, ``Alt-Left``, ``F6``.
          icon
            The icon added to the toolbar as a toolbar button. It can be either
            a 16x16 bitmap or a string presenting one of the icons provided by
            `wxPython's ArtProvider`__ like ``ART_FILE_OPEN``.
          doc
            The documentation shown on the statusbar when selection is on
            the associated menu entry or toolbar button.

        __ http://docs.wxwidgets.org/stable/wx_keycodes.html#keycodes
        __ http://www.wxpython.org/docs/api/wx.ArtProvider-class.html
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name
        self.name = name
        self.action = action
        self.container = container
        self.shortcut = Shortcut(shortcut)
        self.icon = self._get_icon(icon)
        self.doc = doc

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            return wx.ArtProvider.GetBitmap(getattr(wx, icon),
                                            wx.ART_TOOLBAR, (16, 16))
        return icon


class SeparatorInfo(MenuInfo):
    """Used to create separators to menus."""

    def __init__(self, menu_name):
        """Initializes information needed to add separators to menus.

        :Parameters:
          menu_name
            The name of the menu where the separator will be added. If menu does
            not exist, it is created automatically.
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name

    def is_separator(self):
        return True


class _InsertionPoint(object):
    _shortcut_remover = re.compile(' {2,}\([^()]+\)$')

    def __init__(self, before=None, after=None):
        self._item = before or after
        self._insert_before = before is not None

    def get_index(self, menu):
        if not self._item:
            return menu.GetMenuItemCount()
        index = self._find_position_in_menu(menu)
        if not index:
            return menu.GetMenuItemCount()
        if not self._insert_before:
            index += 1
        return index

    def _find_position_in_menu(self, menu):
        for index in range(0, menu.GetMenuItemCount()):
            item = menu.FindItemByPosition(index)
            if self._get_menu_item_name(item).lower() == self._item.lower():
                return index
        return None

    def _get_menu_item_name(self, item):
        return self._shortcut_remover.split(item.GetLabel())[0]
