import collections
from tkinter import *
import tkinter.font as tkfont

import yamliny
import threading
from pprint import pprint

from PIL import GifImagePlugin, Image, ImageTk


class Label(Label):
    def text(self, new_text=None):
        if new_text:
            self['text'] = new_text
        return self['text']


class Button(Button):
    def on_click(self, cmd=None):
        if cmd is not None:
            self['command'] = cmd

    def text(self, new_text=None):
        if new_text:
            self['text'] = new_text
        return self['text']


class AutoLayoutGif():
    def __init__(self, tkinter_root, **args):
        image_url = args['image-url']
        self.container = None
        self.play_state = 1
        if tkinter_root:
            self.tk_root = tkinter_root
        self.image_object = Image.open(image_url)
        w, h = self.image_object.size
        self.natural_aspect_ratio = w / h
        self.frames = []
        self.supports_animation = getattr(self.image_object, "is_animated", False)
        self.arg_params = args
        if self.supports_animation:
            self.frame_count = self.image_object.n_frames
            try:
                self.speed = int(args['speed'])
            except:
                self.speed = 1

    def e_size(self):
        e_height = 0
        e_width = 0
        if 'width' in self.arg_params and 'height' in self.arg_params:
            print('Letterbox mode')
            placed_aspect_ratio = float(self.arg_params['width']) / float(self.arg_params['height'])
            if placed_aspect_ratio < self.natural_aspect_ratio:
                e_width = self.arg_params['width']
                e_height = float(self.arg_params['width']) / self.natural_aspect_ratio
            elif placed_aspect_ratio >= self.natural_aspect_ratio:
                e_width = float(self.arg_params['height']) * self.natural_aspect_ratio
                e_height = self.arg_params['height']
        elif 'with' in self.arg_params:
            print('Width specified mode')
            e_width = self.arg_params['width']
            e_height = float(e_width) / self.natural_aspect_ratio
        elif 'height' in self.arg_params:
            print('Height specified mode')
            e_height = self.arg_params['height'] if 'height' in self.arg_params else self.arg_params['default-height']
            e_width = float(e_height) * self.natural_aspect_ratio
        elif 'default-width' in self.arg_params:
            print('Nothing specified; default width mode')
            e_width = self.arg_params['default-width']
            e_height = float(e_width) / self.natural_aspect_ratio
        elif 'default-height' in self.arg_params:
            print('Nothing specified; default height mode')
            e_height = self.arg_params['default-height']
            e_width = float(e_height) * self.natural_aspect_ratio
        else:
            ValueError('AutoLayout couldn\'t find any width or height or fallback width/height to place an image.')
        return {'height': e_height, 'width': e_width}

    def place(self, **args):
        element_size = self.e_size()
        placed_width = element_size['width']
        placed_height = element_size['height']
        if self.supports_animation:
            for frame in range(0, self.frame_count):
                self.image_object.seek(frame)
                resized_frame = self.image_object.resize((int(placed_width), int(placed_height)))
                self.frames.append(ImageTk.PhotoImage(resized_frame))
                initial_img = self.frames[0]
        else:
            resized_frame = self.image_object.resize((int(placed_width), int(placed_height)))
            initial_img = ImageTk.PhotoImage(resized_frame)
        self.container = Label(self.tk_root, image=initial_img)
        self.container.photo = initial_img
        self.container.place(x=args['x'], y=args['y'], width=placed_width, height=placed_height)
        if self.supports_animation:
            self.invoke_animation(self.speed)

    def invoke_animation(self, gif_speed):
        def update(current_frame=0):
            if self.play_state == 1:
                if current_frame + 1 < self.frame_count:
                    current_frame += 1
                else:
                    current_frame = 0
                self.container.configure(image=self.frames[current_frame])
                self.container.photo = self.frames[current_frame]
            self.tk_root.after(int(100 / gif_speed) + 1, lambda: update(current_frame))

        update()

    def pause(self):
        self.play_state = 0

    def play(self):
        self.play_state = 1


# Subclass which allows for functions to be applied to multiple elements without having to manually iterate
class ElemCollection(list):
    def __getattr__(self, name):
        def wrapper(*args):
            methods_to_run = []
            for elem in self:
                if hasattr(elem, name):
                    if callable(getattr(elem, name)):
                        methods_to_run.append(getattr(elem, name))
            return [method(args) for method in methods_to_run]

        return wrapper


def clean_inline_yaml(inline_yaml):
    yaml_in_progress = inline_yaml

    # Begin by stripping lead/trail whitespace
    lines = yaml_in_progress.split("\n")
    lines = list(filter(None, lines))

    # Capture indentation depth
    indent_depth = 0
    for i, char in enumerate(lines[0]):
        if char in ' \t':
            indent_depth = i + 1
        else:
            break

    indent_stripped_lines = []
    for line in lines:
        indent_stripped_lines.append(line[indent_depth:])

    yaml_in_progress = "\n".join(indent_stripped_lines)

    cleaned_yaml = yaml_in_progress
    return cleaned_yaml


presentation_defaults = '''
        window:
          layout-mode: auto
          width: 300
          margin-left: 20
          margin-top: 20
          margin-right: 20
          margin-bottom: 20
        
        header:
          font-family: SFPro
          font-size: 22
          font-weight: bold
          foreground-color: black
          background-color: None
          margin-top: 5
          margin-bottom: 5
          margin-left: 5
          margin-right: 5
          width: 150
        
        image:
          margin-top: 5
          margin-bottom: 5
          margin-left: 5
          margin-right: 5
          default-width: 150
          speed: 2
        
        button:
          height: 28
          width: 100
          font-family: SFPro
          font-size: 13
          font-weight: normal
          foreground-color: None
          background-color: None
          margin-top: 5
          margin-bottom: 25
          margin-left: 0
          margin-right: 0
'''


class AutoLayoutWindow:
    def __init__(self, interface='interface.yaml', presentation='presentation.yaml', title='Untitled', during=print):
        if isinstance(interface, collections.Mapping):
            self.interface_obj = interface
        elif isinstance(interface, str):
            if interface[len(interface) - 5:len(interface)] == '.yaml':
                with open(interface, 'r') as f:
                    interface_text = f.read()
                self.interface_obj = yamliny.loads(interface_text.strip())
            else:
                self.interface_obj = yamliny.loads(clean_inline_yaml(interface))
        else:
            ValueError('Failed to identify an interface YAML file or dict passed to interface argument.')

        if isinstance(presentation, collections.Mapping):
            self.presentation_obj = presentation
        elif isinstance(presentation, str):
            if presentation[len(presentation) - 5:len(presentation)] == '.yaml':
                with open(presentation, 'r') as f:
                    presentation_text = f.read()
                self.presentation_obj = yamliny.loads(presentation_text.strip())
            else:
                self.presentation_obj = yamliny.loads(clean_inline_yaml(presentation))
        else:
            ValueError('Failed to identify an presentation YAML file or dict passed to presentation argument.')

        # Default stylesheet
        self.presentation_defaults_obj = yamliny.loads(clean_inline_yaml(presentation_defaults))

        # Set up cursor dictionary

        self.window_style = self._get_styles_by_elem('window')
        self.cursor = {'x': int(self.window_style['margin-left']), 'y': int(self.window_style['margin-top'])}
        self.auto_layout = False
        if self.window_style['layout-mode'] == 'auto':
            self.auto_layout = True

        # Widget dictionary. Used for selecting widgets after window has been created.
        self.element_name_dictionary = {}
        self.element_set_dictionary = {}
        self.element_kind_dictionary = {}

        self.root = Tk()
        self.root.title(title)

        # self.cursor
        content_height = int(self.window_style['margin-top']) + int(self.window_style['margin-bottom'])
        content_width = 0

        if self.auto_layout:
            content_width = int(self.window_style['width'])
            content_height = int(self.window_style['height']) if 'height' in self.window_style else content_height

        for line in self.interface_obj.values():
            # Initiate variables to capture line-level style attributes
            line_height = 0
            line_width = int(self.window_style['margin-left']) + int(self.window_style['margin-right'])

            auto_layout_scale_factor = self._get_line_scale_factor(line.items(), content_width)

            for element_name, element_data in line.items():
                elem_box = self._render(element_name, element_data, auto_layout_scale_factor)
                line_height = max([elem_box['height'], line_height])
                line_width += elem_box['width']

            self._cursor_carriage_return(line_height)
            content_height += line_height
            if not self.auto_layout:
                content_width = max([line_width, content_width])

        self.root.geometry(f'{int(content_width)}x{int(content_height)}')

        self.root.after(0, lambda: during(self))
        self.root.mainloop()

    # Cursor functions

    def _cursor(self, elem_dimensions, styles):
        if 'margin-top' in styles:
            self.cursor['y'] += int(styles['margin-top'])
        if 'margin-left' in styles:
            self.cursor['x'] += int(styles['margin-left'])

        # The top,left position to draw the new element from
        old_cursor = dict(self.cursor)

        # Move in to position for the next element: reset margin top, and shift right for margin right and width
        if 'margin-right' in styles:
            self.cursor['x'] += int(styles['margin-right'])
        self.cursor['x'] += int(elem_dimensions['width'])
        if 'margin-top' in styles:
            self.cursor['y'] += int(styles['margin-top'])
        return old_cursor

    def _cursor_carriage_return(self, line_height):
        self.cursor['y'] += line_height
        self.cursor['x'] = int(self.window_style['margin-left'])

    # Private methods (General)

    # Private methods (cascading styles)

    def _get_styles_by_elem(self, kind, style_obj={}):
        new_style_obj = style_obj
        # Apply defaults initially (this provides a quickstart stylesheet and allows style attributes to be optional without causing key errors)
        for p_obj in [self.presentation_defaults_obj, self.presentation_obj]:
            if kind in p_obj:
                style_attributes = p_obj[kind]
                for attribute_name, attribute_value in style_attributes.items():
                    new_style_obj[attribute_name] = attribute_value
        return new_style_obj

    def _get_styles_by_set(self, set_name, style_obj):
        new_style_obj = style_obj
        if set_name in self.presentation_obj:
            style_attributes = self.presentation_obj[set_name]
            for attribute_name, attribute_value in style_attributes.items():
                new_style_obj[attribute_name] = attribute_value
        return new_style_obj

    def _get_styles_by_name(self, name_name, style_obj):
        new_style_obj = style_obj
        if name_name in self.presentation_obj:
            style_attributes = self.presentation_obj[name_name]
            for attribute_name, attribute_value in style_attributes.items():
                new_style_obj[attribute_name] = attribute_value
        return new_style_obj

    def _get_styles_from_inline(self, inline_styles, style_obj):
        new_style_obj = style_obj
        for attribute_name, attribute_value in inline_styles.items():
            new_style_obj[attribute_name] = attribute_value
        return new_style_obj

    def _get_styles(self, kind, elem, auto_layout_sf=1):
        style = {}
        style = self._get_styles_by_elem(kind, style)
        if 'set' in elem:
            for set_name in elem['set'].split(' '):
                style = self._get_styles_by_set(set_name, style)
        if 'name' in elem:
            style = self._get_styles_by_name(elem['name'], style)
        if 'presentation' in elem:
            style = self._get_styles_from_inline(elem['presentation'], style)
        if 'width' not in style and kind == 'image':
            style['image-url'] = elem['presentation']['image-url']
            print('_get_styles is calculating aspect ratio')
            tmp_img = AutoLayoutGif(None, **style)
            style['width'] = tmp_img.e_size()['width']
        style['width'] = float(style['width']) * auto_layout_sf
        return style

    def _styles_to_arguments(self, styles):
        # Construct the tkinter arguments (kwag) from the style object
        for attr, val in styles.items():
            styles[attr] = val = None if val == 'None' else val
        kwag = {}
        if 'fg' in styles:
            kwag['fg'] = styles['foreground-color']
        if 'bg' in styles:
            kwag['bg'] = styles['background-color']
        if 'font-family' in styles:  # Text mode
            kwag['font'] = tkfont.Font(self.root, family=styles['font-family'], size=styles['font-size'],
                                       weight=styles['font-weight'])
        return kwag

    # Private methods (element rendering)

    def _render(self, elem_name, elem, auto_layout_sf):
        render_groups = {
            'header': self._render_text,
            'button': self._render_button,
            'image': self._render_image
        }
        elem['name'] = elem_name
        return render_groups[elem['kind']](elem['kind'], elem, auto_layout_sf)

    def _render_text(self, elem_kind, elem, auto_layout_sf):
        styles = self._get_styles(elem_kind, elem, auto_layout_sf)
        kwag = self._styles_to_arguments(styles)
        kwag['text'] = elem['text']
        kwag['anchor'] = 'nw'
        kwag['wraplength'] = styles['width']
        self.element_name_dictionary[elem['name']] = Label(self.root, **kwag)
        self._index_element(self.element_name_dictionary[elem['name']], elem)
        elem_size = {
            'height': int(kwag['font'].metrics('linespace') * 1.1 + 3),
            'width': int(styles['width'])
        }
        line_length = kwag['font'].measure(kwag['text'])
        number_of_lines = line_length / elem_size['width']
        number_of_lines = int(number_of_lines) + (number_of_lines % 1 > 0)  # Round up
        elem_size['height'] *= number_of_lines
        outer_dimensions = {
            'height': int(styles['margin-top']) + elem_size['height'] + int(styles['margin-bottom']),
            'width': int(styles['margin-left']) + elem_size['width'] + int(styles['margin-right'])
        }
        self.element_name_dictionary[elem['name']].place(**self._cursor(elem_dimensions=elem_size, styles=styles),
                                                         height=elem_size['height'], width=elem_size['width'])
        return outer_dimensions  # Line height

    def _render_button(self, elem_kind, elem, auto_layout_sf):
        styles = self._get_styles(elem_kind, elem, auto_layout_sf)
        kwag = self._styles_to_arguments(styles)
        kwag['text'] = elem['text']
        self.element_name_dictionary[elem['name']] = Button(self.root, **kwag)
        self._index_element(self.element_name_dictionary[elem['name']], elem)
        elem_size = {
            'height': int(styles['height']),
            'width': int(styles['width'])
        }
        line_length = kwag['font'].measure(kwag['text'])
        elem_size['width'] = line_length
        outer_dimensions = {
            'height': int(styles['margin-top']) + elem_size['height'] + int(styles['margin-bottom']),
            'width': int(styles['margin-left']) + elem_size['width'] + int(styles['margin-right'])
        }
        self.element_name_dictionary[elem['name']].place(**self._cursor(elem_dimensions=elem_size, styles=styles),
                                                         height=elem_size['height'], width=None)
        return outer_dimensions  # Line height

    def _render_image(self, elem_kind, elem, auto_layout_sf):
        styles = self._get_styles(elem_kind, elem, auto_layout_sf)
        #  Pass styles directly, as this is an AutoLayoutWindow subclass, not stock-tkinter
        self.element_name_dictionary[elem['name']] = AutoLayoutGif(self.root, **styles)
        self._index_element(self.element_name_dictionary[elem['name']], elem)
        elem_size = self.element_name_dictionary[elem['name']].e_size()  # Images can use automatic sizing based on
        outer_dimensions = {                                             # natural aspect ratio
            'height': int(styles['margin-top']) + int(elem_size['height']) + int(styles['margin-bottom']),
            'width': int(styles['margin-left']) + int(elem_size['width']) + int(styles['margin-right'])
        }
        self.element_name_dictionary[elem['name']].place(**self._cursor(elem_dimensions=elem_size, styles=styles),
                                                         height=elem_size['height'], width=elem_size['width'])
        return outer_dimensions  # Line height

    # Private methods (to support element rendering)

    def _get_line_scale_factor(self, line_items, content_width):
        if self.auto_layout:
            margin_space = int(self.window_style['margin-left']) + int(self.window_style['margin-right'])
            unscaled_inner_width = 0
            for element_name, element_data in line_items:
                element_data['name'] = element_name
                styles = self._get_styles(element_data['kind'], element_data)
                margin_space += int(styles['margin-left']) + int(styles['margin-right'])
                unscaled_inner_width += int(styles['width'])
            inner_width = content_width - margin_space
            scale_factor = inner_width / unscaled_inner_width
            return scale_factor
        else:
            return 1

    def _index_element(self, elem, meta):
        if 'kind' in meta:
            kind = meta['kind']
            elems_list = self.element_kind_dictionary.setdefault(kind, [])
            elems_list.append(elem)
        if 'set' in meta:
            set = meta['set']
            self.element_set_dictionary[set] = elem

    # Public methods (DOM access)

    def get_elem_by_name(self, name):
        return self.element_name_dictionary[name]

    def get_elems_by_set(self, set):
        return self.element_set_dictionary[set]

    def get_elems_by_kind(self, kind):
        return ElemCollection(self.element_kind_dictionary[kind])

    def get_elems_by_line(self, line):
        lines = self.interface_obj
        elem_collection = ElemCollection()
        if line in lines:
            elems = [self.get_elem_by_name(name) for name in lines[line].keys()]
            elem_collection = ElemCollection(elems)
        return elem_collection

    # Public methods (DOM manipulation)

    def after(self, delay, func):
        self.root.after(delay, func)
