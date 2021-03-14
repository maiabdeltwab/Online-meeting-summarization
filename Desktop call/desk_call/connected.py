from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition ,ScreenManager
import cx_Oracle
import basehash
import login
import Client as Client
from Alert import Alert
from incall import incall

class Connected(Screen):
    
    def connect(self, code):
        app = App.get_running_app()
        app.code = code
        try:
            # unhashing the invite code
            hash_fn = basehash.base36()
            sp = code.split('z')
            ip = str(hash_fn.unhash(sp[0])) + '.' + str(hash_fn.unhash(sp[1]))+ '.' +\
                     str(hash_fn.unhash(sp[2])) + '.' + str(hash_fn.unhash(sp[3]))
            global gid
            gid = int(hash_fn.unhash(sp[4]))
            uid = login.uid

            #add screen incall here (not in main) as it uses gid and uid
            self.manager.add_widget(incall(name='incall'))  

            #connect to database to check for the inv. code
            con = cx_Oracle.connect('meetapp/meetapp@localhost')
            cursor = con.cursor()
            cursor.execute("select ID from APP_GROUP where INVITE_CODE=:inv_code", inv_code=code)
            row = cursor.fetchone()
            
            if row != None :
                                
                # Check if the user in this group
                cursor.execute("select USER_ID from APP_GROUP_MEMBERS where GROUP_ID=:groupid and USER_ID=:userid", groupid=gid ,userid=uid)
                row = cursor.fetchone()
                
                if row != None :
                    cursor.execute("select call_state from app_group where id=:groupid", groupid=gid)
                    row = cursor.fetchone()                   
                    
                    if row != None:
                        port = row[0]
                        # update call state
                        cursor.execute("update app_group_members set in_call=:incall where group_id=:groupid and user_id=:userid", incall=1, groupid=gid, userid=uid)
                        con.commit()

                        cursor.execute("select id from APP_GROUP_MEMBERS where group_id=:groupid and user_id=:userid", groupid=gid, userid=uid)
                        print(uid)
                        row = cursor.fetchone()
                        print(row[0])
                        group_member_id = row[0]  

                        global client
                        client = Client.Client(ip, port, group_member_id)
                        
                        self.manager.transition = SlideTransition(direction="right")
                        self.manager.current = 'incall'
                    else :
                        Alert('Error','Please try again')
                        self.manager.get_screen('connected').resetForm()
                # if not group member
                else :
                    Alert('Error','You are not in this group.\nAsk the group admin to enter you.')
                    self.manager.get_screen('connected').resetForm()
                #cursor.close() 
            else : 
                Alert('Error','No available call for this group')
                self.manager.get_screen('connected').resetForm()
        # if code is invalid
        except:   
              Alert('Error','Please enter valid code')
              self.manager.get_screen('connected').resetForm()   

    def disconnect(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()

    def resetForm(self):
        self.ids['code'].text = ""
