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
from python_script import face_recognition


class FaceInputView(ModalView):
    # Modal view for labeling new faces
    face_id = -1

    def on_open(self):
        self.face_image.source = model.Faces.get_by_id(self.face_id).img_path

    def close_view(self):
        self.dismiss()

    def submit_b(self):
        model.Faces.get_by_id(self.face_id).add_person(str(self.input_text.text))
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.unidentified_faces_screen.reload_screen()

    def find_similar_b(self):
        if str(self.input_text.text) != '':
            model.Faces.get_by_id(self.face_id).add_person(str(self.input_text.text))
            app = App.get_running_app()
            app.root.content_screen.ids.unidentified_faces_screen.reload_screen()
            self.close_view()
            view = SimilarFacesView()
            view.face_id = self.face_id
            view.person_id = model.Faces.get_by_id(self.face_id).face_person
            view.open()
            app = App.get_running_app()
            app.root.content_screen.ids.unidentified_faces_screen.reload_screen()

    def delete_b(self):
        model.Faces.get_by_id(self.face_id).delete_face()
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.unidentified_faces_screen.reload_screen()


class SimilarFacesView(ModalView):
    # Model view for finding similar unidentified faces
    face_id = -1
    person_id = -1

    def on_open(self):
        for face in face_recognition.suggest_similar(self.face_id, 56):
            img = SimilarGridImage()
            img.load_img(face)
            self.faces_button_grid.add_widget(img)

        self.person_name_label.text = model.Persons.get_by_id(self.person_id).name
        self.face_image.source = model.Faces.get_by_id(self.face_id).img_path

    def close_view(self):
        self.dismiss()

    def confirm_b(self):
        person_name = model.Persons.get_by_id(self.person_id).name
        for widget in self.faces_button_grid.children:
            model.Faces.get_by_id(widget.face_id).add_person(person_name)
        self.dismiss()
        app = App.get_running_app()
        app.root.content_screen.ids.unidentified_faces_screen.reload_screen()


class FaceOptionView(ModalView):
    # Modal view for selecting different options for an identified face
    face_id = -1

    def on_open(self):
        self.face_image.source = model.Faces.get_by_id(self.face_id).img_path
        return

    def close_view(self):
        self.dismiss()

    def view_similar_b(self):
        self.close_view()
        view = SimilarFacesView()
        view.face_id = self.face_id
        view.person_id = model.Faces.get_by_id(self.face_id).face_person
        view.open()

    def change_person_b(self):
        view = ChangePersonView()
        view.face_id = self.face_id
        view.open()
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.clear_faces()
        app.root.content_screen.ids.person_view_screen.load_screen()
        self.close_view()

    def view_photo_b(self):
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.view_screen.photo_id = model.Faces.get_by_id(self.face_id).face_photo
        app.root.content_screen.current = 'view_screen'

    def delete_face_b(self):
        model.Faces.get_by_id(self.face_id).delete_face()
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.clear_faces()
        app.root.content_screen.ids.person_view_screen.load_screen()


class ModifyPersonView(ModalView):
    # Modal view for changing person name
    person_id=-1

    def close_view(self):
        self.dismiss()

    def confirm_b(self):
        model.Persons.get_by_id(self.person_id).modify_name(person_name=self.input_text.text)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.reload_name()

    def cancel_b(self):
        self.close_view()


class DeletePersonView(ModalView):
    # Modal view for changing person name
    person_id=-1

    def close_view(self):
        self.dismiss()

    def confirm_b(self):
        model.Persons.get_by_id(self.person_id).delete_person()
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.current = 'person_screen'

    def cancel_b(self):
        self.close_view()


class ChangePersonView(ModalView):
    face_id = -1

    def on_open(self):
        person_result = model.get_persons('', 1)
        for person in person_result:
            person_button = PersonChangeButton()
            person_button.load_button(person.person_id)
            person_button.face_id=self.face_id
            self.person_button_grid.add_widget(person_button)

    def close_view(self):
        self.person_button_grid.clear_widgets()
        self.dismiss()
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.clear_faces()
        app.root.content_screen.ids.person_view_screen.load_screen()

    def remove_person_b(self):
        face = model.Faces.get_by_id(self.face_id)
        face.change_person(-1)
        self.dismiss()

    def save_and_close(self):
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.person_view_screen.clear_faces()
        app.root.content_screen.ids.person_view_screen.load_screen()


class PersonChangeButton(util_func.HoverBehavior, Button):
    person_id = -1
    face_id = -1

    def on_release(self):
        face = model.Faces.get_by_id(self.face_id)
        face.change_person(self.person_id)
        self.parent.parent.parent.parent.save_and_close()

    def load_button(self, person_id):
        self.person_id = person_id
        person = model.Persons.get_by_id(self.person_id)
        self.text = '[b]' +  person.name + '[/b] (' + str(person.photo_count) + ')'

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class FaceOptionButton(util_func.HoverBehavior, Button):
    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class PersonScreenButton(util_func.HoverBehavior, Button):
    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def new_person_b(self):
        pass

    def unidentified_person_b(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'unidentified_faces_screen'


class PersonButton(util_func.HoverBehavior, BoxLayout, Button):
    person_id = -1

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.current = 'person_view_screen'
        app.root.content_screen.ids.person_view_screen.person_id = self.person_id

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class SimilarGridImage(ButtonBehavior, util_func.HoverBehavior, Image):
    face_id = -1

    def load_img(self, face_id):
        self.face_id = face_id
        self.source = model.Faces.get_by_id(face_id).img_path
        return

    def on_release(self):
        self.parent.remove_widget(self)


class FaceGridImage(ButtonBehavior, util_func.HoverBehavior, Image):
    # for unidentified screen
    face_id = -1

    def load_img(self, face_id):
        self.face_id = face_id
        self.source = model.Faces.get_by_id(face_id).img_path
        return

    def on_release(self):
        view = FaceInputView()
        view.face_id = self.face_id
        view.open()
        return


class FaceGridImage2(ButtonBehavior, util_func.HoverBehavior, Image):
    # for the person view screen
    face_id = -1

    def load_img(self, face_id):
        self.face_id = face_id
        self.source = model.Faces.get_by_id(face_id).img_path
        return

    def on_release(self):
        view = FaceOptionView()
        view.face_id = self.face_id
        view.open()


class PersonScreen(Screen):
    search_content = ObjectProperty()
    # current_tag = -1
    order_by = 1

    def on_enter(self):
        self.clear_persons()
        self.load_screen()

    def load_screen(self):
        person_result = model.get_persons(self.search_content.text, self.order_by)
        for person in person_result:
            person_button = PersonButton()
            person_button.person_id = person.person_id
            person_button.person_b_name.text = person.name
            person_button.person_b_count.text = str(person.photo_count)
            self.person_button_grid.add_widget(person_button)

    def clear_persons(self):
        self.person_button_grid.clear_widgets()

    def search_persons(self):
        self.clear_persons()
        self.load_screen()


class UnidentifiedFacesScreen(Screen):
    def on_enter(self):
        self.clear_faces()
        self.load_screen()

    def on_pre_leave(self):
        self.clear_faces()

    def load_screen(self):
        for face in model.Faces.select().where(model.Faces.identified == False).order_by(model.Faces.face_id.desc()):
            img = FaceGridImage()
            img.load_img(face.face_id)
            self.faces_button_grid.add_widget(img)

    def clear_faces(self):
        self.faces_button_grid.clear_widgets()

    def reload_screen(self):
        self.clear_faces()
        self.load_screen()


class PersonViewScreen(Screen):
    person_id = -1
    order_by = 1

    def on_enter(self):
        self.clear_faces()
        self.load_screen()

    def on_pre_leave(self):
        self.clear_faces()

    def load_screen(self):
        person = model.Persons.get_by_id(self.person_id)
        self.person_name_label.text = '[b]' + person.name + '[/b]'
        self.photo_count_label.text = 'There are ' + str(person.photo_count) + ' faces for this person.'
        photo_count = person.photo_count
        if photo_count > 0:
            self.photo_count_label.text= 'There are ' + str(photo_count) + ' faces marked as this person.'
        else:
            self.photo_count_label.text = 'There is currently no identified faces for this person.'

        face_result = model.get_person_faces(self.person_id, self.order_by)
        for face in face_result:
            img = FaceGridImage2()
            img.load_img(face_id=face.face_id)
            self.faces_button_grid.add_widget(img)

    def clear_faces(self):
        self.faces_button_grid.clear_widgets()

    def modify_name_b(self):
        view = ModifyPersonView()
        view.person_id = self.person_id
        view.open()

    def reload_name(self):
        person = model.Persons.get_by_id(self.person_id)
        self.person_name_label.text = '[b]' + person.name + '[/b]'

    def delete_person_b(self):
        view = DeletePersonView()
        view.person_id = self.person_id
        view.open()


