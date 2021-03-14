import os

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

import cx_Oracle
from Alert import Alert


class Login(Screen):
    def do_login(self, loginText, passwordText):
        app = App.get_running_app()

        app.username = loginText
        app.password = passwordText
        if app.password == "" :
            Alert('Error','Invalid Username or password')
        else :
            con = cx_Oracle.connect('meetapp/meetapp@localhost') 
            # Now execute the sqlquery 
            cursor = con.cursor() 
            cursor.execute("select id from auth_user where username=:user_name", user_name=loginText)
            row = cursor.fetchone()
            cursor.close()
            
            if row != None:
                global uid
                uid = row[0]
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'connected'
            
            else:
                Alert('Error','Invalid Username or password')
                self.resetForm()

        app.config.read(app.get_application_config())
        app.config.write()

    def resetForm(self):
        self.ids['nick'].text = ""
        self.ids['password'].text = ""
