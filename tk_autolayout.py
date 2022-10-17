import collections
from tkinter import *
import tkinter.font as tkfont
import yamliny
import threading
from pprint import pprint


class Label(Label):
    def text(self, new_text=None):
        if new_text:
            self['text'] = new_text
        return self['text']


class Button(Button):
    def on_click(self, cmd=None):
        if cmd is not None:
            self['command'] = cmd


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

    # Delete indent from each line
    # for line in yaml_in_progress
    print(indent_depth)

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
        
        button:
          height: 28
          width: 100
          font-family: SFPro
          font-size: 13
          font-weight: normal
          foreground-color: None
          background-color: None
          margin-top: 0
          margin-bottom: 0
          margin-left: 0
          margin-right: 0
'''

class AutoLayoutWindow:
    def __init__(self, interface='interface.yaml', presentation='presentation.yaml', title='Untitled', during=print):
        if isinstance(interface, collections.Mapping):
            print('Loading AutoLayoutWindow interface in inline dict mode.')
            self.interface_obj = interface
        elif isinstance(interface, str):
            if interface[len(interface) - 5:len(interface)] == '.yaml':
                print('Loading AutoLayoutWindow interface in YAML file mode.')
                with open(interface, 'r') as f:
                    interface_text = f.read()
                self.interface_obj = yamliny.loads(interface_text.strip())
            else:
                print('Loading AutoLayoutWindow interface in inline YAML mode.')
                self.interface_obj = yamliny.loads(clean_inline_yaml(interface))
        else:
            ValueError('Failed to identify an interface YAML file or dict passed to interface argument.')

        if isinstance(presentation, collections.Mapping):
            print('Loading AutoLayoutWindow presentation in inline dict mode.')
            self.presentation_obj = presentation
        elif isinstance(presentation, str):
            if presentation[len(presentation) - 5:len(presentation)] == '.yaml':
                print('Loading AutoLayoutWindow presentation in YAML file mode.')
                with open(presentation, 'r') as f:
                    presentation_text = f.read()
                self.presentation_obj = yamliny.loads(presentation_text.strip())
            else:
                print('Loading AutoLayoutWindow presentation in inline YAML mode.')
                self.presentation_obj = yamliny.loads(clean_inline_yaml(presentation))
        else:
            ValueError('Failed to identify an presentation YAML file or dict passed to presentation argument.')

        # Default stylesheet
        # Move to dict within .py file at some point
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

        self.root.geometry(f'{content_width}x{content_height}')

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
        self.cursor['x'] += elem_dimensions['width']
        if 'margin-top' in styles:
            self.cursor['y'] -= int(styles['margin-top'])

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
        style['width'] = float(style['width']) * auto_layout_sf
        return style

    def _styles_to_arguments(self, styles):
        # Construct the tkinter arguments (kwag) from the style object
        for attr, val in styles.items():
            styles[attr] = val = None if val == 'None' else val
        kwag = {
            'font': tkfont.Font(self.root, family=styles['font-family'], size=styles['font-size'],
                                weight=styles['font-weight']),
            'fg': styles['foreground-color'],
            'bg': styles['background-color'],
        }
        return kwag

    # Private methods (element rendering)

    def _render(self, elem_name, elem, auto_layout_sf):
        render_groups = {
            'header': self._render_text,
            'button': self._render_button
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
