from kivy.uix.screenmanager import Screen

from python_script import face_recognition


class ManagementScreen(Screen):
    def on_enter(self):
        pass

    def load_screen(self):
        pass

    def force_train_b(self):
        face_recognition.train_model()
        return

    def force_recognize_b(self):
        face_recognition.recognize_face()
        return
