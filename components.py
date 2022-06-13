from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineAvatarIconListItem
from kivymd.uix.imagelist import SmartTileWithLabel
from kivy.lang.builder import Builder
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
import os
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivymd.uix.snackbar import Snackbar
from kivy.core.window import Window
from kivy.metrics import dp

home_button = Builder.load_string("""
<HomeButton>:
    icon: 'home'
    theme_text_color: 'Custom'
    text_color: app.theme_cls.primary_color
    user_font_size: 33
""")


class HomeButton(MDIconButton):
    pass


checkbox_widget = Builder.load_string("""
<CheckboxWidget>:
    cols: 2
    size_hint_y: None
    height: dp(48)
    MDCheckbox:
        id: orig_file_delete
        size_hint: None, None
        size: dp(48), dp(48)
        on_active:
    MDLabel:
        text: root.text
        size_hint_y: None
        height: dp(48)
""")


class CheckboxWidget(GridLayout):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(CheckboxWidget, self).__init__(**kwargs)


number_input_widget = Builder.load_string("""
<NumberInputWidget>:  
    cols: 2
    size_hint_y: None
    height: dp(48) 
    MDLabel:
        text: root.text
        size_hint_x: None
        width: 140 
    MDTextField:
        id: page_no
        text: '1'
        size_hint_x: None
        width: dp(40)    

""")


class NumberInputWidget(GridLayout):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(NumberInputWidget, self).__init__(**kwargs)


"""
All these custom widgets can update a Dictionary which is declared
 inside another class with Kivy DictProperty(). Any other kivy Properties 
 cannot be used for this requirement. Still confusing how only kivy DictProperty 
 can update a Dictionary which is declared inside another class. 
"""

get_file_name_content = Builder.load_string("""
<GetFileNameContent>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(50)
    
    MDTextField:
        id: file_name_input
        hint_text: 'Enter file name'
""")


class GetFileNameContent(BoxLayout):
    pass


progress_content = Builder.load_string("""
<ProgressContent>:
    orientation: 'vertical'
    padding: 10
    size_hint_y: None
    height: root.ids.message.height + root.ids.progress.height + root.ids.space.height
    pos_hint: {'top': 0.95}
    MDLabel:
        id: message
        text: 'Creating pdf. please wait...'
        size_hint_y: None
        height: self.texture_size[1]+30
    Widget:
        id: space
        size_hint_y: None
        height: 30
    MDProgressBar:
        id: progress
        type: 'indeterminate'
        running_duration: 0.5
        catching_duration: 0.3
    Widget:
""")


class ProgressContent(BoxLayout):
    pass


class ToastSnack(Snackbar):
    def __init__(self, text, duration=2, buttons=0, **kwargs):
        super(ToastSnack, self).__init__(**kwargs)
        self.text = f'[size=20]   {text}'
        self.snackbar_x = dp(30)
        self.snackbar_y = dp(30)
        self.size_hint_x = (Window.width - (dp(60))) / Window.width
        self.duration = duration
        if buttons:
            self.buttons = buttons
        # self.bg_color = (0, 153/255, 230/255, 1)


class ImgToPdfImageWidget(SmartTileWithLabel):
    def __init__(self, file, file_size, page_no, selected_list, **kwargs):
        super(ImgToPdfImageWidget, self).__init__(**kwargs)
        self.source = file
        self.file_name = os.path.basename(file)
        self.file_size = file_size
        self.selected_dict = selected_list  # the selection list
        self.size_hint = (self.width, None)
        self.height = self.height * 3
        self.page_number = page_no
        self.tile_text_color = (217 / 255.0, 217 / 255.0, 217 / 255.0, 1)
        self.text = f"\n [size=13][color=#ffffff]{self.file_name} \n  [color=#b3ecff]({self.file_size})\n"
        self.ids.box.add_widget(MDIconButton(icon='delete', theme_text_color="Custom",
                                             text_color=(26 / 255.0, 198 / 255.0, 255 / 255.0, 1),
                                             on_press=self.remove_image))

    def remove_image(self, *args):
        del self.selected_dict[self.page_number]  # update the dict
        self.parent.remove_widget(self)


merge_pdf_widget = Builder.load_string("""
<MergePdfWidget>:
    IconLeftWidget:
        icon: 'file-pdf'  
        theme_text_color: "Custom"
        color: 1, 0, 0, 1
    IconRightWidget:
        icon: 'close'
        on_release: root.remove_pdf()
""")


class MergePdfWidget(TwoLineAvatarIconListItem):
    def __init__(self, file, file_size, pdf_no, selected_list, **kwargs):
        super(MergePdfWidget, self).__init__(**kwargs)
        self.text = os.path.basename(file)
        self.selected_dict = selected_list
        self.pdf_no = pdf_no
        self.secondary_text = f"[color=#0086b3] {file_size}"

    def remove_pdf(self, *args):
        del self.selected_dict[self.pdf_no]  # update the dict
        self.parent.remove_widget(self)


single_item_widget = Builder.load_string("""
<SingleItemWidget>:
    IconLeftWidget:
        icon: root.custom_icon
    IconRightWidget:
        icon: 'close'
        on_release: root.remove_pdf()
""")


class SingleItemWidget(OneLineAvatarIconListItem):
    custom_icon = StringProperty('')

    def __init__(self, file_dict, icon, **kwargs):
        super(SingleItemWidget, self).__init__(**kwargs)
        self.dict_from_other_class = file_dict  # Getting DictProperty into this class from another class.
        self.text = os.path.basename(self.dict_from_other_class['key'])
        self.custom_icon = icon

    def remove_pdf(self, *args):
        del self.dict_from_other_class['key']  # update the main Dictionary inside another class
        self.parent.remove_widget(self)
