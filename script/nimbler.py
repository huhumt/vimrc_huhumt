#!/usr/bin/env python3
#! - coding: utf-8 -*-

import re
import os
import time
import string
import signal
import subprocess
import configparser
from xml.sax.saxutils import escape

import gi
gi.require_version('GdkX11', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Keybinder', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Wnck, Keybinder, Gdk, GdkX11, Pango


# Python GObject Introspection API Reference available at
# http://lazka.github.io/pgi-docs/. Because after
# http://python-gtk-3-tutorial.readthedocs.org/en/latest/ it's really not that
# useful to try to guess things based on
# https://developer.gnome.org/gtk3/stable/ as suggested.

# Libwnck reference here: https://developer.gnome.org/libwnck/stable/


class FuzzyMatcher():

    def __init__(self, pattern):
        self.pattern = self.setPattern(pattern)

    @classmethod
    def setPattern(cls, pattern):
        return re.compile('.*?'.join(map(re.escape, list(pattern))))

    def score(self, string):
        match = self.pattern.search(string)
        if match is None:
            return 0
        else:
            return (
                100.0 / (1 + match.start())
                + 120.0 / (match.end() - match.start() + 1)
            )


class KeyBindings():

    def __init__(self):
        # That's 93 distinct characters on my system
        # Can't use string.printable because that includes string.whitespace
        self.numbering = list(
            string.digits + string.ascii_letters +
            string.punctuation.replace(':', '')  # filter colon
        )
        self.function_keys = [
            'F1', 'F2', 'F3', 'F4', 'F5',
            'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'
        ]

    def get_keyvals_from_unicode(self):
        return [Gdk.unicode_to_keyval(ord(n)) for n in self.numbering]

    def get_keyvals_from_name(self):
        self.keyvals_from_name = []

        for function_key in self.function_keys:
            keyval = Gdk.keyval_from_name(function_key)
            self.keyvals_from_name.append(keyval)

        return self.keyvals_from_name


class DPIScaling():

    def __init__(self):
        # Get the screen dpi
        self.dpi = Gdk.Screen.get_resolution(Gdk.Screen.get_default())
        # This is a scale factor between points specified in a
        # Pango.FontDescription and cairo units. The default value is 96,
        # meaning that a 10 point font will be 13 units high.
        # (10 * 96. / 72. = 13.3).
        # See http://lazka.github.io/pgi-docs/#Gdk-3.0/classes/Screen.html#Gdk.Screen.set_resolution
        self.scaling_factor = self.dpi / 96


class WindowList():

    def __init__(self, ignored_windows, always_show_windows,
                 ignored_window_types, icon_size, win_size):
        self.ignored_windows = ignored_windows
        self.always_show_windows = always_show_windows
        self.ignored_window_types = ignored_window_types
        self.icon_size = icon_size
        self.win_size = win_size

    def refresh(self):
        # Get the screen and force update
        screen = Wnck.Screen.get_default()
        screen.force_update()

        self.workspaces = screen.get_workspaces()
        active_workspace_id = self.workspaces.index(screen.get_active_workspace())

        # Clear existing
        app_dict = {"Xfce4-terminal": 0, "Firefox-esr": 1, "Firefox": 2}
        windows = {i: [{}] * len(app_dict) for i in range(len(self.workspaces))}

        # Get a list of windows
        for i in screen.get_windows():
            name = i.get_name()
            workspace = i.get_workspace()
            class_group = str(i.get_class_group_name()).capitalize()

            # Filter out extraneous windows
            if not self.isWindowAlwaysShown(name):
                if i.get_window_type() in self.ignored_window_types:
                    continue
                if self.isWindowIgnored(name):
                    continue

            id = (self.workspaces.index(workspace)
                     if workspace else active_workspace_id)
            cur_window_dict = {
                'name': name,
                'class_group': class_group,
                'window_xid': i.get_xid(),
                'rank': 0
            }

            if (class_group in app_dict
                    and not windows[id][app_dict[class_group]]):
                windows[id][app_dict[class_group]] = cur_window_dict
            else:
                windows[id].append(cur_window_dict)

        self.windows = {}
        for k, v in windows.items():
            valid_win = list(filter(None, v))
            if valid_win:
                self.windows[k] = valid_win
        if active_workspace_id not in self.windows:
            self.windows[active_workspace_id] = []
        self.max_windows = len(max(self.windows.values(), key=len))
        # Merged correctly ordered list for switching purposes
        # Via http://stackoverflow.com/a/952952
        self.window_list_merged = [
            item for sublist in self.windows.values() for item in sublist
        ]

    @staticmethod
    def get_window_by_xid(window_xid):
        return Wnck.Window.get(window_xid)

    def get_icon(self, window_xid):
        if self.icon_size == 'default' or type(self.icon_size) is int:
            return self.get_window_by_xid(window_xid).get_icon()
        elif self.icon_size == 'mini':
            return self.get_window_by_xid(window_xid).get_mini_icon()

    def getHighestRanked(self):
        return (self.window_list_merged[0]
                if len(self.window_list_merged)
                else {})

    def rank(self, text):
        fuzzyMatcher = FuzzyMatcher(text.lower())
        for i in self.window_list_merged:
            score = fuzzyMatcher.score(i['name'].lower())
            if i['class_group']:
                score += fuzzyMatcher.score(i['class_group'].lower())
            i['rank'] = score

        self.window_list_merged.sort(key=lambda x: x['rank'], reverse=True)

    def isWindowIgnored(self, window_title):
        for pattern in self.ignored_windows:
            if pattern.search(window_title) is not None:
                return True

        return False

    def isWindowAlwaysShown(self, window_title):
        for pattern in self.always_show_windows:
            if pattern.search(window_title) is not None:
                return True

        return False


class NimblerWindow(Gtk.Window):

    def __init__(self, config):
        Gtk.Window.__init__(self, title='Nimbler')

        # Window is initially hidden
        self.hidden = True
        self.set_default_size(config.win_size[0], config.win_size[1])
        self.set_resizable(True)

        # Set up keybindings
        self.keybindings = KeyBindings()
        self.numbering = self.keybindings.numbering
        self.numbering_keyvals = self.keybindings.get_keyvals_from_unicode()
        self.function_keys_keyvals = self.keybindings.get_keyvals_from_name()
        # Set up keypad numbers dictionary
        self.keypad_numbers = {
            Gdk.KEY_KP_0: Gdk.KEY_0,
            Gdk.KEY_KP_1: Gdk.KEY_1,
            Gdk.KEY_KP_2: Gdk.KEY_2,
            Gdk.KEY_KP_3: Gdk.KEY_3,
            Gdk.KEY_KP_4: Gdk.KEY_4,
            Gdk.KEY_KP_5: Gdk.KEY_5,
            Gdk.KEY_KP_6: Gdk.KEY_6,
            Gdk.KEY_KP_7: Gdk.KEY_7,
            Gdk.KEY_KP_8: Gdk.KEY_8,
            Gdk.KEY_KP_9: Gdk.KEY_9,
        }

        # Set up the frame
        self.frame = Gtk.Frame()
        self.frame.set_shadow_type(1)
        self.add(self.frame)

        # Initialize window list
        self.windowList = WindowList(
            config.ignored_windows,
            config.always_show_windows,
            config.ignored_window_types,
            config.icon_size,
            config.win_size
        )
        # self.windowList.refresh()

        # Register events
        self.connect("key-press-event", self.keypress)

    def populate(self):
        self.window_counter = 0
        self.num_workspaces = len(self.windowList.windows)

        dpi_scaling_factor = DPIScaling().scaling_factor
        i_label_width = dpi_scaling_factor
        i_column_width = int(dpi_scaling_factor * (
            self.windowList.win_size[0]/self.num_workspaces - i_label_width))
        j_row_height = min(int(dpi_scaling_factor * (
            self.windowList.win_size[1]/(self.windowList.max_windows+1))), 25)

        for i, (k, v) in enumerate(self.windowList.windows.items()):
            i_workspace_name = k
            workspace_button = Gtk.Button(
                label=f'Workspace {i_workspace_name}')
            workspace_button.set_size_request(i_column_width, j_row_height)
            # Name is F1 and up to tie into keyboard event handling
            workspace_button.set_name('F' + str(i_workspace_name))
            # The event handler likes a string
            workspace_button.connect(
                'clicked', self.activate_workspace_via_button)

            i_column_left = i * (i_column_width + 1)
            self.grid.attach(workspace_button, i_column_left+i_label_width, 0,
                             i_column_width, j_row_height)

            for j, win in enumerate(v):
                j4grid_top = (j + 1) * j_row_height
                name = win['name']
                icon = self.windowList.get_icon(win['window_xid'])
                binding = self.numbering[self.window_counter]

                # Shows what key to press
                binding_label = Gtk.Label()
                binding_label.set_xalign(0)
                binding_label.set_yalign(0.5)
                if self.window_counter < len(self.numbering):
                    binding_label.set_markup('<b>' + escape(binding) + '</b>')
                self.grid.attach(binding_label, i_column_left, j4grid_top,
                                 i_label_width, j_row_height)

                image = Gtk.Image.new_from_pixbuf(icon)
                button_label = Gtk.Label()
                # icon should be square, size in j_row_height * j_row_height
                name_width = (i_column_width-j_row_height) >> 3
                button_label.set_text(name[:name_width])
                # first attribute is horizontal, second is vertical
                button_label.set_xalign(0)
                button_label.set_yalign(0.5)
                # button_label.set_max_width_chars(256) # not working, why?
                # TODO Make configurable?
                button_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

                # Apparently buttons can only have one child, so we need a box
                # Useful info to be found at:
                #    http://pygtk.org/pygtk2tutorial/ch-ButtonWidget.html
                # but keep in mind it's about Gtk+ 2 and also uses differently
                # named Python objects Pack 'em in
                button_box = Gtk.Box()
                button_box.set_orientation(Gtk.Orientation.HORIZONTAL)
                button_box.set_spacing(5)
                button_box.pack_start(image, False, False, 3)
                button_box.pack_start(button_label, False, False, 3)

                # The all important window button
                button = Gtk.Button()
                button.set_relief(Gtk.ReliefStyle.NONE)
                button.set_size_request(i_column_width, j_row_height)
                button.set_name(binding)
                # button.set_sensitive(False) needs to be trigged when searching
                button.connect('clicked', self.present_window_via_button)
                button.connect('focus', self.highlightButton)
                button.connect('focus-out-event', self.clearButton)

                # Add the content to the button
                button.add(button_box)
                self.grid.attach(button, i_column_left+i_label_width, j4grid_top,
                                 i_column_width, j_row_height)

                # Up the overall counter
                self.window_counter += 1

    def activate_workspace(self, label):
        # Ignore everything in the supplied string but the numbers
        workspace = re.sub('[^0-9]', '', label)
        workspace = int(workspace) - 1

        self.toggle()
        self.windowList.workspaces[workspace].activate(self.getXTime())

    def activate_workspace_via_button(self, button):
        name = button.get_name()
        self.activate_workspace(name)

    def enteredNameChanged(self, entry):
        text = entry.get_text()

        if text:
            self.windowList.rank(text)
            self.populate()

    def highlightButton(self, button, event):
        rgba = Gdk.RGBA(0.5, 0.5, 0.2, 1)
        button.override_background_color(0, rgba)

    def clearButton(self, button, event):
        rgba = Gdk.RGBA(0, 0, 0, 0)
        button.override_background_color(0, rgba)

    def close_window(self, window_xid):
        WindowList.get_window_by_xid(window_xid).close(self.getXTime())

    def close_window_via_number(self, window_number):
        self.toggle()
        self.close_window(
            self.windowList.window_list_merged[window_number]['window_xid']
        )

    def presentWindow(self, window_xid):
        window = WindowList.get_window_by_xid(window_xid)
        workspace = window.get_workspace()
        if workspace is not None:
            workspace.activate(self.getXTime())

        window.activate(self.getXTime())

    def present_window_via_button(self, button):
        name = button.get_name()
        window_number = self.numbering.index(name)
        self.present_window_via_number(window_number)

    def present_window_via_number(self, window_number):
        self.toggle()
        self.presentWindow(
            self.windowList.window_list_merged[window_number]['window_xid']
        )

    def presentByShortcut(self, event, keyval):
        time.sleep(0.1)  # workaround to avoid switch window failure
        self.getXTime()
        # Workspace shortcuts
        if keyval in self.function_keys_keyvals:
            index = self.keybindings.get_keyvals_from_name().index(keyval)
            if index < self.num_workspaces:
                self.activate_workspace(self.keybindings.function_keys[index])
                return True
        # Window shortcuts
        elif keyval in self.numbering_keyvals:
            index = self.numbering_keyvals.index(keyval)
            if index < self.window_counter:
                if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
                    self.close_window_via_number(index)
                else:
                    self.present_window_via_number(index)
                return True
        return False

    def presentHighestRanked(self):
        highestRanked = self.windowList.getHighestRanked()
        if highestRanked:
            self.presentWindow(highestRanked.get('window_xid'))

    def presentManual(self, view, path, column):
        indices = path.get_indices()
        if len(indices) < 1:
            return

        index = indices[0]
        windows = self.windowList.window_list_merged
        if index < len(windows):
            self.toggle()
            self.presentWindow(windows[index]['window_xid'])

    def keypress(self, widget, event):
        # Support pressing numbers on keypad
        # If event.keyval is found in the dictionary of keypad numbers
        # it'll change it into a regular number;
        # otherwise it simply returns event.keyval
        # Thanks to http://stackoverflow.com/a/103081
        event.keyval = self.keypad_numbers.get(event.keyval, event.keyval)
        # selected = self.appListView.get_selection().get_selected()

        if event.keyval == Gdk.KEY_Escape:
            self.toggle()
            return True

        if self.enteredName.has_focus():
            if event.keyval == Gdk.KEY_Return:
                # TODO do something!
                text = self.enteredName.get_text()

                # You might decide just to enter the character after all
                # Needs to be converted to keyval though
                if len(text) == 1:
                    number = ord(text)
                    keyval = Gdk.unicode_to_keyval(number)
                    self.presentByShortcut(event, keyval)
                elif len(text) > 3:
                    if self.windowList.max_windows > 0:
                        if self.windowList.window_list_merged[0]['rank'] > 0:
                            self.present_window_via_number(0)
                            return True
                    self.toggle()
                    subprocess.Popen(["xfce4-appfinder"], start_new_session=True)
                return True
        else:
            # selected = self.appListView.get_selection().get_selected()
            if event.keyval in (Gdk.KEY_colon, Gdk.KEY_slash, Gdk.KEY_question):
                # Show input, thanks to http://stackoverflow.com/a/4956770
                self.enteredName.show()
                self.enteredName.grab_focus()
                # Return True so the colon doesn't end up in the Entry box
                return True
            else:
                return self.presentByShortcut(event, event.keyval)

    def toggle(self):
        if self.hidden:
            self.windowList.refresh()
            self.grid = Gtk.Grid()
            self.grid.set_column_homogeneous(False)
            self.grid.set_row_homogeneous(False)
            # self.grid.set_column_spacing(5)
            # self.grid.set_row_spacing(20)
            self.frame.add(self.grid)

            # Set up the box to enter an app name
            self.enteredName = Gtk.Entry()
            # Set up event
            self.enteredName.connect("changed", self.enteredNameChanged)
            self.grid.attach(self.enteredName, 1, 0,
                             self.windowList.win_size[0], 1)
            self.enteredName.set_no_show_all(True)

            # Register enteredName event
            self.enteredName.connect('changed', self.enteredNameChanged)

            self.resize(self.windowList.win_size[0],
                        self.windowList.win_size[1])
            # Populate windows
            self.populate()

            # Set state
            self.hidden = False
            self.show_all()

            # Clear out the text field
            # self.enteredName.set_text('')
            # self.enteredName.grab_focus()

            # Show our window with focus
            self.stick()
            time = self.getXTime()
            self.get_window().focus(time)
        else:
            self.hidden = True
            self.grid.destroy()
            self.hide()
            self.resize(1, 1)

    def hotkey(self, key, data):
        self.toggle()

    def getXTime(self):
        try:
            time = GdkX11.x11_get_server_time(self.get_window())
        except:
            time = 0

        return time


class Config:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read([
            os.path.expanduser('~/.config/nimbler/nimbler.conf'),
            os.path.expanduser('~/.nimbler.conf')
        ])

        self.loadOptions()

    def loadOptions(self):
        self.hotkey = self.getOption('hotkey', 'F10')
        self.ignored_windows = self.prepareIgnoredWindows(
            self.getOption('ignored_windows', [])
        )
        self.always_show_windows = self.prepareAlwaysShowWindows(
            self.getOption('always_show_windows', [])
        )
        self.ignored_window_types = self.getIgnoredWindowTypes()
        self.icon_size = self.get_icon_size(
            self.getOption('icon_size', 'default'))
        self.win_size = list(
            map(int, self.getOption('win_size', '800x400').lower().split('x')))

    def getOption(self, option_name, default_value):
        if self.config.has_option('DEFAULT', option_name):
            return self.config.get('DEFAULT', option_name)
        else:
            return default_value

    def prepareIgnoredWindows(self, ignored_windows):
        return self.splitAndCompileWindowRegexes(ignored_windows)

    def prepareAlwaysShowWindows(self, always_show_windows):
        return self.splitAndCompileWindowRegexes(always_show_windows)

    def splitAndCompileWindowRegexes(self, windows):
        # Turn window str into a list
        if type(windows) is str:
            windows = list(filter(None, windows.split("\n")))

        windows_re_list = []
        # Now, turn each of the window names into a regex pattern
        for w in windows:
            windows_re_list.append(re.compile(w))
        return windows_re_list

    def getIgnoredWindowTypes(self):
        window_types = {
            'normal': {
                'window_type': Wnck.WindowType.NORMAL, 'default': True
            },
            'desktop': {
                'window_type': Wnck.WindowType.DESKTOP, 'default': False
            },
            'dock': {
                'window_type': Wnck.WindowType.DOCK, 'default': False
            },
            'dialog': {
                'window_type': Wnck.WindowType.DIALOG, 'default': False
            },
            'toolbar': {
                'window_type': Wnck.WindowType.TOOLBAR, 'default': False
            },
            'menu': {
                'window_type': Wnck.WindowType.MENU, 'default': False
            },
            'utility': {
                'window_type': Wnck.WindowType.UTILITY, 'default': False
            },
            'splashscreen': {
                'window_type': Wnck.WindowType.SPLASHSCREEN, 'default': False
            },
        }

        ignored_window_types = []

        for window_type in window_types:
            should_show = bool(int(
                self.getOption(
                    'show_windows_' + window_type,
                    window_types[window_type]['default']
                )
            ))
            if not should_show:
                ignored_window_types.append(
                    window_types[window_type]['window_type'])

        return ignored_window_types

    def get_icon_size(self, icon_size):
        if icon_size == 'default' or icon_size == 'mini':
            return icon_size
        elif icon_size.isdigit():
            icon_size = int(icon_size)
            Wnck.set_default_icon_size(icon_size)
            return icon_size


def nimbler():
    # Catch SIGINT signal
    # signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Load the configuration with defaults
    config = Config()

    # Create the window and set attributes
    win = NimblerWindow(config)
    win.connect("delete-event", Gtk.main_quit)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_keep_above(True)
    win.set_skip_taskbar_hint(True)
    win.set_decorated(False)

    # Set the hotkey
    Keybinder.init()
    if not Keybinder.bind(config.hotkey, win.hotkey, None):
        print("Could not bind the hotkey:", config.hotkey)
    else:
        # The main loop
        Gtk.main()


def main():
    pidfile = "/tmp/nimbler.pid"

    if os.path.isfile(pidfile):
        pid = open(pidfile, 'r').read()
        if os.path.exists(f"/proc/{pid}"):
            raise SystemExit(f"{os.path.basename(__file__)} already in running")

    try:
        open(pidfile, 'w').write(str(os.getpid()))
        nimbler()
    except Exception as e:
        print(e)
    finally:
        os.unlink(pidfile)


if __name__ == "__main__":
    main()
