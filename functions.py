from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
from kivymd.uix.filemanager import MDFileManager
import time
import os
import random
from fpdf import FPDF
import components


def get_file_size(file, metric='auto'):
    file = os.path.abspath(file)
    file_size = os.stat(file).st_size

    if metric == 'auto':
        if file_size / 1024 < 1024:
            file_size = '{:.2f}'.format(file_size / 1024)
            file_size = str(file_size) + 'KB'
        elif file_size / 1024 >= 1024:
            file_size = '{:.2f}'.format(file_size / (1024 * 1024))
            file_size = str(file_size) + 'MB'
        elif file_size / 1024 >= 1024 * 1024:
            file_size = '{:.2f}'.format(file_size / (1024 * 1024 * 1024))
            file_size = str(file_size) + 'GB'
        else:
            file_size = 'N/A'
    elif metric == 'KB':
        file_size = '{:.2f}'.format(file_size / 1024)
        file_size = str(file_size) + 'KB'
    elif metric == 'MB':
        file_size = '{:.2f}'.format(file_size / (1024 * 1024))
        file_size = str(file_size) + 'MB'
    elif metric == 'GB':
        file_size = '{:.2f}'.format(file_size / (1024 * 1024 * 1024))
        file_size = str(file_size) + 'GB'
    else:
        file_size = 'N/A'
    return file_size


def file_chooser_popup(self, selector, extensions, callback_method):
    self.file_chooser = MDFileManager(
        select_path=callback_method,
        selector=selector,
        exit_manager=self.exit_manager,
        ext=extensions,
    )
    try:
        if os.path.exists('/storage/emulated/0/'):
            self.file_chooser.show('/storage/emulated/0/')
            print('no emulated')
        else:
            self.file_chooser.show('/')
            print('Opening alternative location')
    except:
        components.ToastSnack(text="Sorry, couldn't open file manager", duration=2).open()


# Used for getting an unique id for all the widgets added to preview pane.
def get_unique_id(selection_list):
    if len(selection_list) > 0:
        page_no = len(selection_list) + 1
    else:
        page_no = 1

    # If page_no already exists in the dictionary as a key, get the highest key value,
    # and increase it by 1.
    if page_no in selection_list:
        all_keys = list(selection_list.keys())
        max_key = max(all_keys)
        page_no = max_key + 1

    # If the key still present in the dictionary, return a warning to the user.
    if page_no in selection_list:
        print('Caution: Key is Duplicating')

    return page_no


# Used for returning the page count live preview to the bottom toolbar.
def update_counter_title(selection_list, final_string_for_single_item, final_string_for_multiple_items):
    available_items = len(selection_list)
    page_count_title = ''
    if available_items == 1:
        page_count_title = f"{available_items} {final_string_for_single_item}"
    elif available_items == 0:
        page_count_title = ""
    else:
        page_count_title = f"{available_items} {final_string_for_multiple_items}"

    return page_count_title


def get_unique_output(file_name, file_ext, output_location):
    """
    :param file_name: str : The name which taken by user.
    :param file_ext: str : The extension of output file should be (with dot(.))
    :param output_location: str : The location to save ouput file.
    :return: str : The complete path and file name of output file.
    """
    files_in_output = os.listdir(output_location)  # all the files in output location
    checking_item = f"{file_name}{file_ext}"
    if checking_item in files_in_output:
        extender = 1
        duplication = 1
        while duplication:
            checking_item = f"{file_name}({str(extender)}){file_ext}"
            extender += 1
            if checking_item not in files_in_output:
                duplication = 0
            if extender > 500:  # Taken too long time. Try something else.
                extender = random.randint(500, 9000)
    output = f"{output_location}/{checking_item}"
    return output


def filter_filename(file_name):
    reversed_chars = ["|", "\\", "?", "*", "<", "\"", "/", ":", ">", "'", '@',
                      '!', '=', '+', '[', ']', '{', '}', '~', '`', '%', '^']
    output = ''
    for char in file_name:
        if char in reversed_chars:
            return False
        else:
            continue
    return True


# ************************************************
# Main Processes
# ************************************************

class PMPdf(FPDF):
    def __init__(self, header_text, margins, image_width, page_numbering, footer_text, branding_font_size, **kwargs):
        super(PMPdf, self).__init__(**kwargs)
        self.header_text = header_text
        self.left_margin = margins[0]
        self.top_margin = margins[1]
        self.right_margin = margins[2]
        self.header_width = image_width
        self.page_numbering = page_numbering
        self.custom_font_size = branding_font_size
        self.footer_text = footer_text

    def header(self):
        self.set_font('Times', '', 30)
        # if header text present, go down and add cell.
        if self.header_text:
            self.set_y(self.top_margin)  # Go to bottom according to padding
            self.set_x(self.left_margin)  # Start from the image beginning.
            self.multi_cell(w=self.header_width, h=20, txt=self.header_text, border=0, fill=0, align='L')
        self.ln(20)  # Line break

    def footer(self, *args):
        # Go to 1.5 cm from bottom
        self.set_y(-12)
        self.set_x(self.left_margin)
        self.set_font(family='Times', style='', size=self.custom_font_size)
        self.cell(w=self.header_width / 3, h=10, txt=self.footer_text + ' ', border=0, ln=0, align='L', fill=False)

        # self.line(20, 280, 190, 280)
        if self.page_numbering:
            page_num = str(self.page_no())
        else:
            page_num = ' '
        self.cell(w=self.header_width / 3, h=10, txt=page_num + ' ', border=0, ln=0, align='C')

        # App Branding Link
        self.set_font(family='Times', style='', size=self.custom_font_size)
        self.cell(w=self.header_width / 3, h=10, txt='Created with:  PDF Master', border=0, ln=0, align='R', fill=False)


def create_pdf(instance, image_list, output_path, file_name, settings):
    """
    :param instance: self: refers to self which passed when calling function.
    :param image_list: list : The filtered images which selected by user.
    :param output_path: str : Output pdf saving path.
    :param file_name: str : Output File name.
    :param settings: list :
        [0] : list   : Page margins
            [0] : int : Left margin
            [1] : int : Top Margin
            [2] : int : Right Margin
        [1] : str    : size of pdf
        [2] : str    : Orientation
        [3] : int    : pdf quality level
            quality 1 : Normal
            quality 2 : Medium
            quality 3 : Low
        [4] : str    : Header text to add in header.
        [5] : bool   : Page numbering state.
        [6] : str   : Footer text to add in footer.
    :return:
    """

    # Start image x axis according to left margin.
    left_margin = starting_point_x = settings[0][0]
    if left_margin:
        left_margin = int(float(left_margin))
    if not left_margin:
        left_margin = 0

    # Start image y axis according to top margin.
    top_margin = starting_point_y = settings[0][1]
    if top_margin:
        top_margin = int(float(top_margin))
    if not top_margin:
        top_margin = 0

    right_margin = settings[0][2]
    if right_margin:
        right_margin = int(float(right_margin))
    if not right_margin:
        right_margin = 0

    # if format is A5, reduce the branding text size.
    font_size = 13
    if settings[1] == 'A5':
        font_size = 10

    # Width and height of image. (just declaration).
    # Further will be changed according to the paper sizes.
    width = float
    height = float

    # Header text. If it is given by user add it to the header.
    # if header text present, set header height to manage image height.
    header_text = settings[4]
    header_height = 0
    if header_text:
        header_height = 30

    # Footer text
    footer_text = settings[6]

    # file_list is a Dictionary
    keys = list(image_list.keys())

    # Page Numbering
    page_numbering = settings[5]

    page_width = float
    page_height = float

    # Set the image properly according to the margins.
    if settings[1] == 'A3':  # (297 × 420)
        if settings[2] == 'P':
            page_width = 297
            page_height = 420
        else:
            page_width = 420
            page_height = 297
        width = page_width - (left_margin + right_margin)
        height = page_height - (top_margin + 15 + header_height)
        starting_point_x, starting_point_y = left_margin, top_margin + header_height

    elif settings[1] == 'A4':  # (210 × 297)
        if settings[2] == 'P':
            page_width = 210
            page_height = 297
        else:
            page_width = 297
            page_height = 210
        width = page_width - (left_margin + right_margin)
        height = page_height - (top_margin + 15 + header_height)
        starting_point_x, starting_point_y = left_margin, top_margin + header_height

    elif settings[1] == 'A5':  # (148 × 210)
        if settings[2] == 'P':
            page_width = 148
            page_height = 210
        else:
            page_width = 210
            page_height = 148
        width = page_width - (left_margin + right_margin)
        height = page_height - (top_margin + 15 + header_height)
        starting_point_x, starting_point_y = left_margin, top_margin + header_height

    elif settings[1] == 'Letter':  # (215.9 * 279.4)
        if settings[2] == 'P':
            page_width = 215.9
            page_height = 279.4
        else:
            page_width = 279.4
            page_height = 215.9
        width = page_width - (left_margin + right_margin)
        height = page_height - (top_margin + 15 + header_height)
        starting_point_x, starting_point_y = left_margin, top_margin + header_height

    elif settings[1] == 'Legal':  # (215.9 * 355.6)
        if settings[2] == 'P':
            page_width = 215.9
            page_height = 355.6
        else:
            page_width = 355.6
            page_height = 215.9
        width = page_width - (left_margin + right_margin)
        height = page_height - (top_margin + 15 + header_height)
        starting_point_x, starting_point_y = left_margin, top_margin + header_height

    else:
        pass

    # Not necessary
    starting_point_x = round(starting_point_x)
    starting_point_y = round(starting_point_y)

    margins = [left_margin, top_margin, right_margin]

    # the PDF object.
    pdf = PMPdf(orientation=settings[2],
                unit='mm',
                format=settings[1],
                header_text=settings[4],  # Custom
                margins=margins,  # Custom
                image_width=width,  # Custom
                page_numbering=page_numbering,  # Custom
                footer_text=footer_text,  # Custom
                branding_font_size=font_size)  # Custom
    pdf.alias_nb_pages()  # get page numbers

    try:
        # Create the pages and add images to them.
        for key in keys:
            pdf.add_page()
            the_image = image_list[key]
            pdf.image(the_image, x=starting_point_x, y=starting_point_y, w=width, h=height)

        # Analyze the file output location and output pdf.
        try:
            os.makedirs(f'{output_path}Generated')
            output_path = output_path + 'Generated'
        except OSError as err:
            output_path = output_path + 'Generated'
            print(err)

        instance.pdf_file = get_unique_output(file_name, '.pdf', output_path)
        pdf.output(instance.pdf_file)  # output the pdf file.
        return instance.pdf_file

    except:
        return False


def merge_pdf_files(instance, pdf_list, output_path, file_name):
    merger = PdfFileMerger()
    keys = pdf_list.keys()

    try:
        for key in keys:
            single_pdf = pdf_list[key]
            merger.append(PdfFileReader(open(single_pdf, 'rb')))

        # Analyze the file output location and output pdf.
        try:
            os.makedirs(f'{output_path}Merged')
            output_path = output_path + 'Merged'
        except OSError as err:
            output_path = output_path + 'Merged'
            print(err)

        instance.output_pdf = get_unique_output(file_name, '.pdf', output_path)
        merger.write(instance.output_pdf)  # pdf output.
        return instance.output_pdf

    except:
        return False



def add_watermark(instance, pdf_dict, watermark_dict, output_path, settings):
    """
    :param instance:
    :param pdf_dict: dict : A dictionary of single pdf file.
    :param watermark_dict: dict : A dictionary of single image or pdf as watermark source
    :param output_path: str : The location of saving pdf
    :param settings:
        [0] : str : Delete original file checkbox state
        [1] : str : Output file name
        [2] : int : Pdf page no to be used as watermark source if user diven (default: 0)
    :return:
    """
    file = pdf_dict['key']  # the PDF file
    # Get file width and Height in mm (mediaBox returns in points)
    pdf = PdfFileReader(file)
    pdf_width = pdf.getPage(0).mediaBox[2] * 0.352778
    pdf_height = pdf.getPage(0).mediaBox[3] * 0.352778

    watermark_source = watermark_dict['key']  # The Watermark source file
    temp_source = ''

    # Check if watermark source is a pdf or an image. If it is an image,
    # first of all create a pdf with that image and use it as source.
    if not watermark_source.endswith('.pdf'):
        # Yes. it is an image
        pdf = FPDF()
        pdf.add_page()
        the_image = watermark_source
        pdf.image(the_image, x=0, y=0, w=pdf_width, h=pdf_height)

        # Save the created pdf temporarily in a 'custom' folder.
        try:
            os.makedirs(output_path + '/temp')
        except:
            pass

        pdf.output(output_path + '/temp/1.pdf')
        watermark_source = output_path + '/temp/1.pdf'
        temp_source = output_path + '/temp/1.pdf'

    # The watermark source
    watermark_obj = PdfFileReader(watermark_source)
    if watermark_obj.getNumPages() < settings[2]:
        print('Source pdf has no page: ', settings[2])
        return False

    print('Getting data:')
    print('page no: ', settings[2])
    print('No of pages: ', watermark_obj.getNumPages())
    watermark_page = watermark_obj.getPage(settings[2]-1)

    pdf_reader = PdfFileReader(file)
    pdf_writer = PdfFileWriter()

    for page in range(pdf_reader.getNumPages()):
        page = pdf_reader.getPage(page)
        page.mergePage(watermark_page)  # Add watermark page
        pdf_writer.addPage(page)

    try:
        os.makedirs(output_path + '/Watermarked')
        output_location = output_path + '/Watermarked'
    except:
        output_location = output_path + '/Watermarked'

    try:
        instance.output_pdf = get_unique_output(settings[1], '.pdf', output_location)
        with open(instance.output_pdf, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)

        # If user want to delete original file, just delete it.
        if settings[0] == 'down':
            os.remove(os.path.abspath(file))

        try:
            os.remove(temp_source)
        except:
            pass
        return instance.output_pdf
    except:
        return False


def secure_pdf(instance, password, pdf_file, output_file_name, output_path, orig_file_del):
    pdf = os.path.abspath(pdf_file['key'])  # File to add password

    # Analyze the file output location and output pdf.
    try:
        os.makedirs(output_path + '/Secured')
        output_location = output_path + '/Secured'
    except:
        output_location = output_path + '/Secured'

    pdf_writer = PdfFileWriter()
    pdf_reader = PdfFileReader(pdf)

    for page in range(pdf_reader.getNumPages()):
        pdf_writer.addPage(pdf_reader.getPage(page))

    pdf_writer.encrypt(user_pwd=password, owner_pwd=password, use_128bit=True)
    instance.output_pdf = get_unique_output(output_file_name, '.pdf', output_location)

    try:
        with open(instance.output_pdf, 'wb') as fo:
            pdf_writer.write(fo)

        # Check and delete original file if necessary.
        try:
            if orig_file_del:
                os.remove(pdf)
        except:
            pass
        return instance.output_pdf   # There it is. BOOM.
    except:
        return False
