from tk_autolayout import *

test_window = AutoLayoutWindow(
    title='Python Application',
    interface='''
        line_0:
            main_title_text:
                kind: header
                text: Hello, world
        line_1:
            paragraph_text:
                kind: header
                text: Welcome to this Python application.
            aside_photograph:
                kind: image
                presentation:
                    image-url: image.jpg
                    height: 80
        line_2:
            primary_action_button:
                kind: button
                text: Let's go
    ''',
    presentation='''
        window:
            width: 450
        paragraph_text:
            font-weight: normal
            font-size: 15
    '''
)
