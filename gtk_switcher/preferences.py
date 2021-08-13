import gi

from pyatem.command import MultiviewInputCommand
from pyatem.field import InputPropertiesField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class PreferencesWindow:
    def __init__(self, parent, application, connection):
        self.application = application
        self.connection = connection
        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.model_changing = False

        builder = Gtk.Builder()
        builder.add_from_resource('/nl/brixit/switcher/ui/preferences.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("window")
        self.window.set_application(self.application)

        self.multiview_window = []

        self.model_me1 = builder.get_object("model_me1")
        self.model_aux = builder.get_object("model_aux")

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.settingsstack = builder.get_object("settingsstack")
        self.multiview_layout = builder.get_object("multiview_layout")
        self.multiview_tl = builder.get_object("multiview_tl")
        self.multiview_tr = builder.get_object("multiview_tr")
        self.multiview_bl = builder.get_object("multiview_bl")
        self.multiview_br = builder.get_object("multiview_br")
        self.multiview_swap = builder.get_object("multiview_swap")
        self.multiview_layout = builder.get_object("multiview_layout")
        self.apply_css(self.window, self.provider)

        self.window.set_transient_for(parent)
        self.window.set_modal(True)
        self.load_models()
        self.load_preferences()
        self.connection.mixer.on('change:multiviewer-properties:*', self.make_multiviewer)
        self.connection.mixer.on('change:multiviewer-input:*', self.update_multiviewer_input)
        self.window.show_all()

    def load_models(self):
        inputs = self.connection.mixer.mixerstate['input-properties']
        self.model_changing = True
        for i in inputs.values():
            if i.available_me1:
                self.model_me1.append([str(i.index), i.name])

            if i.available_aux:
                self.model_aux.append([str(i.index), i.name])
        self.model_changing = False

    def load_preferences(self):
        state = self.connection.mixer.mixerstate

        if 'multiviewer-properties' in state:
            self.make_multiviewer()

    def update_multiviewer_input(self, input):
        pass

    def make_multiviewer(self, *args):
        state = self.connection.mixer.mixerstate
        multiviewer = state['multiviewer-properties'][0]
        self.multiview_window = []
        for widget in self.multiview_layout:
            self.multiview_layout.remove(widget)

        sideways = multiviewer.layout == 5 or multiviewer.layout == 10

        if sideways:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)
        else:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)

        if multiviewer.top_left_small:
            self.make_split_multiview_window(0, 0, False)
        if multiviewer.top_right_small:
            self.make_split_multiview_window(1, 0, False)
        if multiviewer.top_left_small:
            self.make_split_multiview_window(0, 0, True)
        if multiviewer.top_right_small:
            self.make_split_multiview_window(1, 0, True)

        if multiviewer.bottom_left_small:
            self.make_split_multiview_window(0, 1, False)
        if multiviewer.bottom_right_small:
            self.make_split_multiview_window(1, 1, False)
        if multiviewer.bottom_left_small:
            self.make_split_multiview_window(0, 1, True)
        if multiviewer.bottom_right_small:
            self.make_split_multiview_window(1, 1, True)

        for index, window in enumerate(self.multiview_window):
            window.index = index

        self.multiview_tl.set_active(not multiviewer.top_left_small)
        self.multiview_tr.set_active(not multiviewer.top_right_small)
        self.multiview_bl.set_active(not multiviewer.bottom_left_small)
        self.multiview_br.set_active(not multiviewer.bottom_right_small)
        self.multiview_swap.set_active(multiviewer.flip)
        self.multiview_layout.show_all()

    def make_split_multiview_window(self, x, y, second=False):
        x *= 2
        y *= 2
        if not second:
            self.make_multiview_window(x, y, 1, 1)
            self.make_multiview_window(x + 1, y, 1, 1)
        else:
            self.make_multiview_window(x, y + 1, 1, 1)
            self.make_multiview_window(x + 1, y + 1, 1, 1)

    def make_multiview_window(self, x, y, w=2, h=2):
        x *= w
        y *= h
        routable = self.connection.mixer.mixerstate['topology'].multiviewer_routable
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(box)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_left(8)
        box.set_margin_right(8)

        index = len(self.multiview_window)
        if index in self.connection.mixer.mixerstate['multiviewer-input'][0]:
            input = self.connection.mixer.mixerstate['multiviewer-input'][0][index]
            ip = self.connection.mixer.mixerstate['input-properties'][input.source]

            if routable:
                input_select = Gtk.ComboBox.new_with_model(self.model_aux)
                input_select.set_entry_text_column(1)
                input_select.set_id_column(0)
                input_select.window = index
                renderer = Gtk.CellRendererText()
                input_select.pack_start(renderer, True)
                input_select.add_attribute(renderer, "text", 1)
                input_select.set_active_id(str(input.source))
                input_select.set_margin_bottom(16)
                input_select.connect('changed', self.on_multiview_window_changed)
                box.add(input_select)
            else:
                input_label = Gtk.Label(ip.name)
                input_label.set_margin_bottom(16)
                box.add(input_label)

            buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_end(buttonbox, False, False, 0)
            if input.vu:
                vu = self.connection.mixer.mixerstate['multiviewer-vu'][0][index]
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-vu.svg")
                vubutton = Gtk.ToggleButton(image=icon)
                vubutton.set_active(vu.enabled)
                buttonbox.add(vubutton)
            if input.safearea:
                sa = self.connection.mixer.mixerstate['multiviewer-safe-area'][0][index]
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-safearea.svg")
                sabutton = Gtk.ToggleButton(image=icon)
                sabutton.set_active(sa.enabled)
                buttonbox.add(sabutton)

        self.multiview_layout.attach(frame, x, y, w, h)
        self.multiview_window.append(frame)

    def on_multiview_window_changed(self, widget):
        if self.model_changing:
            return
        cmd = MultiviewInputCommand(index=0, window=widget.window, source=int(widget.get_active_id()))
        self.connection.mixer.send_commands([cmd])

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)