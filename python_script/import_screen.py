from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView


import uuid
import cv2
import time
import numpy as np

from python_script import util_func
from python_script import settings
from python_script import face_recognition
from db_model import model
from kivy.uix.modalview import ModalView


class DuplicateView(ModalView):
    photo_ls = []

    def on_open(self):
        self.load_image()

    def close_view(self):
        self.duplicate_grid.clear_widgets()
        self.dismiss()
        app = App.get_running_app()
        app.root.content_screen.import_screen.print_finished()

    def load_image(self):
        for id in self.photo_ls:
            img = DuplicateViewImage()
            img.source = model.Photos.get_by_id(id).file_path
            img.photo_id = id
            self.duplicate_grid.add_widget(img)

        return

    def clear(self):
        self.duplicate_grid.clear_widgets()
        return

    def restore(self):
        self.clear()
        self.load_image()
        return

    def confirm_b(self):
        for widget in self.duplicate_grid.children:
            model.Photos.get_by_id(widget.photo_id).delete_photo()
        self.duplicate_grid.clear_widgets()
        self.close_view()
        return


class DuplicateViewImage(ButtonBehavior, Image):
    photo_id = -1

    def on_release(self):
        self.parent.remove_widget(self)


class ImportPreviewImage(ButtonBehavior, Image):
    hash_val = ''
    p_ls = []

    def on_release(self):
        self.parent.remove_widget(self)
        app = App.get_running_app()
        app.root.content_screen.import_screen.remove_photo(self.p_ls, self.hash_val)
        return


def get_average_hash(path):
    hash = ''

    img = cv2.imread(path, 0)
    img = cv2.resize(img, (8, 8), interpolation=cv2.INTER_AREA).flatten()
    avg = np.average(img)
    for pixel in img:
        if pixel > avg:
            hash += '1'
        else:
            hash += '0'

    return hash


def extract_file_path(file_path):
    # function for extracting the file_name, directory and extension
    f_path = str(file_path)
    name_pos = f_path.rindex('/') + 1
    f_name = f_path[name_pos :-1]
    f_dir = f_path[2: name_pos]
    f_ext = f_name[f_name.rindex('.'):]
    return f_dir, f_name, f_ext


def is_image_file(file_ext):
    # check if the image extension is correct
    image_ext = ['.jpg', '.png', '.jpeg', '.PNG', '.JPG']
    if any (file_ext == ext for ext in image_ext):
        return True
    return False


class ImportScreenButton(util_func.HoverBehavior, Button):
    def on_release(self):
        # defined in gallery.kv file
        pass

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def cancel_b(self):
        # reserve for cancel button
        app = App.get_running_app()
        app.root.content_screen.import_screen.import_preview_grid.cols=3
        return

    def import_photo_b(self):
        # function for the import button
        app = App.get_running_app()
        app.root.content_screen.import_screen.import_photos()
        return

    def clear_data_b(self):
        # function for the clear button
        app = App.get_running_app()
        app.root.content_screen.import_screen.clear_import_photos()
        return

    def add_tag_b(self):
        app = App.get_running_app()
        app.root.content_screen.import_screen.add_tag()
        return


class ImportTagButton(util_func.HoverBehavior, Button):
    tag_name = ''

    def on_enter(self):
        self.background_color = (0.9, 0.65, 0.65, 1)

    def on_leave(self):
        self.background_color = (0.5, 0.5, 0.5, 1)

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.import_screen.remove_tag(self.tag_name)
        app.root.content_screen.import_screen.import_tag_grid.remove_widget(self)
        return


class ImportScreen(Screen):
    # Class for the import screen
    import_album = ObjectProperty()
    import_tag = ObjectProperty()
    file_list = []
    photo_count = 0
    tag_set = set()
    hash_set = set()

    def on_enter(self):
        Window.bind(on_dropfile=self.drop_file_handler)

    def on_pre_leave(self):
        Window.unbind(on_dropfile=self.drop_file_handler)
        self.clear_import_data()

    def drop_file_handler(self, window, file_path):
        # Function for handling the file drop event
        f_dir, f_name, f_ext = extract_file_path(file_path)
        if is_image_file(f_ext):
            self.import_warn_label.text = 'Please make sure you do not upload duplicate image!'
            h_val = get_average_hash(f_dir + f_name)

            if h_val in self.hash_set:
                return

            self.hash_set.add(h_val)
            new_name = uuid.uuid4().hex + f_ext

            self.file_list.append([f_name, new_name, f_dir, h_val])

            img = ImportPreviewImage(source=f_dir + f_name)
            img.p_ls = [f_name, new_name, f_dir, h_val]
            img.hash_val = h_val
            self.import_preview_grid.add_widget(img)
            self.photo_count += 1
            self.import_warn_label.text = ''
            self.import_button.text = '  Import photos (' + str(self.photo_count) + ')  '

        else:
            self.import_warn_label.text = 'Please make sure it is an image file!'
        return

    def clear_import_photos(self):
        # function to clear all photo data in the import screen
        self.import_warn_label.text = ''
        self.import_button.text = '  Import photos  '
        self.file_list = []
        self.photo_count = 0
        self.import_preview_grid.clear_widgets()
        self.hash_set = set()
        return

    def clear_import_data(self):
        # function to clear all photo data and input data in the screen
        self.import_tag_grid.clear_widgets()
        self.clear_import_photos()
        self.import_tag.text = ''
        self.import_album.text = ''
        self.tag_set = set()
        self.hash_set = set()
        return

    def import_photos(self):
        if self.photo_count > 0:
            a_name = self.import_album.text
            # tags = self.import_tags.text
            model.set_old()

            for f_name, new_name, f_dir, h_val in self.file_list:
                new_dir = settings.Gallery_photo_dir

                if a_name == '':
                    new_dir = settings.Gallery_new_photo_dir
                else:
                    new_dir = new_dir + a_name + '/'

                model.Photos.create_photo(file_name=f_name, file_dir=new_dir, new_name=new_name, h_val=h_val,
                                          original_path=f_dir + f_name, album_name=a_name, tag_set=self.tag_set)
            num_photos = str(self.photo_count)
            self.clear_import_data()
            face_recognition.recognize_face()

            model.filter_new_photos()
            self.duplicate_search()

        else:
            self.import_warn_label.text = 'Please upload photos first!'



        return

    def add_tag(self):
        tag_name = self.import_tag.text
        if tag_name != '' and tag_name not in self.tag_set:
            tag_label = ImportTagButton(text = tag_name)
            tag_label.tag_name = tag_name
            self.import_tag_grid.add_widget(tag_label)

            self.tag_set.add(tag_name)
            self.import_tag.text = ''
        else:
            self.import_warn_label.text = 'Please make sure the tag name is not empty or a duplicate'
        return

    def remove_tag(self, tag_name):
        self.tag_set.remove(tag_name)
        return

    def remove_photo(self, p_ls, hash_val):
        self.file_list.remove(p_ls)
        self.hash_set.remove(hash_val)
        self.photo_count -= 1
        self.import_button.text = '  Import photos (' + str(self.photo_count) + ')  '
        return

    def duplicate_search(self):
        d_ls = model.duplicate_photo_search()
        if d_ls:
            view = DuplicateView()
            view.photo_ls = d_ls
            view.open()
        self.print_finished()
        return

    def print_finished(self):
        new_count = model.Photos.select().where(model.Photos.new == True).count()
        self.import_warn_label.text = str(new_count) + ' photo(s) has been successfully imported!'

