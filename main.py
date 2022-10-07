from tk_autolayout import *

def test_cmd(input=None):
    if input is not None:
        print(f'You provided an input! {input}')
    else:
        print(f'Command invoked with no input')

def during(w):
    w.get_elem_by_name('main-title').text('Hello new text!')
    w.get_elem_by_name('do-something')

test_window = AutoLayoutWindow(
    title='Test Application',
    during=during
)

