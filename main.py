from tk_autolayout import *

test_window = AutoLayoutWindow(
    title='Python Application',
    interface='''
        line_0:
            logo_text:
                kind: header
                text: Python App
        line_1:
            sub_text:
                kind: header
                text: Welcome to this Python application.
        line_2:
            btn:
                kind: button
                text: Let's go
    ''',
    presentation='''
        window:
            background-color: white
        sub_text:
            font-weight: normal
            font-size: 15
    '''
)
