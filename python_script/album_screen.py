from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView

from python_script import util_func
from db_model import model


class CreateAlbumView(ModalView):
    def close_view(self):
        self.dismiss()

    def cancel_b(self):
        self.close_view()

    def confirm_b(self):
        if self.new_album_name.text == '':
            self.warn_label.text = 'Error! Album name cannot be empty'
            return
        self.close_view()
        model.Albums.create_album(album_name=self.new_album_name.text,
                                  album_description=self.new_album_description.text)
        app = App.get_running_app()
        app.root.content_screen.ids.album_screen.search_album()
        return


class ModifyAlbumView(ModalView):
    album_id = -1

    def on_open(self):
        album = model.Albums.get_by_id(self.album_id)
        self.new_album_name.text = album.name
        self.new_album_description.text = album.description

    def close_view(self):
        self.dismiss()

    def cancel_b(self):
        self.close_view()

    def confirm_b(self):
        if self.new_album_name.text == '':
            self.warn_label.text = 'Error! Album name cannot be empty'
            return

        album = model.Albums.get_by_id(self.album_id)
        album.modify_album(album_name=self.new_album_name.text,
                           album_description=self.new_album_description.text)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.album_view_screen.reload_info()


class AlbumScreenButton(util_func.HoverBehavior, Button):
    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def search_album_b(self):
        app = App.get_running_app()
        app.root.content_screen.ids.album_screen.search_album()

    def create_album_b(self):
        app = App.get_running_app()
        app.root.content_screen.ids.album_screen.create_album()


class AlbumButton(util_func.HoverBehavior, BoxLayout, Button):
    album_id = -1

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'album_view_screen'
        app.root.content_screen.ids.album_view_screen.album_id = self.album_id


class AlbumGridImage(ButtonBehavior, util_func.HoverBehavior, Image):
    photo_id = -1

    def load_img(self, photo_id):
        self.photo_id = photo_id
        photo = model.Photos.get_by_id(photo_id)
        self.source = photo.file_path

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.view_screen.photo_id = self.photo_id
        app.root.content_screen.current = 'view_screen'


class AlbumScreen(Screen):
    search_content = ObjectProperty()
    order_by = 1

    def on_enter(self):
        self.clear_screen()
        self.load_screen()

    def load_screen(self):
        album_result = model.get_albums(self.search_content.text, self.order_by)
        for album in album_result:
            album_button = AlbumButton()
            album_button.album_id = album.album_id
            album_button.album_b_name.text = album.name
            album_button.album_b_count.text = str(album.photo_count)
            album_button.album_b_description.text = 'Description: ' + album.description
            self.album_button_grid.add_widget(album_button)

    def clear_screen(self):
        self.album_button_grid.clear_widgets()

    def search_album(self):
        self.clear_screen()
        self.load_screen()

    def create_album(self):
        view = CreateAlbumView()
        view.open()


class AlbumViewScreen(Screen):
    album_id = 1
    order_by = 1

    def on_enter(self):
        self.clear_grid()
        self.load_screen()

    def load_screen(self):
        album = model.Albums.get_by_id(self.album_id)
        self.album_name_info.text = '[b]' + album.name + '[/b]'
        self.album_description_label.text = '[b]Description:[/b] \n' + album.description
        photo_count = album.photo_count
        if photo_count > 0:
            self.album_result_label.text = 'This album contains ' + str(photo_count) + ' photos.'
        else:
            self.album_result_label.text = 'This album is currently empty!'

        photo_result = model.get_album_photos(self.album_id, self.order_by)
        for photo in photo_result:
            img = AlbumGridImage()
            img.load_img(photo_id=photo.photo_id)
            self.album_photo_grid.add_widget(img)

    def clear_grid(self):
        self.album_photo_grid.clear_widgets()

    def reload_info(self):
        album = model.Albums.get_by_id(self.album_id)
        self.album_name_info.text = '[b]' + album.name + '[/b]'
        self.album_description_label.text = '[b]Description:[/b] \n' + album.description

    def modify_album_b(self):
        view = ModifyAlbumView()
        view.album_id = self.album_id
        view.open()



