# import of Kivy lib
from kivy.config import Config

# Kivy config settings
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('graphics', 'width', '1440')
Config.set('graphics', 'height', '1200')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.base import ExceptionManager, ExceptionHandler
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior

# import of other ext lib


# import of python lib
import datetime
import os


# Import of other python codes
from python_script import util_func
# noinspection PyUnresolvedReferences
from python_script import home_screen, import_screen, search_screen, view_screen, settings
# noinspection PyUnresolvedReferences
from python_script import tag_screen, album_screen, person_screen, management_screen, filter_screen
from python_script import face_recognition
from db_model import model



# ---declaration of global variables---


# ---declaration of classes---
class HomeLabel(ButtonBehavior, util_func.HoverBehavior, Label):
    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'home_screen'

    def on_enter(self):
        self.color = (0.92, 0.96, 1, 1)

    def on_leave(self):
        self.color = (1, 1, 1, 1)


class MenuButton(util_func.HoverBehavior, Button):
    # Class for the main menu buttons
    def on_release(self):
        # defined in gallery.kv file
        pass

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class ScreenManager(ScreenManager):
    # Class for the screen manager
    pass


class GalleryLayout(BoxLayout):
    # Class for the gallery layout
    pass


class GalleryApp(App):
    # Class for the gallery App

    def build(self):
        # return the gallery layout and also load all of the necessary kv files
        Builder.load_file('./kivy_file/home.kv')
        Builder.load_file('./kivy_file/import.kv')
        Builder.load_file('./kivy_file/search.kv')
        Builder.load_file('./kivy_file/view.kv')
        Builder.load_file('./kivy_file/tag_screen.kv')
        Builder.load_file('./kivy_file/album_screen.kv')
        Builder.load_file('./kivy_file/person_screen.kv')
        Builder.load_file('./kivy_file/management.kv')
        Builder.load_file('./kivy_file/filter_screen.kv')
        return GalleryLayout()


class ErrorHandler(ExceptionHandler):
    # Error handler
    
    def handle_exception(self, inst):
        # logs the time and error to the console
        print(datetime.datetime.now(), 'Caught Exception:', inst)
        return ExceptionManager.PASS


def init_app():
    if not os.path.exists(settings.Gallery_new_photo_dir):
        os.makedirs(settings.Gallery_new_photo_dir)


if __name__ == '__main__':

    init_app()
    model.init_db()
    face_recognition.init_face_recognition()
    #ExceptionManager.add_handler(ErrorHandler())
    gallery = GalleryApp()
    gallery.run()

