from pathlib import Path
import mimetypes

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (
    StringProperty, NumericProperty, ReferenceListProperty, ObjectProperty)
from kivy.resources import resource_add_path
from kivy.core.text import LabelBase, DEFAULT_FONT
import cv2


resource_add_path(str(Path(__file__).parent / "resources"))

LabelBase.register(DEFAULT_FONT, "fonts/NotoSansCJKjp-Regular.otf")
LabelBase.register("code_input", "fonts/NotoSansMonoCJKjp-Regular.otf")


class IconBase:
    icon = StringProperty("")
    padding_left = NumericProperty(0)
    padding_top = NumericProperty(0)
    padding_right = NumericProperty(0)
    padding_bottom = NumericProperty(0)
    padding = ReferenceListProperty(
        padding_left, padding_top, padding_right, padding_bottom)


class IconWidget(IconBase, Widget):
    pass


class IconButton(IconBase, Button):
    pass


class IconToggleButton(IconBase, ToggleButton):
    pass


class ChooseFolderPopupLayout(RelativeLayout):
    close = ObjectProperty(None)
    set_folder_function = ObjectProperty(None)
    file_chooser = ObjectProperty(None)

    def set_folder(self):
        if self.file_chooser.selection:
            return self.set_folder_function(self.file_chooser.selection[0])


class ChooseFolderPopup(Popup):
    def __init__(self, set_folder_function, function_after_close=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.content = ChooseFolderPopupLayout()
        self.content.close = self.dismiss
        self.content.set_folder_function = set_folder_function
        self.function_after_close = function_after_close

        def close():
            self.dismiss()
            if self.function_after_close:
                self.function_after_close()


class ChooseFilePopupLayout(RelativeLayout):
    close = ObjectProperty(None)
    set_file_path_function = ObjectProperty(None)
    file_chooser = ObjectProperty(None)

    def set_file_path(self):
        if self.file_chooser.selection:
            return self.set_file_path_function(self.file_chooser.selection[0])


class ChooseFilePopup(Popup):
    def __init__(self, set_file_path_function, function_after_close=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.content = ChooseFilePopupLayout()
        self.content.close = self.dismiss
        self.content.set_file_path_function = set_file_path_function
        self.function_after_close = function_after_close

        def close():
            self.dismiss()
            if self.function_after_close:
                self.function_after_close()


class AlertPopupLayout(RelativeLayout):
    close = ObjectProperty(None)
    message = StringProperty("")


class AlertPopup(Popup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.content = AlertPopupLayout()
        self.content.close = self.dismiss
        self.content.message = message


class SearchScreen(Screen):
    # TODO: Fix variable name: image_to_search_input
    searching_place_input = ObjectProperty(None)
    image_to_search_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_mime_types = ("image/png", "image/jpeg",
                                 "image/gif", "image/bmp")

    def show_choose_searching_place(self):
        popup = ChooseFolderPopup(self.set_searching_place)
        popup.open()

    def set_searching_place(self, path):
        if Path(path).is_dir():
            self.searching_place_input.text = path
            return True
        elif Path(path).is_file():
            popup = AlertPopup("It isn't directory.")
            popup.open()

    def show_choose_image_to_search(self):
        popup = ChooseFolderPopup(self.set_image_to_search)
        popup.open()

    def set_image_to_search(self, path):
        if Path(path).is_file():
            print(mimetypes.guess_type(path))
            if mimetypes.guess_type(path)[0] in self.image_mime_types:
                self.image_to_search_input.text = path
                return True
            else:
                popup = AlertPopup("It isn't  image or supported files.")
                popup.open()
        elif Path(path).is_dir():
            popup = AlertPopup("It isn't file.")
            popup.open()
    
    # def search_and_show_image(self):
    #     result = self.search_image()
    #     if result

    def search_image(self):
        # --- validation
        search_failed = False
        if not (self.searching_place_input.text or
                self.image_to_search_input.text):
            search_failed = True
        else:
            searching_place = Path(self.searching_place_input.text)
            image_to_search = Path(self.image_to_search_input.text)
            if image_to_search.is_file():
                is_image = (mimetypes.guess_type(str(image_to_search))[0]
                            in self.image_mime_types)
            if not (searching_place.is_dir() or is_image):
                search_failed = True
        if search_failed:
            popup = AlertPopup("The input is incorrect or not entered.")
            popup.open()
            return False
        # ---
        IMAGE_SIZE = (100, 100)
        print(searching_place, image_to_search)
        image_to_search = str(image_to_search)
        target_img = cv2.imread(image_to_search)
        target_img = cv2.resize(target_img, IMAGE_SIZE)
        target_hist = cv2.calcHist([target_img], [0], None, [256], [0, 256])
        hists = {}
        for file_path in searching_place.iterdir():
            file_path = str(file_path)
            if (not Path(file_path).is_file() or
                    file_path == image_to_search):
                continue
            else:
                mime = mimetypes.guess_type(file_path)
                if not(mime[0] in self.image_mime_types):
                    continue
                comparing_img_path = str(searching_place / file_path)
                comparing_img = cv2.imread(comparing_img_path)
                comparing_img = cv2.resize(comparing_img, IMAGE_SIZE)
                comparing_hist = cv2.calcHist(
                    [comparing_img], [0], None, [256], [0, 256])
                ret = cv2.compareHist(target_hist, comparing_hist, 0)
                hists[file_path] = ret
                del comparing_img
        del target_img
        hists_max = max(hists.values())
        for file_path, hist in hists.items():
            if hists_max == hist:
                return file_path


class NiterugaApp(App):
    def __init__(self):
        super().__init__()
        self.title = "Niteruga"

    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(SearchScreen(name="search"))
        return self.sm


def main():
    NiterugaApp().run()


if __name__ == "__main__":
    main()
