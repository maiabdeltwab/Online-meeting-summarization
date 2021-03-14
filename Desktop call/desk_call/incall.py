from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty
import cx_Oracle
import basehash
import login
import connected
import Client as Client

class incall(Screen):
   

    def get_name(self):
        gid = connected.gid
        uid = login.uid
        con = cx_Oracle.connect('meetapp/meetapp@localhost')
        cursor = con.cursor()
        cursor.execute("select name from APP_GROUP where id=:id_group", id_group=gid)
        row = str(cursor.fetchone())
        bad_chars = [':','(',')',"'",","] 
        for i in bad_chars : 
            row = row.replace(i, '')
        gname = row.upper() + ' Group'
        return gname

    def get_users(self):
        gid = connected.gid
        uid = login.uid
        con = cx_Oracle.connect('meetapp/meetapp@localhost')
        cursor = con.cursor()
        cursor.execute("SELECT u.first_name || ' ' || u.last_name FROM AUTH_USER u join APP_USER_PROFILE p on(u.id=p.USER_ID) join APP_GROUP_MEMBERS gm on(gm.USER_ID=u.id) join app_group g on(g.ID=gm.GROUP_ID) WHERE g.id=:id_group and u.id!=:userid and in_call=1", id_group=gid ,userid=uid )
        row = str(cursor.fetchone())
        bad_chars = [':','(',')',"'",","] 
        for i in bad_chars : 
            row = row.replace(i, '')
        user_incall = row
        return user_incall
    

    def endcall(self):
        uid = login.uid
        gid = connected.gid
        con = cx_Oracle.connect('meetapp/meetapp@localhost') 
        cursor = con.cursor()
        cursor.execute("update app_group_members set in_call=:incall where group_id=:groupid and user_id=:userid", incall=0, groupid=gid, userid=uid)
        con.commit()
        connected.client.end_call()
        cursor.close()
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'connected'
        self.manager.get_screen('connected').resetForm()

    def disconnect(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()

    





        #cursor.execute("SELECT u.first_name, u.last_name FROM AUTH_USER u join APP_USER_PROFILE p on(u.id=p.USER_ID) join APP_GROUP_MEMBERS gm on(gm.USER_ID=u.id) join app_group g on(g.ID=gm.GROUP_ID) WHERE g.id =:id_group and in_call=1", id_group=gid)
