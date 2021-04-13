from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.app import App

from copy import copy, deepcopy

from python_script import util_func

from db_model import model


class DisplayOptionButton(util_func.HoverBehavior, Button):
    def on_release(self):
        # defined in gallery.kv file
        pass

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)

    def large_b(self):
        app = App.get_running_app()
        app.root.content_screen.search_screen.set_large_display()

    def standard_b(self):
        app = App.get_running_app()
        app.root.content_screen.search_screen.set_medium_display()

    def small_b(self):
        app = App.get_running_app()
        app.root.content_screen.search_screen.set_small_display()


class SearchScreenButton(util_func.HoverBehavior, Button):
    def on_release(self):
        # defined in gallery.kv file
        pass

    def on_enter(self):
        self.background_color = (0.8, 0.8, 0.8, 1)

    def on_leave(self):
        self.background_color = (1, 1, 1, 1)


class SearchGridImage(ButtonBehavior, util_func.HoverBehavior, Image):
    photo_id = -1

    def load_img(self, photo_id):
        self.photo_id = photo_id
        self.source = model.Photos.get_by_id(photo_id).file_path

    def on_release(self):
        app = App.get_running_app()
        app.root.content_screen.ids.view_screen.photo_id = self.photo_id
        app.root.content_screen.current = 'view_screen'


class SearchScreen(Screen):
    search_content = ObjectProperty()
    search_result = None
    search_count = 0

    def on_enter(self):
        self.search_content.text=''
        self.clear_result()
        self.search_result = model.search_photo(order_by=1)
        self.load_result(title='[b]All photos[/b]')

    def on_pre_leave(self):
        self.clear_result()

    def load_result(self, title):
        self.search_result_label.text = title
        if self.search_result is None:
            self.load_more_button.text = 'All results are loaded'
            self.load_more_button.disabled = True
            return
        i=0
        for row in self.search_result:
            img = SearchGridImage()
            img.load_img(photo_id=row.photo_id)
            self.search_result_grid.add_widget(img)
            i += 1
            if i >= 80:
                break
        self.search_count = i

        if self.search_count >= len(self.search_result):
            self.load_more_button.text = 'All results are loaded'
            self.load_more_button.disabled = True
        else:
            self.load_more_button.text = 'Load more results'
            self.load_more_button.disabled = False

    def load_more(self):
        if self.search_result is None:
            return
        t_count = len(self.search_result)

        i=0
        if self.search_count <= t_count:
            for row in self.search_result[self.search_count:]:
                img = SearchGridImage()
                img.load_img(photo_id=row.photo_id)
                self.search_result_grid.add_widget(img)
                i += 1
                if i >= 40:
                    break
        self.search_count += i
        if self.search_count >= len(self.search_result):
            self.load_more_button.text = 'All results are loaded'
            self.load_more_button.disabled = True
        else:
            self.load_more_button.text = 'Load more results'
            self.load_more_button.disabled = False

    def clear_result(self):
        self.search_count = 0
        self.search_result_grid.clear_widgets()
        return

    def search_bar_search(self):
        a_name, t_ls, p_ls, is_new = parse_search_content(self.search_content.text)
        result_str = '[b]Search Result[/b]\n[b]ALBUM[/b]: '

        if a_name == '' and t_ls == set() and p_ls == set() and is_new is False:
            self.search_result = model.search_photo(order_by=1)
            self.clear_result()
            self.load_result('[b]All photos[/b]')
            return

        result_str = result_str + a_name + ' [b]TAGS[/b]: ' + ', '.join(t_ls) + ' [b]PERSONS[/b]: ' + ', '.join(p_ls)
        self.search_result = model.search_photo(album_name=a_name, tag_ls=t_ls, person_ls=p_ls, is_new=is_new,
                                                order_by=1)
        self.clear_result()
        self.load_result(result_str)

    def advanced_search(self):
        pass

    def set_large_display(self):
        self.search_result_grid.cols = 3
        self.search_result_grid.row_default_height = 320

    def set_medium_display(self):
        self.search_result_grid.cols = 5
        self.search_result_grid.row_default_height = 200

    def set_small_display(self):
        self.search_result_grid.cols = 7
        self.search_result_grid.row_default_height = 140


def parse_search_content(search_str):
    # function to parse the search string
    album_name = ''
    tag_ls = set()
    person_ls = set()
    is_new = False

    for phrase in search_str.split(','):
        phrase = phrase.strip(' ')

        if phrase == 'new':
            is_new = True

        loc = phrase.find(':')
        if loc == -1:
            continue
        header = phrase[:loc].strip(' ')
        content = phrase[loc + 1:].strip(' ')

        if header == 'a' or header == 'album':
            album_name = content

        if header == 't' or header == 'tag':
            tag_ls.add(content)

        if header == 'p' or header == 'person':
            person_ls.add(content)


    return album_name, tag_ls, person_ls, is_new
