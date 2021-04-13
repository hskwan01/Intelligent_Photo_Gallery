from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.modalview import ModalView

from python_script import util_func
from db_model import model


class ModifyPhotoView(ModalView):
    t_set = set()
    a_name = ''
    photo_id = -1

    def on_open(self):
        self.album_inp_field.text = self.a_name
        for tag in self.t_set:
            tag_label = ViewModifyTagButton(text=tag)
            tag_label.tag_name = tag
            self.tag_grid.add_widget(tag_label)

    def close_view(self):
        # close the view
        self.tag_grid.clear_widgets()
        self.dismiss()

    def add_tag(self):
        tag_name = self.tag_inp_field.text
        if tag_name != '' and tag_name not in self.t_set:
            tag_label = ViewModifyTagButton(text = tag_name)
            tag_label.tag_name = tag_name
            self.tag_grid.add_widget(tag_label)

            self.t_set.add(tag_name)
            self.tag_inp_field.text = ''
        else:
            self.popup_msg_label.text = "Tag name cannot be a duplicated or empty"
        return

    def remove_tag(self, tag_name):
        self.t_set.remove(tag_name)
        return

    def confirm_modify_b(self):
        photo = model.Photos.get_by_id(self.photo_id)
        photo.change_album(self.album_inp_field.text)
        photo.change_tags(self.t_set)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.view_screen.clear_screen()
        app.root.content_screen.view_screen.load_screen()
        return


class ViewModifyTagButton(util_func.HoverBehavior, Button):
    tag_name = ''

    def on_enter(self):
        self.background_color = (0.9, 0.65, 0.65, 1)

    def on_leave(self):
        self.background_color = (0.5, 0.5, 0.5, 1)

    def on_release(self):
        self.parent.parent.parent.parent.remove_tag(self.tag_name)
        self.parent.remove_widget(self)
        return


class ViewTagButton(util_func.HoverBehavior, Button):
    tag_id = -1

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'tag_view_screen'
        app.root.content_screen.ids.tag_view_screen.tag_id = self.tag_id

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class ViewPersonButton(util_func.HoverBehavior, Button):
    person_id = -1

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.person_id = self.person_id
        app.root.content_screen.current = 'person_view_screen'

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class ViewScreenButton(util_func.HoverBehavior, Button):
    def on_release(self):
        # defined in gallery.kv file
        pass

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def delete_photo_b(self):
        app = App.get_running_app()
        app.root.content_screen.view_screen.delete_photo()

    def modify_photo_b(self):
        # function for modify button
        app = App.get_running_app()
        app.root.content_screen.view_screen.modify_photo()


class ViewScreen(Screen):
    photo_id = -1

    def on_enter(self):
        self.clear_screen()
        self.load_screen()

    def load_screen(self):
        photo = model.Photos.get_by_id(self.photo_id)
        self.title_info.text = '[b]' + photo.file_name + '[/b]'
        self.import_datetime_info.text = str(photo.import_time)
        self.create_datetime_info.text = str(photo.create_time)
        self.display_image.source = photo.file_path
        self.album_info.text = photo.get_album_name()
        photo.view_photo()

        for tag in model.Tags.select().join(model.PhotoTag).where(model.PhotoTag.photo == self.photo_id):
            tag_button = ViewTagButton()
            tag_button.tag_id = tag.tag_id
            tag_button.text = tag.name
            self.tag_grid.add_widget(tag_button)

        tmp_ls = []

        for person in model.Persons.select().join(model.Faces).where(model.Faces.face_photo == self.photo_id):
            if person.person_id in tmp_ls:
                continue
            tmp_ls.append(person.person_id)
            person_button = ViewPersonButton()
            person_button.person_id = person.person_id
            person_button.text = person.name
            self.person_grid.add_widget(person_button)

    def clear_screen(self):
        self.person_grid.clear_widgets()
        self.tag_grid.clear_widgets()

    def delete_photo(self):
        model.Photos.get_by_id(self.photo_id).delete_photo()
        app = App.get_running_app()
        app.root.content_screen.current = 'search_screen'

    def modify_photo(self):
        view = ModifyPhotoView()
        tag_set = set()
        for tag in model.Tags.select().join(model.PhotoTag).where(model.PhotoTag.photo == self.photo_id):
            tag_set.add(tag.name)
        view.t_set = tag_set
        if model.Photos.get_by_id(self.photo_id).photo_album is not None:
            view.a_name = model.Photos.get_by_id(self.photo_id).get_album_name()
        view.photo_id = self.photo_id
        view.open()
