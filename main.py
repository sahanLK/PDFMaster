from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.properties import DictProperty
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
import os
import components
import time
import functions
import threading
from kivy.utils import platform


if platform == 'android':
    # from android import loadingscreen
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                         Permission.READ_EXTERNAL_STORAGE])
else:
    Window.size = (450, 620)


class HomeScreen(Screen):
    pass


class ImgToPdfScreen(Screen):
    selection_list = DictProperty()
    pdf_quality = NumericProperty(1)
    pdf_size = StringProperty('A4')
    orientation = StringProperty('P')
    page_numbering = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(ImgToPdfScreen, self).__init__(**kwargs)
        self.progress_pop = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.ProgressContent(),
        )
        self.file_name_popup = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.GetFileNameContent(),
            buttons=[
                MDFlatButton(text='Close', on_release=self.close_filename_popup),
                MDFlatButton(text='Create PDF', on_release=self.start),
            ])
        self.success_msg = components.ToastSnack(
            text='PDF created successfully...',
            duration=7,
            buttons=[
                MDFlatButton(text='[color=#ffffff][size=20]open', on_release=self.open_file),
            ])
        self.err_msg = components.ToastSnack(text='Error when creating pdf...')

    def start_progress(self, *args):
        self.progress_pop.content_cls.ids.progress.start()
        self.progress_pop.open()

    def close_progress(self, *args):
        time.sleep(0.5)
        self.progress_pop.content_cls.ids.progress.stop()
        self.progress_pop.dismiss()

    # Open the popup.
    def image_chooser_popup(self):
        extention_list = ['.jpg', '.JPEG', '.JPG', '.png', '.PNG']
        functions.file_chooser_popup(self, 'multi', extention_list, self.selected)
        MDApp.get_running_app().file_manager_open = True

    # Exit from file manager
    def exit_manager(self, *args):
        self.file_chooser.close()  # file_chooser is in functions.py
        MDApp.get_running_app().file_manager_open = False

    # Checking and filtering user selected files and updating the List Property
    def selected(self, *args):
        self.file_chooser.close()  # this _popup is in functions.py
        MDApp.get_running_app().file_manager_open = False

        for file in self.file_chooser.selection:
            # get an unique id for widget.
            page_no = functions.get_unique_id(self.selection_list)
            valid_extensions = ['.jpg', '.JPG', '.png', '.PNG']  # Allowed Image Extensions
            file_ext = os.path.splitext(file)[1]
            if file_ext in valid_extensions:
                self.selection_list[page_no] = file
                # Get the image size
                file = os.path.abspath(file)
                file_size = functions.get_file_size(file)
                # Add the image widget to the preview pane.
                image_widget = components.ImgToPdfImageWidget(file, file_size, page_no, self.selection_list)
                self.ids.img_to_pdf_preview_pane.add_widget(image_widget)
                page_no += 1

    # Update the Page count title.
    def on_selection_list(self, *args):
        page_count_title = functions.update_counter_title(self.selection_list, 'Page', 'Pages')
        self.ids.bottom_toolbar.title = page_count_title

    # Closing the File Name Popup
    def close_filename_popup(self, *args):
        self.file_name_popup.dismiss()

    def clear_selection_completely(self, *args):
        self.ids.img_to_pdf_preview_pane.clear_widgets()
        self.selection_list.clear()

    # Paper sizes define methods.
    def _set_size_a3(self, checkbox, state, *args):
        self.pdf_size = 'A3'

    def _set_size_a4(self, checkbox, state, *args):
        self.pdf_size = 'A4'

    def _set_size_a5(self, checkbox, state, *args):
        self.pdf_size = 'A5'

    def _set_size_letter(self, checkbox, state, *args):
        self.pdf_size = 'Letter'
        
    def _set_size_legal(self, checkbox, state, *args):
        self.pdf_size = 'Legal'

    def _set_size_custom(self, *args):
        pass

    # PDF quality define methods.
    def _set_quality_normal(self, *args):
        self.pdf_quality = 1

    def _set_quality_medium(self, *args):
        self.pdf_quality = 2

    def _set_quality_low(self, *args):
        self.pdf_quality = 3

    # Set page orientation.
    def _set_orient_portrait(self, *args):
        self.orientation = 'P'

    def _set_orient_landscape(self, *args):
        self.orientation = 'L'

    # Page Numbering
    def _set_page_numbering(self, switch, value, *args):
        if value:
            self.page_numbering = 1
        else:
            self.page_numbering = 0

    # Get the file name
    def get_file_name(self, *args):
        # Check if everything is ready correctly.
        if not self.selection_list.keys():
            components.ToastSnack(text='At least one image required').open()
            return

        margins = [self.ids.left_margin_field.text, self.ids.top_margin_field.text, self.ids.right_margin_field.text]
        for margin in margins:
            if margin:
                try:
                    margin = int(margin)
                    if margin > 50:
                        components.ToastSnack(text='Margin should be 50mm or less.').open()
                        return
                except:
                    components.ToastSnack(text='margin should be a number.').open()
                    return

        # All good. Let's get the file name.
        self.file_name_popup.open()

    # Create the PDF
    def create_pdf(self, file_name, *args):
        self.file_name_popup.dismiss()  # Close the popup.

        # Progress Indicator
        self.progress_pop.open()
        self.progress_pop.content_cls.ids.progress.start()

        quality = self.pdf_quality ; size = self.pdf_size ; orientation = self.orientation
        margins = [self.ids.left_margin_field.text, self.ids.top_margin_field.text, self.ids.right_margin_field.text]
        header_text = self.ids.header_text_field.text
        footer_text = self.ids.footer_text_field.text
        page_numbering = self.page_numbering

        settings = [margins, size, orientation, quality, header_text, page_numbering, footer_text]
        output_folder = MDApp.get_running_app().android_user_path

        self.output_file = functions.create_pdf(self, self.selection_list, output_folder, file_name, settings)   # Create the PDF
        self.progress_pop.dismiss()
        if self.output_file:
            self.success_msg.open()
        else:
            self.err_msg.open()

    # Initiate threads
    def start(self, *args):
        file_name = self.file_name_popup.content_cls.ids.file_name_input.text
        if file_name:
            validity = functions.filter_filename(file_name)
            if validity:
                main_thread = threading.Thread(target=self.create_pdf, args=[file_name])
                main_thread.start()
            else:
                components.ToastSnack(text='Invalid file name...').open()

    def open_file(self, *args):  # Try to open created pdf.
        try:
            print('Opening File')
            os.startfile(os.path.abspath(self.output_file))
        except:
            pass


class MergePdfScreen(Screen):
    selection_list = DictProperty()
    file_name = StringProperty('merged')

    def __init__(self, **kwargs):
        super(MergePdfScreen, self).__init__(**kwargs)
        self.progress_pop = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.ProgressContent(),
        )
        self.file_name_popup = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.GetFileNameContent(),
            buttons=[
                MDFlatButton(text='Close', on_release=self.close_filename_popup),
                MDFlatButton(text='Create PDF', on_release=self.start),
            ])
        self.success_msg = components.ToastSnack(
            text='PDF created successfully...',
            buttons=[
                MDFlatButton(text='[color=#ffffff][size=20]open', on_release=self.open_file),
            ],
            duration=7,
        )
        self.err_msg = components.ToastSnack(text='Error when creating pdf...')

    def start_progress(self, *args):
        self.progress_pop.content_cls.ids.progress.start()
        self.progress_pop.open()

    def close_progress(self, *args):
        time.sleep(0.5)
        self.progress_pop.content_cls.ids.progress.stop()
        self.progress_pop.dismiss()

    def merge_pdf_popup(self):
        functions.file_chooser_popup(self, 'multi', ['.pdf'], self.selected)
        MDApp.get_running_app().file_manager_open = True

    # Exit from file manager
    def exit_manager(self, *args):
        self.file_chooser.close()  # file_chooser is in functions.py
        MDApp.get_running_app().file_manager_open = False

    # Filter the User Selected files and take only PDF files.
    def selected(self, *args):
        self.file_chooser.close()  # this _popup is in functions.py
        MDApp.get_running_app().file_manager_open = False

        for file in self.file_chooser.selection:
            # get an unique id for widget.
            pdf_id = functions.get_unique_id(self.selection_list)
            valid_extensions = ['.pdf']  # Allowed file Extensions
            file_ext = os.path.splitext(file)[1]

            # Validate the selected files.
            if file_ext in valid_extensions:
                self.selection_list[pdf_id] = file
                # Get the file size.
                file_size = functions.get_file_size(file, 'MB')
                # Add the image widget to the preview pane.
                pdf_widget = components.MergePdfWidget(file, file_size, pdf_id, self.selection_list)
                self.ids.merge_pdf_preview_pane.add_widget(pdf_widget)

    # Will be automatically called whenever the <SELECTION_LIST> list property changes.
    def on_selection_list(self, *args):
        # print('PDF list updated !! \n ')
        pdf_count_title = functions.update_counter_title(self.selection_list, 'File', 'Files')
        self.ids.merge_pdf_bottom_bar.title = pdf_count_title
        # print(len(self.selection_list), ' items exists !!')

    def clear_selection_completely(self):
        self.ids.merge_pdf_preview_pane.clear_widgets()
        self.selection_list.clear()

    # Get the File Name from User
    def get_file_name(self):
        # Check if all the necessary files are added or not.
        if not len(self.selection_list.keys()) >= 2:
            components.ToastSnack(text='There is nothing here to merge').open()
            return

        self.file_name_popup.open()

    # Closing the File Name Popup
    def close_filename_popup(self, *args):
        self.file_name_popup.dismiss()

    # Merging the pdf files with the valid pdf files
    def merge_pdf_files(self, *args):
        self.file_name_popup.dismiss()  # Close the popup.
        self.start_progress()  # progress Indicator
        output_file_name = self.file_name_popup.content_cls.ids.file_name_input.text
        output_folder = MDApp.get_running_app().android_user_path

        self.output_file = functions.merge_pdf_files(self, self.selection_list, output_folder, output_file_name)
        self.close_progress()

        if self.output_file:
            self.success_msg.open()
        else:
            self.err_msg.open()

    def close_popup_dialog(self, *args):
        self.dialog.dismiss()

    # Initiate threads.
    def start(self, *args):
        file_name = self.file_name_popup.content_cls.ids.file_name_input.text
        if file_name:
            validity = functions.filter_filename(file_name)
            if validity:
                main_thread = threading.Thread(target=self.merge_pdf_files, args=[file_name])
                main_thread.start()
            else:
                components.ToastSnack(text='Invalid file name...').open()

    def open_file(self, *args):  # Try to open created pdf.
        try:
            os.startfile(os.path.abspath(self.output_file))
        except:
            pass


class WatermarkScreen(Screen):
    file = DictProperty()
    file_name = StringProperty("watermarked")
    watermark_source = DictProperty()

    def __init__(self, **kwargs):
        super(WatermarkScreen, self).__init__(**kwargs)
        self.progress_pop = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.ProgressContent(),
        )
        self.file_name_popup = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.GetFileNameContent(),
            buttons=[
                MDFlatButton(text='Close', on_release=self.close_filename_popup),
                MDFlatButton(text='Create PDF', on_release=self.start),
            ])
        self.success_msg = components.ToastSnack(
            text='PDF created successfully...',
            buttons=[
                MDFlatButton(text='[color=#ffffff][size=20]open', on_release=self.open_file),
            ],
            duration=7,
        )
        self.err_msg = components.ToastSnack(text='Error when creating pdf...')

    def start_progress(self, *args):
        self.progress_pop.content_cls.ids.progress.start()
        self.progress_pop.open()

    def close_progress(self, *args):
        time.sleep(0.5)
        self.progress_pop.content_cls.ids.progress.stop()
        self.progress_pop.dismiss()

    def select_pdf_to_watermark(self, *args):
        functions.file_chooser_popup(self, 'file', ['.pdf'], self.selected)
        MDApp.get_running_app().file_manager_open = True

    def exit_manager(self, *args):
        self.file_chooser.close()
        MDApp.get_running_app().file_manager_open = False

    def selected(self, selected_file, *args):
        self.file_chooser.close()  # close file_chooser
        MDApp.get_running_app().file_manager_open = False

        """
        There is only one key used everywhere in this Dictionary
        Because only one file is allowed in this Dictionary.
        """
        self.file['key'] = os.path.abspath(selected_file)  # Set the ObjectProperty value

        self.ids.watermark_pdf_preview.clear_widgets()  # Clear the area every time before adding new widget by user.
        self.ids.watermark_pdf_preview.add_widget(
            components.SingleItemWidget(self.file, 'file-pdf-outline'))

    def select_watermark_source(self, extensions, *args):
        self.source_extensions = extensions
        functions.file_chooser_popup(self, 'file', extensions, self.add_source_widget)
        MDApp.get_running_app().file_manager_open = True

    def add_source_widget(self, selected_file, *args):
        self.file_chooser.close()  # file_chooser is in functions.py
        MDApp.get_running_app().file_manager_open = False

        self.watermark_source['key'] = os.path.abspath(selected_file)
        self.ids.watermark_source.clear_widgets()

        # Choose icon according to the file
        custom_icon = 'image-outline'
        source_ext = os.path.splitext(selected_file)[1]
        if source_ext == '.pdf':
            custom_icon = 'file-pdf-outline'
            # Activate page no selection layout also
            self.ids.page_no_layout.disabled = False

        # if selected file is an image Disable the page_no area
        if source_ext != '.pdf':
            self.ids.page_no_layout.disabled = True
            self.ids.page_no_field.text = ''  # Clear the inout field

        self.ids.watermark_source.add_widget(components.SingleItemWidget(self.watermark_source, custom_icon))

    def get_file_name(self, *args):
        # Check if all the assets are ready or not
        if 'key' not in self.file.keys():
            components.ToastSnack(text='Please select a pdf file.').open()
            return

        if 'key' not in self.watermark_source.keys():
            components.ToastSnack(text='Please select a watermark source.').open()
            return

        # Everything is ready. Lets take file name from user.
        self.file_name_popup.open()

    def close_filename_popup(self, *args):
        self.file_name_popup.dismiss()

    def add_watermark(self, file_name, *args):
        self.file_name_popup.dismiss()
        self.start_progress()

        orig_file_delete = self.ids.delete_orig_file.ids.orig_file_delete.state  # Accessing more levels deep.
        source_page_no = self.ids.page_no_field.text
        if source_page_no:
            try:
                source_page_no = int(float(source_page_no))
            except:
                source_page_no = 1
        else:
            source_page_no = 1
        settings = [orig_file_delete, file_name, source_page_no]
        output_folder = MDApp.get_running_app().android_user_path

        self.output_file = functions.add_watermark(self, self.file, self.watermark_source, output_folder, settings)
        print(self.output_file)
        self.close_progress()

        if self.output_file:
            self.success_msg.open()
        else:
            self.err_msg.open()

    def start(self, *args):
        file_name = self.file_name_popup.content_cls.ids.file_name_input.text
        if file_name:
            validity = functions.filter_filename(file_name)
            if validity:
                main_thread = threading.Thread(target=self.add_watermark, args=[file_name])
                main_thread.start()
            else:
                components.ToastSnack(text='Invalid file name...').open()

    def open_file(self, *args):  # Try to open created pdf.
        try:
            print('Opening File')
            os.startfile(os.path.abspath(self.output_file))
        except:
            pass


class SecurePdfScreen(Screen):
    pdf_file = DictProperty()
    del_orig_file = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SecurePdfScreen, self).__init__(**kwargs)
        self.progress_pop = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.ProgressContent(),
        )
        self.file_name_popup = MDDialog(
            type='custom',
            auto_dismiss=False,
            content_cls=components.GetFileNameContent(),
            buttons=[
                MDFlatButton(text='Close', on_release=self.close_filename_popup),
                MDFlatButton(text='Create PDF', on_release=self.start),
            ])
        self.success_msg = components.ToastSnack(
            text='PDF created successfully...',
            buttons=[
                MDFlatButton(text='[color=#ffffff][size=20]open', on_release=self.open_file),
            ],
            duration=7,
        )
        self.err_msg = components.ToastSnack(text='Error when creating pdf...')

    def start_progress(self, *args):
        self.progress_pop.content_cls.ids.progress.start()
        self.progress_pop.open()

    def close_progress(self, *args):
        time.sleep(0.5)
        self.progress_pop.content_cls.ids.progress.stop()
        self.progress_pop.dismiss()

    def open_manager(self, *args):
        functions.file_chooser_popup(self, 'file', ['.pdf'], self.selected)
        MDApp.get_running_app().file_manager_open = True

    def exit_manager(self, *args):
        self.file_chooser.close()
        MDApp.get_running_app().file_manager_open = False

    def selected(self, selected_file, *args):
        self.file_chooser.close()  # close file_chooser
        MDApp.get_running_app().file_manager_open = False

        """
        There is only one key used everywhere in this Dictionary
        Because only one file is allowed in this Dictionary.
        """
        self.pdf_file['key'] = os.path.abspath(selected_file)  # Set the ObjectProperty value

        self.ids.secure_pdf_preview_pane.clear_widgets()  # Clear the area every time before adding new widget by user.
        self.ids.secure_pdf_preview_pane.add_widget(
            components.SingleItemWidget(self.pdf_file, 'file-pdf-outline'))

    def get_file_name(self, *args):
        # Check if all the necessory components are ready or not.
        if 'key' not in self.pdf_file.keys():
            components.ToastSnack(text='Please select a pdf file').open()
            return
        if not self.ids.passwd_field.text:
            components.ToastSnack(text='Password is required...').open()
            return 

        # Everything is ready. Let's take file name
        self.file_name_popup.open()

    def close_filename_popup(self, *args):
        self.file_name_popup.dismiss()

    # Useless method. only for checking
    def delete_orig_file(self, checkbox, value, *args):
        if value:
            self.del_orig_file = True
        else:
            self.del_orig_file = False

    def secure_pdf(self, file_name, *args):
        self.file_name_popup.dismiss()
        self.start_progress()
        
        password = self.ids.passwd_field.text
        output_folder = MDApp.get_running_app().android_user_path
        self.output_file = functions.secure_pdf(self, password, self.pdf_file, file_name, output_folder, self.del_orig_file)
        self.close_progress()

        if self.output_file:
            self.success_msg.open()
        else:
            self.err_msg.open()

    def toggle_password_field(self, checkbox, value, *args):
        # Toggle show and hide password.
        if value:
            self.ids.passwd_field.password = False
        else:
            self.ids.passwd_field.password = True

    def start(self, *args):
        file_name = self.file_name_popup.content_cls.ids.file_name_input.text
        if file_name:
            validity = functions.filter_filename(file_name)
            if validity:   # Create and Initiate threads only if filename is valid.
                main_thread = threading.Thread(target=self.secure_pdf, args=[file_name])
                main_thread.start()
            else:
                components.ToastSnack(text='Invalid file name...').open()

    def open_file(self, *args):  # Try to open created pdf.
        try:
            print('Opening File')
            os.startfile(os.path.abspath(self.output_file))
        except:
            pass


class PdfMaster(MDApp):
    title = 'PDF Master'

    """
    Whenever you open or close file manager in any screen, you should update
    this property to prevent weired behaviour of file manager.
    """
    file_manager_open = BooleanProperty(False)

    """
    This path will be used to create the app folder and to save all the 
    output files.
    """
    android_user_path = StringProperty('')

    def __init__(self, **kwargs):
        super(PdfMaster, self).__init__(**kwargs)
        self.icon = 'assets/icon.png'
        Window.bind(on_keyboard=self.on_keypress)    # Handle key press
        self.screen = ScreenManager()
        self.exit_app_dialog = MDDialog(
            text='EXIT APP ?',
            auto_dismiss=False,
            size_hint=(0.6, 0.6),
            buttons=[
                    MDFlatButton(text="CANCEL", theme_text_color='Custom', text_color=(0, 170/255, 1, 1),
                        on_release = self.close_popup),
                    MDFlatButton(text="EXIT", theme_text_color='Custom', text_color=(0, 170/255, 1, 1),
                        on_release = self.stop),
                    ],
        )
        self.android_user_path = self.prepare_location()

    def close_popup(self, *args):
        self.exit_app_dialog.dismiss()

    def prepare_location(self, *args):
        default_path = '/storage/emulated/0/'

        if os.path.exists(default_path) and platform=='android':
            try:
                os.mkdir(default_path + 'PDF Master')
                self.android_user_path = '/storage/emulated/0/PDF Master/'
            except FileExistsError:
                print('Folder already exists')
                self.android_user_path = '/storage/emulated/0/PDF Master/'
            except:
                self.android_user_path = '/'
        elif platform == 'win':
            self.android_user_path = 'C:/Users/Sahan/Desktop/App Files/'
        elif platform == 'linux':
            self.android_user_path = ''
        return self.android_user_path

    # Controlling back button behaviour
    def on_keypress(self, window, key, current_screen='home_screen', *args):
        if key == 27: # ESC key
            if self.screen.current == 'home_screen' and not self.file_manager_open:   # Try to exit.
                self.exit_app_dialog.open()
                return True
            elif not self.file_manager_open:   # Try to go Home.
                self.screen.transition.direction = 'right'
                self.screen.current = 'home_screen'
                return True
            elif self.file_manager_open:  # Go 1 level back from File manager.
                try:
                    self.screen.current_screen.file_chooser.back()
                except:
                    pass
                return True
            else:  # Just stay on app.
                return True

    def on_pause(self):
        return True

    def build(self):
        # self.theme_cls.primary_palette = 'Blue'     
        # self.theme_cls.primary_hue = 'A700'
        # self.theme_cls.theme_style = 'Dark'
        self.screen.add_widget(HomeScreen(name='home_screen'))
        self.screen.add_widget(ImgToPdfScreen(name='img_to_pdf_screen'))
        self.screen.add_widget(MergePdfScreen(name='merge_pdf_screen'))
        self.screen.add_widget(WatermarkScreen(name='watermark_screen'))
        self.screen.add_widget(SecurePdfScreen(name='secure_pdf_screen'))
        return self.screen


if __name__ == "__main__":
    PdfMaster().run()
