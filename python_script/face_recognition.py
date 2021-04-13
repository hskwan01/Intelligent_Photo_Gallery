import dlib
import numpy as np
import pandas as pd
import os
import cv2
import uuid
import pickle
import math

from sklearn.neighbors import RadiusNeighborsClassifier

from db_model import model
from python_script import settings

df_cols = ['person_id', 'f_0', 'f_1', 'f_2', 'f_3', 'f_4', 'f_5', 'f_6', 'f_7', 'f_8', 'f_9', 'f_10', 'f_11', 'f_12',
           'f_13', 'f_14', 'f_15', 'f_16', 'f_17', 'f_18', 'f_19', 'f_20', 'f_21', 'f_22', 'f_23', 'f_24', 'f_25',
           'f_26', 'f_27', 'f_28', 'f_29', 'f_30', 'f_31', 'f_32', 'f_33', 'f_34', 'f_35', 'f_36', 'f_37', 'f_38',
           'f_39', 'f_40', 'f_41', 'f_42', 'f_43', 'f_44', 'f_45', 'f_46', 'f_47', 'f_48', 'f_49', 'f_50', 'f_51',
           'f_52', 'f_53', 'f_54', 'f_55', 'f_56', 'f_57', 'f_58', 'f_59', 'f_60', 'f_61', 'f_62', 'f_63', 'f_64',
           'f_65', 'f_66', 'f_67', 'f_68', 'f_69', 'f_70', 'f_71', 'f_72', 'f_73', 'f_74', 'f_75', 'f_76', 'f_77',
           'f_78', 'f_79', 'f_80', 'f_81', 'f_82', 'f_83', 'f_84', 'f_85', 'f_86', 'f_87', 'f_88', 'f_89', 'f_90',
           'f_91', 'f_92', 'f_93', 'f_94', 'f_95', 'f_96', 'f_97', 'f_98', 'f_99', 'f_100', 'f_101', 'f_102', 'f_103',
           'f_104', 'f_105', 'f_106', 'f_107', 'f_108', 'f_109', 'f_110', 'f_111', 'f_112', 'f_113', 'f_114', 'f_115',
           'f_116', 'f_117', 'f_118', 'f_119', 'f_120', 'f_121', 'f_122', 'f_123', 'f_124', 'f_125', 'f_126', 'f_127']

feature_cols = df_cols[1:]

clf_model_path = 'ml_model/radius_neigh.pickle'
clf_model = RadiusNeighborsClassifier(radius=0.48, weights='distance', algorithm='auto', p=2, outlier_label=-1)
clf_trained = False

face_landmark_model_path = './ml_model/shape_predictor_5_face_landmarks.dat'
face_rec_model_path = './ml_model/dlib_face_recognition_resnet_model_v1.dat'


detector = None
face_landmark = None
face_rec = None
face_clf = None


def init_face_recognition():
    global detector
    global face_landmark
    global face_rec

    detector = dlib.get_frontal_face_detector()
    face_landmark = dlib.shape_predictor(face_landmark_model_path)
    face_rec = dlib.face_recognition_model_v1(face_rec_model_path)

    if not os.path.exists(settings.Gallery_new_face_dir):
        os.makedirs(settings.Gallery_new_face_dir)

    train_model()
    recognize_face()


def detect_extract_face(img_path):
    img = cv2.imread(img_path)
    faces = detector(img, 1)
    face_list = []

    for k, d in enumerate(faces):
        shape = face_landmark(img, d)
        face_descriptor = face_rec.compute_face_descriptor(img, shape)

        crop_img = img[max(0, d.top()):min(d.bottom(), img.shape[0]), max(0, d.left()): min(d.right(), img.shape[1])]

        crop_img_path = settings.Gallery_new_face_dir + uuid.uuid4().hex + '.jpg'

        cv2.imwrite(crop_img_path, crop_img)

        face_list.append((crop_img_path, list(face_descriptor)))

    return face_list


def is_eligible_classify():
    return model.Persons.select().where(model.Persons.recognised == True).count() >= 2


def train_model():
    if is_eligible_classify():
        df = pd.DataFrame(columns=df_cols)

        for face in model.Faces.select().join(model.Persons).where(model.Persons.recognised == True):
            df = df.append(pd.Series([int(face.face_person.person_id)] + pickle.loads(face.features), index=df_cols),
                           ignore_index=True)

        clf_model.fit(df[feature_cols], df['person_id'])
        global clf_trained
        clf_trained = True


def recognize_face():
    if is_eligible_classify():
        if not clf_trained:
            train_model()
        for face in model.Faces.select().where(model.Faces.identified == False):
            person_id = clf_model.predict([pickle.loads(face.features)])[0]
            if person_id != -1:
                face.add_person_id(person_id)


def recognize_new_face():
    if is_eligible_classify():
        if not clf_trained:
            train_model()
        for face in model.Faces.select().join(model.Photos).where(model.Photos.new == True):
            person_id = clf_model.predict(pickle.loads(face.features))
            if person_id != -1:
                face.add_person_id(person_id)


def is_similar_faces(face_1, face_2):
    # check if the 2 faces are similar
    face_threshold = 0.3025
    dist = 0
    for v1, v2 in zip(face_1, face_2):
        dist += (v1 - v2) ** 2
    if dist <= face_threshold:
        return True
    else:
        return False


def suggest_similar(face_id, num_photos):
    # suggest similar photo base on the euclidean distance
    face_feature = pickle.loads(model.Faces.get_by_id(face_id).features)
    similar_ls = []

    for face in model.Faces.select().where(model.Faces.identified == False):
        if is_similar_faces(face_feature, pickle.loads(face.features)):
            similar_ls.append(face.face_id)
            if len(similar_ls) >= num_photos:
                return similar_ls
    return similar_ls




