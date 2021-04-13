from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.app import App
from kivy.uix.modalview import ModalView

from python_script import util_func
from db_model import model


class ModifyTagView(ModalView):
    # Modal view for changing tag name
    tag_id=-1

    def close_view(self):
        self.dismiss()

    def confirm_b(self):
        if self.input_text.text == '':
            self.warn_label.text = 'Error! Tag name cannot be empty!'
            return
        model.Tags.get_by_id(self.tag_id).modify_name(tag_name=self.input_text.text)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.tag_view_screen.reload_name()

    def cancel_b(self):
        self.close_view()


class TagButton(util_func.HoverBehavior, BoxLayout, Button):
    tag_id = -1

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'tag_view_screen'
        app.root.content_screen.ids.tag_view_screen.tag_id = self.tag_id

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class TagGridImage(ButtonBehavior, util_func.HoverBehavior, Image):
    photo_id = -1

    def load_img(self, photo_id):
        self.photo_id = photo_id
        photo = model.Photos.get_by_id(photo_id)
        self.source = photo.file_path

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.view_screen.photo_id = self.photo_id
        app.root.content_screen.current = 'view_screen'


class TagScreen(Screen):
    search_content = ObjectProperty()
    # current_tag = -1
    order_by = 1

    def on_enter(self):
        self.clear_tags()
        self.load_tags()

    def load_tags(self):
        tag_result = model.get_tags(self.search_content.text, self.order_by)
        for tag in tag_result:
            tag_button = TagButton()
            tag_button.tag_id = tag.tag_id
            tag_button.tag_b_name.text = tag.name
            tag_button.tag_b_count.text = str(tag.photo_count)
            self.tag_button_grid.add_widget(tag_button)

    def clear_tags(self):
        self.tag_button_grid.clear_widgets()

    def search_tags(self):
        self.clear_tags()
        self.load_tags()


class TagViewScreen(Screen):
    tag_id = -1
    order_by = 1

    def on_enter(self):
        self.clear_grid()
        self.load_screen()

    def load_screen(self):
        tag = model.Tags.get_by_id(self.tag_id)
        self.tag_name_info.text = tag.name
        photo_count = tag.photo_count
        if photo_count > 0:
            self.tag_result_label.text = 'This tag contains ' + str(photo_count) + ' photos.'
        else:
            self.tag_result_label.text = 'This tag is currently empty!'

        photo_result = model.get_tag_photos(self.tag_id, self.order_by)
        for photo in photo_result:
            img = TagGridImage()
            img.load_img(photo_id=photo.photo_id)
            self.tag_photo_grid.add_widget(img)

    def clear_grid(self):
        self.tag_photo_grid.clear_widgets()

    def reload_name(self):
        tag = model.Tags.get_by_id(self.tag_id)
        self.tag_name_info.text = tag.name

    def modify_name_b(self):
        view = ModifyTagView()
        view.tag_id = self.tag_id
        view.open()

