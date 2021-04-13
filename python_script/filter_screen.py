from kivy.uix.screenmanager import Screen
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App

from python_script import util_func
from db_model import model

import pickle
import datetime


class FilterRuleLayout(BoxLayout, Label):
    filter_id = 0

    def swap_up_b(self):
        model.FilterRule.get_by_id(self.filter_id).swap_priority_up()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()

    def swap_down_b(self):
        model.FilterRule.get_by_id(self.filter_id).swap_priority_down()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()

    def delete_b(self):
        model.FilterRule.get_by_id(self.filter_id).delete_rule()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()

    def modify_b(self):
        view = ModifyConditionView()
        my_filter = model.FilterRule.get_by_id(self.filter_id)
        view.tag_set = set(pickle.loads(my_filter.c_tag_ls))
        view.person_set = set(pickle.loads(my_filter.c_person_ls))
        view.filter_id = self.filter_id
        view.c_album = my_filter.c_album
        view.a_album = my_filter.a_album
        view.a_tag = my_filter.a_tag
        if my_filter.c_create_date_af is not None:
            view.af_date = str(my_filter.c_create_date_af)
        if my_filter.c_create_date_bf is not None:
            view.bf_date = str(my_filter.c_create_date_bf)
        view.open()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()

    def apply_b(self):
        model.FilterRule.get_by_id(self.filter_id).apply_filter()


class PopupTagButton(util_func.HoverBehavior, Button):
    tag_name = ''

    def on_enter(self):
        self.background_color = (0.9, 0.65, 0.65, 1)

    def on_leave(self):
        self.background_color = (0.5, 0.5, 0.5, 1)

    def on_release(self):
        self.parent.parent.parent.parent.parent.parent.remove_tag(self.tag_name)
        self.parent.remove_widget(self)
        return


class PopupPersonButton(util_func.HoverBehavior, Button):
    tag_name = ''

    def on_enter(self):
        self.background_color = (0.9, 0.65, 0.65, 1)

    def on_leave(self):
        self.background_color = (0.5, 0.5, 0.5, 1)

    def on_release(self):
        self.parent.parent.parent.parent.parent.parent.remove_person(self.person_name)
        self.parent.remove_widget(self)
        return


class SetConditionView(ModalView):
    tag_set = set()
    person_set = set()

    def on_open(self):
        self.tag_set = set()
        self.person_set = set()

    def close_view(self):
        # close the view
        self.tag_set = set()
        self.person_set = set()
        self.dismiss()

    def next_b(self):
        # function for the 'next' button (opens the set action popup)
        try:
            if self.date_bf_inp_field.text != '':
                datetime.datetime.strptime(self.date_bf_inp_field.text, '%Y-%m-%d %H:%M:%S')
            if self.date_af_inp_field.text != '':
                datetime.datetime.strptime(self.date_af_inp_field.text, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.popup_msg_label.text = "Please make sure you enter an valid datetime format"
            return

        if len(self.tag_set) == 0 and len(self.person_set) == 0 and self.album_inp_field.text == '' \
                and self.date_bf_inp_field.text == '' and self.date_af_inp_field.text == '':
            self.popup_msg_label.text = "Please at least fill in a condition (e.g. tag / person / album)"
            return
        view = SetActionView()
        view.album_name = self.album_inp_field.text
        view.tag_set = self.tag_set
        view.person_set = self.person_set
        view.bf_time = self.date_bf_inp_field.text
        view.af_time = self.date_af_inp_field.text
        self.close_view()
        view.open()

    def add_person(self):
        person_name = self.person_inp_field.text
        if person_name != '' and person_name not in self.person_set:
            person_label = PopupPersonButton(text = person_name)
            person_label.person_name = person_name
            self.person_cond_grid.add_widget(person_label)

            self.person_set.add(person_name)
            self.person_inp_field.text = ''
        else:
            self.popup_msg_label.text = "Please make sure the person name is not a duplicate or empty"
        return

    def remove_person(self, person_name):
        self.person_set.remove(person_name)
        return

    def add_tag(self):
        tag_name = self.tag_inp_field.text
        if tag_name != '' and tag_name not in self.tag_set:
            tag_label = PopupTagButton(text = tag_name)
            tag_label.tag_name = tag_name
            self.tag_cond_grid.add_widget(tag_label)

            self.tag_set.add(tag_name)
            self.tag_inp_field.text = ''
        else:
            self.popup_msg_label.text = "Please make sure the tag name is not a duplicate or empty"
        return

    def remove_tag(self, tag_name):
        self.tag_set.remove(tag_name)
        return


class SetActionView(ModalView):
    # class for the new filter action popup
    tag_set = set()
    person_set = set()
    album_name = ''
    bf_time = ''
    af_time = ''

    def close_view(self):
        # close the view
        self.dismiss()

    def create_b(self):
        if self.album_inp_field.text == self.album_name and self.album_name != '':
            self.popup_msg_label.text = "Target album cannot be the same as the album condition"
            return
        if self.album_inp_field.text == '' and self.tag_inp_field.text == '':
            self.popup_msg_label.text = "Please specify at least 1 action (e.g. tag / album)"
            return
        model.create_filter_rule(c_tag_ls=list(self.tag_set), c_person_ls=list(self.person_set),
                                 c_album=self.album_name, a_tag=self.tag_inp_field.text,
                                 a_album = self.album_inp_field.text, c_bf_time=self.bf_time, c_af_time=self.af_time)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()


class ModifyConditionView(ModalView):
    filter_id = 0
    tag_set = set()
    person_set = set()
    c_album = ''
    a_album = ''
    a_tag = ''
    af_date = ''
    bf_date = ''

    def on_open(self):
        for tag in self.tag_set:
            tag_label = PopupTagButton(text=tag)
            tag_label.tag_name = tag
            self.tag_cond_grid.add_widget(tag_label)

        for person in self.person_set:
            person_label = PopupPersonButton(text=person)
            person_label.person_name = person
            self.person_cond_grid.add_widget(person_label)
        print('sdf', self.bf_date, self.af_date)
        self.album_inp_field.text = self.c_album
        self.date_bf_inp_field.text = self.bf_date
        self.date_af_inp_field.text = self.af_date

    def close_view(self):
        # close the view
        self.dismiss()

    def next_b(self):
        # function for the 'next' button (opens the set action popup)
        try:
            if self.date_bf_inp_field.text != '':
                datetime.datetime.strptime(self.date_bf_inp_field.text, '%Y-%m-%d %H:%M:%S')
            if self.date_af_inp_field.text != '':
                datetime.datetime.strptime(self.date_af_inp_field.text, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.popup_msg_label.text = "Please make sure you enter an valid datetime format"
            return
        if len(self.tag_set) == 0 and len(self.person_set) == 0 and self.album_inp_field.text == '' \
                and self.date_bf_inp_field.text == '' and self.date_af_inp_field.text == '':
            self.popup_msg_label.text = "Please at least fill in a condition (e.g. tag / person / album)"
            return
        view = ModifyActionView()
        view.album_name = self.album_inp_field.text
        view.tag_set = self.tag_set
        view.person_set = self.person_set
        view.a_album = self.a_album
        view.a_tag = self.a_tag
        view.filter_id = self.filter_id
        view.bf_time = self.date_bf_inp_field.text
        view.af_time = self.date_af_inp_field.text
        self.close_view()
        view.open()

    def add_person(self):
        person_name = self.person_inp_field.text
        if person_name != '' and person_name not in self.person_set:
            person_label = PopupPersonButton(text = person_name)
            person_label.person_name = person_name
            self.person_cond_grid.add_widget(person_label)

            self.person_set.add(person_name)
            self.person_inp_field.text = ''
        else:
            self.popup_msg_label.text = "Please make sure the person name is not a duplicate or empty"
        return

    def remove_person(self, person_name):
        self.person_set.remove(person_name)
        return

    def add_tag(self):
        tag_name = self.tag_inp_field.text
        if tag_name != '' and tag_name not in self.tag_set:
            tag_label = PopupTagButton(text = tag_name)
            tag_label.tag_name = tag_name
            self.tag_cond_grid.add_widget(tag_label)

            self.tag_set.add(tag_name)
            self.tag_inp_field.text = ''
        else:
            self.popup_msg_label.text = "Please make sure the tag name is not a duplicate or empty"
        return

    def remove_tag(self, tag_name):
        self.tag_set.remove(tag_name)
        return


class ModifyActionView(ModalView):
    # class for the modify filter action popup
    filter_id = 0
    tag_set = set()
    person_set = set()
    album_name = ''
    a_album = ''
    a_tag = ''
    af_time = ''
    bf_time = ''

    def on_open(self):
        self.album_inp_field.text = self.a_album
        self.tag_inp_field.text = self.a_tag

    def close_view(self):
        # close the view
        self.dismiss()

    def modify_b(self):
        if self.album_inp_field.text == self.album_name and self.album_name != '':
            self.popup_msg_label.text = "Target album cannot be the same as the album condition"
            return
        if self.album_inp_field.text == '' and self.tag_inp_field.text == '':
            self.popup_msg_label.text = "Please specify at least 1 action (e.g. tag / album)"
            return
        model.FilterRule.get_by_id(self.filter_id).modify_rule(c_tag_ls=list(self.tag_set),
                                                               c_person_ls=list(self.person_set),
                                                               c_album=self.album_name,
                                                               a_tag=self.tag_inp_field.text,
                                                               a_album = self.album_inp_field.text,
                                                               c_bf_time = self.bf_time,
                                                               c_af_time = self.af_time)
        self.close_view()
        app = App.get_running_app()
        app.root.content_screen.ids.filter_screen.update_screen()


class FilterScreen(Screen):
    # Class for the filter screen

    def on_enter(self):
        self.clear_screen()
        self.load_screen()

    def load_screen(self):
        # loads the screen
        filters = model.get_filters()
        for f in filters:
            new_filter = FilterRuleLayout()
            new_filter.filter_id = f.filter_id
            new_filter.priority_label.text = '[b]' + str(f.priority) + '[/b]'
            new_filter.c_tag_list_label.text = '[b]Tags: [/b]' + ', '.join(pickle.loads(f.c_tag_ls))
            new_filter.c_person_list_label.text = '[b]Persons: [/b]' + ', '.join(pickle.loads(f.c_person_ls))
            new_filter.c_album_label.text = '[b]Album: [/b]' + f.c_album
            date_str_af = '[b] created after: [/b]'
            if f.c_create_date_af is not None:
                date_str_af += str(f.c_create_date_af)
            new_filter.c_photo_date_label_af.text = date_str_af
            date_str_bf = '[b] created before: [/b]'
            if f.c_create_date_bf is not None:
                date_str_bf += str(f.c_create_date_bf)
            new_filter.c_photo_date_label_bf.text = date_str_bf
            new_filter.a_album_label.text = '[b] Album: [/b]' + f.a_album
            new_filter.a_tag_label.text = '[b] Tag: [/b]' + f.a_tag

            self.filter_rule_grid.add_widget(new_filter)

    def clear_screen(self):
        # clear the widgets in the grids
        self.filter_rule_grid.clear_widgets()

    def update_screen(self):
        # update the order and content of the filter rules widgets
        self.clear_screen()
        self.load_screen()

    def add_new_filter_b(self):
        # function for the add filter button (opens the popup)
        view = SetConditionView()
        view.open()

    def apply_filters_b(self):
        # function for the apply filter button
        pass
