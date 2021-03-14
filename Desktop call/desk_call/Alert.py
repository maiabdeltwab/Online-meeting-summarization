from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup    
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

# This Class For pop ups
class Alert(Popup):

    def __init__(self, title, text):
        super(Alert, self).__init__()
        content = AnchorLayout(anchor_x='center', anchor_y='bottom')
        # the message content  
        content.add_widget(
            Label(text=text, halign='left', valign='top')
        )
        # ok button to continue
        ok_button = Button(text='Ok', size_hint=(None, None), size=(Window.width / 20, Window.height / 20))
        content.add_widget(ok_button)
        # create the pop up
        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(Window.width / 3, Window.height / 3),
            auto_dismiss=True,
        )
        # action for close
        ok_button.bind(on_press=popup.dismiss)
        # start popup
        popup.open()