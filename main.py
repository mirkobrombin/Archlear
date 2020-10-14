#!/usr/bin/env python3
import gi
from os import path, walk, statvfs
from pathlib import Path
import shutil

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

class ArchlearUtils:
    user_dir = str(Path.home())
    stvfs = statvfs('/').f_frsize * statvfs('/').f_blocks

    def pacman_is_locked(self):
        return path.exists("/var/lib/pacman/db.lck")
    
    def yay_exists(self):
        return path.exists("/usr/bin/yay")

    def get_readable_size(self, num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
            
        return "%.1f%s%s" % (num, 'Yi', suffix)
        
    def get_size(self, from_path):
        total_size = 0
        for dirpath, dirnames, filenames in walk(from_path):
            for f in filenames:
                fp = path.join(dirpath, f)
                if not path.islink(fp):
                    total_size += path.getsize(fp)
        
        percentage = (total_size / self.stvfs)

        return [
            self.get_readable_size(total_size),
            percentage
        ]

    def get_pacman_size(self):
        return self.get_size("/var/cache/pacman/pkg")

    def get_yay_size(self):
        return self.get_size("%s/.cache/yay" % self.user_dir)
    
    def clear_pacman_cache(self, w):
        if self.pacman_is_locked:
            dialog = Gtk.MessageDialog(transient_for=w, modal=True, buttons=Gtk.ButtonsType.OK)
            dialog.props.text = "Pacman is currently in use. It is not safe to delete the cache right now, wait for it to finish."
            dialog.run()
            dialog.destroy()
            return False
        
        # paccache -rk 2 [or] pacman -Sc

    def clear_yay_cache(self, w):
        shutil.rmtree("%s/.cache/yay" % self.user_dir)
        return False


class Archlear(Gtk.Window):
    def __init__(self):
        self.title = "Archlear"
        Gtk.Window.__init__(self, title=self.title)
        self.set_position(Gtk.WindowPosition.CENTER)

        # CSS
        css = b"""
                progressbar {
                    margin: 5px 0 0 0;
                }
                progressbar > trough > progress {
                    background-image: none;
                    background-color: red;
                    border-color: red;
                }
                .margin-top {
                    margin: 20px 0 0 0;
                }
            """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        self.context = Gtk.StyleContext()
        screen = Gdk.Screen.get_default()
        self.context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.utils = ArchlearUtils()

        self.set_dark_mode()
        self.header_bar()

        # vbox is the main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.set_border_width(20)
        self.add(main_box)

        # Pacman cache
        self.pacman_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.pacman_cache()
        main_box.add(self.pacman_box)

        # Yay cache
        if self.utils.yay_exists():
            self.yay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.yay_cache()
            main_box.add(self.yay_box)

        # Add vbox to window
        self.add(main_box)

    def set_dark_mode(self):
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

    def header_bar(self):
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = self.title
        self.set_titlebar(header_bar)

        # Clear all button
        all_clr_btn = Gtk.Button("Clear all")
        header_bar.pack_start(all_clr_btn)

    def pacman_cache(self):
        size = self.utils.get_pacman_size()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label()
        title.set_markup("<b>Pacman</b>")
        vbox.add(title)

        progressbar = Gtk.ProgressBar()
        progressbar.set_fraction(size[1])
        vbox.add(progressbar)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, homogeneous=True)
        clr_btn = Gtk.Button("Clear pacman cache")
        clr_btn.connect("clicked", self.on_pacman_clr_clicked)
        hbox.add(Gtk.Label("/var/cache/pacman/pkg"))
        hbox.add(Gtk.Label("Used: %s" % size[0]))
        hbox.add(clr_btn)
        vbox.add(hbox)

        self.pacman_box.add(vbox)

    def on_pacman_clr_clicked(self, input):
        self.utils.clear_pacman_cache(self)

    def yay_cache(self):
        size = self.utils.get_yay_size()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label()
        title.set_markup("<b>Yay Cache (AUR)</b>")
        title.get_style_context().add_class("margin-top")
        vbox.add(title)

        progressbar = Gtk.ProgressBar()
        progressbar.set_fraction(size[1])
        vbox.add(progressbar)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, homogeneous=True)
        clr_btn = Gtk.Button("Clear yay cache")
        clr_btn.connect("clicked", self.on_yay_clr_clicked)
        hbox.add(Gtk.Label("~/.cache/yay"))
        hbox.add(Gtk.Label("Used: %s" % size[0]))
        hbox.add(clr_btn)
        vbox.add(hbox)
        self.yay_box.add(vbox)
        print("aaaa")

    def on_yay_clr_clicked(self, input):
        #self.utils.clear_yay_cache(self)
        for widget in self.yay_box:
            self.yay_box.remove(widget)
        self.yay_cache()


win = Archlear()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
