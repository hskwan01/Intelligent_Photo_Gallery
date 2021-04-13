from peewee import *
import datetime
import os
import pickle
from shutil import copy2
import cv2
from time import mktime

from python_script import face_recognition
from python_script import settings

DATABASE = 'gallery.db'

sqlite_db = SqliteDatabase(DATABASE, pragmas=(('foreign_keys', 'on'),))


def init_db():
    # function to connect and create table if not exist
    sqlite_db.connect()
    sqlite_db.create_tables([Albums, Photos, Tags, PhotoTag, Faces, Persons, FilterRule])
    return


class BaseModel(Model):
    class Meta:
        database = sqlite_db


class Albums(BaseModel):
    # Album class
    album_id = PrimaryKeyField()
    name = CharField(unique=True, null=False)
    create_date = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                formats=['%Y-%m-%d %H:%M:%S'])
    description = TextField(default='')
    photo_count = IntegerField(default=0)

    def create_album(album_name = '', album_description = ''):
        query = Albums.select().where(Albums.name == album_name)
        if not query.exists():
            new_album, created = Albums.get_or_create(name=album_name)
            new_album.description = album_description
            new_album.save()
            return True

        return False

    def update_count(self):
        # function to update the photo count
        self.photo_count = Photos.select().where(Photos.photo_album == self.album_id).count()
        self.save()
        return

    def modify_album(self, album_name, album_description):
        # function to change the album name and description
        query = Albums.select().where((Albums.name == album_name) & (Albums.name != self.name))

        if not query.exists():
            self.name = album_name
            self.description = album_description
            self.save()
            return True

        return False

    def delete_album(self):
        # function to delete this album
        # require more code to delete the dir
        self.delete_instance()


class Tags(BaseModel):
    # Tag class
    tag_id = PrimaryKeyField()
    name = CharField(unique=True, null=False)
    photo_count = IntegerField(default=0)

    def update_count(self):
        # function to update the photo count
        count = self.photo_count = PhotoTag.select().where(PhotoTag.tag == self.tag_id).count()
        if count > 0:
            self.save()
        else:
            self.delete_instance()

    def modify_name(self, tag_name):
        # function to modify the tag name
        # return True if modified successfully
        query = Tags.select().where(Tags.name == tag_name)

        if not query.exists():
            self.name = tag_name
            self.save()
            return True

        return False


class Photos(BaseModel):
    # Photo class
    photo_id = PrimaryKeyField()
    file_name = CharField()
    import_time = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                formats=['%Y-%m-%d %H:%M:%S'])
    create_time = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                formats=['%Y-%m-%d %H:%M:%S'])
    file_path = TextField()
    view_count = IntegerField(default=0)
    last_view = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              formats=['%Y-%m-%d %H:%M:%S'])
    new = BooleanField()
    photo_album = ForeignKeyField(Albums, on_delete='SET NULL', backref='photos', null=True, default=None)
    hash = TextField(null=False, index=True)
    # description = TextField(default='')
    # favourite = BooleanField()

    def create_photo(file_name='', file_dir='', new_name='', original_path='', album_name='', tag_set=set(), h_val=''):
        # function to copy the photo and add it to the database
        # !!! Thought to increase the efficiency, create another bulk create function to handle
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_path = file_dir + new_name
        copy2(original_path, file_path)

        c_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        m_time = datetime.datetime.fromtimestamp(os.path.getmtime(original_path)).strftime('%Y-%m-%d %H:%M:%S')
        new_photo = Photos.create(file_name=file_name, import_time=c_time, file_path=file_path, view_count=0,
                                  last_view=c_time, new=True, create_time=m_time, hash=h_val)

        if album_name != '':
            album, created = Albums.get_or_create(name=album_name)
            new_photo.photo_album = album.get_id()
            new_photo.save()
            album.update_count()

        for tag_name in tag_set:
            tag, created = Tags.get_or_create(name=tag_name)
            photo_tag, created = PhotoTag.get_or_create(photo=new_photo.photo_id, tag=tag.tag_id)
            tag.update_count()

        face_list = face_recognition.detect_extract_face(new_photo.file_path)
        for face_path, face_feature in face_list:
            new_face = Faces.create(identified=False, img_path=face_path, features=pickle.dumps(face_feature),
                                    face_photo=new_photo.photo_id, face_person=None, new=True)
            new_face.save()

        return new_photo

    def view_photo(self):
        self.view_count += 1
        self.last_view = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save()
        return

    def delete_photo(self):
        album_key = self.photo_album
        tags_id_ls = self.get_tags_id()
        os.remove(self.file_path)

        for face in Faces.select().where(Faces.face_photo == self.photo_id):
            face.delete_face()

        self.delete_instance()

        if album_key is not None:
            Albums.get_by_id(album_key).update_count()

        if len(tags_id_ls) > 0:
            for tag_id in tags_id_ls:
                Tags.get_by_id(tag_id).update_count()
        return

    def get_album_id(self):
        return self.photo_album

    def get_album_name(self):
        if self.photo_album is not None:
            return Albums.get_by_id(self.photo_album).name
        return 'None'

    def get_tags_id(self):
        tags = PhotoTag.select().where(PhotoTag.photo == self.photo_id)
        return [tag.tag for tag in tags]

    def change_album(self, a_name=''):

        old_album_id = self.photo_album
        new_album_id = None
        print(a_name)
        new_dir = ''
        if a_name == '':
            if self.photo_album is None:
                return
            self.photo_album = None
            new_dir = settings.Gallery_new_photo_dir
        else:
            if self.photo_album is not None:
                if Albums.get_by_id(self.photo_album).name == a_name:
                    return
            album, created = Albums.get_or_create(name=a_name)
            new_dir = settings.Gallery_photo_dir + a_name + '/'
            self.photo_album = album.album_id
            new_album_id = album.album_id

            if not os.path.exists(new_dir):
                os.makedirs(new_dir)

        name_pos = self.file_path.rindex('/') + 1
        f_name = self.file_path[name_pos:]
        new_path = new_dir + f_name
        copy2(self.file_path, new_path)
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

        self.file_path = new_path
        self.save()

        if old_album_id is not None:
            Albums.get_by_id(old_album_id).update_count()

        if new_album_id is not None:
            Albums.get_by_id(new_album_id).update_count()

    def change_tags(self, tag_set=set()):
        o_tag_ids = self.get_tags_id()
        o_tag_set = set()
        for tag_id in o_tag_ids:
            tag = Tags.get_by_id(tag_id)
            o_tag_set.add(tag.name)

            if tag.name in tag_set:
                continue

            PhotoTag.get(PhotoTag.photo == self.photo_id, PhotoTag.tag == tag_id).delete_instance()
            tag.update_count()
        for t in tag_set:
            if t in o_tag_set:
                continue

            tag, created = Tags.get_or_create(name=t)
            photo_tag, created = PhotoTag.get_or_create(photo=self.photo_id, tag=tag.tag_id)
            tag.update_count()


class PhotoTag(BaseModel):
    # class for the many to many relationship between the Tag class and Photo class
    photo = ForeignKeyField(Photos, on_delete='CASCADE', backref='photo_tag', null=False)
    tag = ForeignKeyField(Tags, on_delete='CASCADE', backref='tag_photo', null=False)


class Persons(BaseModel):
    person_id = PrimaryKeyField()
    name = CharField(unique=True, null=False)
    photo_count = IntegerField(default=0, null=False)
    recognised = BooleanField(default=False, null=False)

    def update_count(self):
        # function to update the photo count
        old_recognised = self.recognised
        self.photo_count = Faces.select().where(Faces.face_person == self.person_id).count()
        self.save()
        if self.photo_count >= 50:
            self.recognised = True
            self.save()
        else:
            self.recognised = False
            self.save()

            # if self.photo_count <= 0:
            #     self.delete_instance()

        if self.recognised != old_recognised:
            face_recognition.train_model()
            face_recognition.recognize_face()

        return

    def modify_name(self, person_name):
        # function to change the person name
        query = Persons.select().where(Persons.name == person_name)

        if not query.exists():
            self.name = person_name
            self.save()
            return True

        return False

    def delete_person(self):
        for face in Faces.select().where(Faces.face_person == self.person_id):
            face.face_person = None
            face.identified = False
            face.save()

        self.update_count()

        if self.photo_count <= 0:
            self.delete_instance()
        return


class FilterRule(BaseModel):
    # class for upload filters
    filter_id = PrimaryKeyField()
    priority = IntegerField(null=False)
    c_album = TextField(null=True)
    c_person_ls = BlobField(null=True)
    c_tag_ls = BlobField(null=True)
    c_create_date_bf = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'], null=True)
    c_create_date_af = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'], null=True)
    a_album = TextField(null=True)
    a_tag = TextField(null=True)

    def delete_rule(self):
        query = (FilterRule.update({FilterRule.priority: FilterRule.priority - 1})
                 .where(FilterRule.priority > self.priority))
        query.execute()
        self.delete_instance()

    def swap_priority_up(self):
        if self.priority == 1:
            return

        prev_rule = FilterRule.get(FilterRule.priority == self.priority - 1)
        prev_rule.swap_priority_down()

    def swap_priority_down(self):
        if self.priority == FilterRule.select().count():
            return

        next_rule = FilterRule.get(FilterRule.priority == self.priority + 1)
        next_rule.priority = next_rule.priority - 1
        next_rule.save()
        self.priority = self.priority + 1
        self.save()
        return

    def modify_rule(self, c_tag_ls, c_person_ls, c_album, a_tag, a_album, c_bf_time, c_af_time):
        self.c_tag_ls = pickle.dumps(c_tag_ls)
        self.c_person_ls = pickle.dumps(c_person_ls)
        self.c_album = c_album
        self.a_tag = a_tag
        self.a_album = a_album
        if c_af_time != '':
            self.c_create_date_af = c_af_time
        else:
            self.c_create_date_af = None
        if c_bf_time != '':
            self.c_create_date_bf = c_bf_time
        else:
            self.c_create_date_bf = None
        self.save()

    def apply_filter(self, is_new=False):
        result = Photos.select(Photos)

        if is_new:
            result = result.where(Photos.new == True)

        if self.c_album != '':
            album = Albums.get_or_none(name=self.c_album)
            if album is None:
                return
            else:
                result = result.where(Photos.photo_album == album.album_id)

        album_result = result
        tag_ids = []
        for tag in pickle.loads(self.c_tag_ls):
            tmp_tag = Tags.get_or_none(name=tag)
            if tmp_tag is None:
                return
            else:
                tag_ids.append(tmp_tag.tag_id)
        if tag_ids:
            result = result.switch(Photos).join(PhotoTag).where(PhotoTag.tag << tag_ids).group_by(Photos.photo_id)\
                .having(fn.Count(PhotoTag.tag) == len(tag_ids))

        person_ids = []
        for person in pickle.loads(self.c_person_ls):
            tmp_person = Persons.get_or_none(name=person)
            if tmp_person is None:
                return
            else:
                person_ids.append(tmp_person.person_id)

        if person_ids:
            result = result & album_result.switch(Photos).join(Faces).where(Faces.face_person << person_ids).group_by(Photos.photo_id)\
                .having(fn.Count(Faces.face_person) == len(person_ids))

        if self.c_create_date_af is not None:
            result = result.where(Photos.create_time >= self.c_create_date_af)

        if self.c_create_date_bf is not None:
            result = result.where(Photos.create_time <= self.c_create_date_bf)

        set_album = self.a_album != ''
        set_tag = self.a_tag != ''
        file_dir = ''
        target_album = None
        target_tag = None

        if set_album:
            target_album, created = Albums.get_or_create(name=self.a_album)
            file_dir = settings.Gallery_photo_dir + self.a_album + '/'

            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

        if set_tag:
            target_tag, created = Tags.get_or_create(name=self.a_tag)

        for photo in result:
            if set_album:
                name_pos = photo.file_path.rindex('/') + 1
                f_name = photo.file_path[name_pos:]
                new_path = file_dir + f_name
                copy2(photo.file_path, new_path)
                if os.path.exists(photo.file_path):
                    os.remove(photo.file_path)

                old_album_id = photo.photo_album

                photo.photo_album = target_album.get_id()
                photo.file_path = new_path
                photo.save()

                if old_album_id is not None:
                    Albums.get_by_id(old_album_id).update_count()

            if set_tag:
                photo_tag, created = PhotoTag.get_or_create(photo=photo.photo_id, tag=target_tag.tag_id)
                print(photo_tag.photo)

        if set_album:
            target_album.update_count()
        if set_tag:
            target_tag.update_count()


class Faces(BaseModel):
    # class for faces
    face_id = PrimaryKeyField()
    identified = BooleanField(default=False, null=False)
    img_path = TextField(null=False)
    features = BlobField()
    new = BooleanField(default=True, null=False)
    face_photo = ForeignKeyField(Photos, on_delete='CASCADE', backref='photo_face', null=False)
    face_person = ForeignKeyField(Persons, on_delete='CASCADE', backref='person_face', null=True)

    def add_person(self, person_name):
        # associate person to the face
        if person_name != '':
            person, created = Persons.get_or_create(name=person_name)
            self.face_person = person.person_id
            self.identified = True
            self.new = False
            self.save()
            person.update_count()
            return True
        return False

    def add_person_id(self, person_id):
        self.face_person = person_id
        self.identified = True
        self.save()
        person = Persons.get_by_id(person_id)
        person.update_count()
        person.save()

    def delete_face(self):
        # function to correctly delete a face
        person_key = self.face_person
        os.remove(self.img_path)
        self.delete_instance()

        if person_key is not None:
            Persons.get_by_id(person_key).update_count()
        return

    def change_person(self, person_id):
        if person_id != -1:
            prev_person = self.face_person
            self.face_person = person_id
            self.identified = True
            self.save()
            person = Persons.get_by_id(person_id)
            person.update_count()

            if prev_person is not None:
                prev_p = Persons.get_by_id(prev_person)
                prev_p.update_count()
        else:
            person = Persons.get_by_id(self.face_person)
            self.face_person = None
            self.identified = False
            self.save()
            person.update_count()



# --- SEARCH RELATED FUNCTIONS ---


def select_all_photos(order_by=0):
    # function to select all photos by a certain order
    return order_search_photo(Photos.select(), order_by)


def search_photo(album_name='', tag_ls=set(), person_ls=set(), is_new=False, order_by=0):
    result = Photos.select(Photos)

    if is_new:
        result = result.where(Photos.new == True)

    if album_name != '':
        album = Albums.get_or_none(name=album_name)
        if album is None:
            return None
        else:
            result = result.where(Photos.photo_album == album.album_id)

    if tag_ls:
        tag_ids = []
        for tag in tag_ls:
            tmp_tag = Tags.get_or_none(name=tag)
            if tmp_tag is None:
                return None
            else:
                tag_ids.append(tmp_tag.tag_id)

        result = result.switch(Photos).join(PhotoTag).where(PhotoTag.tag << tag_ids).group_by(Photos.photo_id) \
            .having(fn.Count(PhotoTag.tag) == len(tag_ids))

    if person_ls:
        person_ids = []
        for person in person_ls:
            tmp_person = Persons.get_or_none(name=person)
            if tmp_person is None:
                return None
            else:
                person_ids.append(tmp_person.person_id)
        result = result.switch(Photos).join(Faces).where(Faces.face_person << person_ids).group_by(Photos.photo_id) \
            .having(fn.Count(Faces.face_person) == len(person_ids))

    return order_search_photo(result, order_by)


def order_search_photo(photo_result, order_by=0):
    # order teh search result
    if order_by == 0:
        return photo_result.order_by(Photos.import_time)
    elif order_by == 1:
        return photo_result.order_by(Photos.import_time.desc())
    elif order_by == 2:
        return photo_result.order_by(Photos.file_name)
    elif order_by == 3:
        return photo_result.order_by(Photos.file_name.desc())


# --- IMPORT RELATED FUNCTIONS ---


def set_old():
    # function to set the 'new' field of all photos to False
    query = Photos.update(new=False).where(Photos.new == True)
    query.execute()
    return


# --- TAG RELATED FUNCTIONS ---


def get_tags(search_str='', order_by=1):
    # function to get matching tags and sort it
    tag_result = Tags.select().where(Tags.name.contains(search_str))
    if order_by == 1:
        return tag_result.order_by(fn.Lower(Tags.name))
    elif order_by == -1:
        return tag_result.order_by(fn.Lower(Tags.name).desc())
    elif order_by == 2:
        return tag_result.order_by(Tags.photo_count)
    elif order_by == -2:
        return tag_result.order_by(Tags.photo_count.desc())
    return tag_result


def get_tag_photos(tag_id=-1, order_by=1):
    # function to get all photos given an album ID
    tag_photos = Photos.select().join(PhotoTag).where(PhotoTag.tag == tag_id)
    if order_by == 1:
        return tag_photos.order_by(Photos.import_time)
    elif order_by == -1:
        return tag_photos.order_by(Photos.import_time.desc())
    elif order_by == 2:
        return tag_photos.order_by(Photos.file_name)
    elif order_by == -2:
        return tag_photos.order_by(Photos.file_name.desc())
    return tag_photos


# --- ALBUM RELATED FUNCTIONS ---


def get_albums(search_str='', order_by=1):
    # function to perform a query to get all albums
    album_result = Albums.select().where(Albums.name.contains(search_str))
    if order_by == 1:
        return album_result.order_by(fn.Lower(Albums.name))
    elif order_by == -1:
        return album_result.order_by(fn.Lower(Albums.name).desc())
    elif order_by == 2:
        return album_result.order_by(Albums.photo_count)
    elif order_by == -2:
        return album_result.order_by(Albums.photo_count.desc())
    return album_result


def get_album_photos(album_id=-1, order_by=1):
    # function to get all photos given an album ID
    album_photos = Photos.select().where(Photos.photo_album == album_id)
    if order_by == 1:
        return album_photos.order_by(Photos.import_time)
    elif order_by == -1:
        return album_photos.order_by(Photos.import_time.desc())
    elif order_by == 2:
        return album_photos.order_by(Photos.file_name)
    elif order_by == -2:
        return album_photos.order_by(Photos.file_name.desc())
    return album_photos


# --- PERSON RELATED FUNCTIONS


def get_persons(search_str='', order_by=1):
    # function to perform a query to get all albums
    person_result = Persons.select().where(Persons.name.contains(search_str))
    if order_by == 1:
        return person_result.order_by(fn.Lower(Persons.name))
    elif order_by == -1:
        return person_result.order_by(fn.Lower(Persons.name).desc())
    elif order_by == 2:
        return person_result.order_by(Persons.photo_count)
    elif order_by == -2:
        return person_result.order_by(Persons.photo_count.desc())
    return person_result


def get_person_faces(person_id=-1, order_by=1):
    # function to get all photos given an album ID
    person_faces = Faces.select().where(Faces.face_person == person_id)
    if order_by == 1:
        return person_faces.order_by(Faces.face_id)
    elif order_by == -1:
        return person_faces.order_by(Faces.face_id.desc())
    return person_faces


# --- IMPORT FILTER RELATED ---

def create_filter_rule(c_tag_ls, c_person_ls, c_album, a_tag, a_album, c_bf_time, c_af_time):
    # function to create a new import filter rule
    priority = FilterRule.select().count() + 1
    new_f_rule = FilterRule.create(priority=priority, c_album=c_album, c_person_ls=pickle.dumps(c_person_ls),
                                   c_tag_ls=pickle.dumps(c_tag_ls), a_album=a_album, a_tag=a_tag)
    if c_af_time != '':
        new_f_rule.c_create_date_af = c_af_time
    if c_bf_time != '':
        new_f_rule.c_create_date_bf = c_bf_time
    new_f_rule.save()
    return


def filter_new_photos():
    # function to apply the filters on photo import
    for filter_rule in FilterRule.select():
        filter_rule.apply_filter(is_new=True)


def filter_all_photos():
    # function to apply all filters to existing photos
    for filter_rule in FilterRule.select():
        filter_rule.apply_filter()


def get_filters():
    # function to return all filters in order of the priority
    return FilterRule.select().order_by(FilterRule.priority)


def duplicate_photo_search():
    new_photos = Photos.select().where(Photos.new == True)
    duplicate_ls = []
    for photo in new_photos:
        query = Photos.select().where((Photos.hash == photo.hash) & (Photos.new == False))
        if query.exists():
            duplicate_ls.append(photo.photo_id)

    if duplicate_ls:
        return duplicate_ls
    return None

