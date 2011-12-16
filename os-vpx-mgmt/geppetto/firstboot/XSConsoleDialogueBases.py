# Copyright (c) 2007-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleDialoguePane import *
from XSConsoleFields import *
from XSConsoleLayout import *
from XSConsoleMenus import *
from XSConsoleLang import *
from XSConsoleTask import *
from XSConsoleUtils import *


class Dialogue:
    def __init__(self, inLayout=None, inParent=None):
        self.layout = FirstValue(inLayout, Layout.Inst())
        self.parent = FirstValue(inParent, self.layout.Parent())

        self.panes = {}

    def Pane(self, inName=None):
        return self.panes[FirstValue(inName, 0)]

    def NewPane(self, inPane, inName=None):
        self.panes[FirstValue(inName, 0)] = inPane
        return inPane

    def Title(self):
        return self.title

    def Destroy(self):
        for pane in self.panes.values():
            pane.Delete()

    def Render(self):
        for pane in self.panes.values():
            pane.Render()

    def UpdateFields(self):
        pass

    def NeedsCursor(self):
        retVal = False
        for pane in self.panes.values():
            if pane.NeedsCursor():
                retVal = True
        return retVal

    def CursorOff(self):
        for pane in self.panes.values():
            pane.CursorOff()

    def Reset(self):
        # Reset to known state, e.g. first menu item selected
        pass

    def Snapshot(self):
        retVal = []
        for key in sorted(self.panes.keys()):
            retVal.append(self.panes[key].Snapshot())
        return retVal


class InfoDialogue(Dialogue):
    def __init__(self, inText, inInfo=None):
        Dialogue.__init__(self)
        self.text = inText
        self.info = inInfo

        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddWrappedCentredBoldTextField(self.text)

        if self.info is not None:
            pane.NewLine()
            pane.AddWrappedTextField(self.info)

        helpKeys = {Lang("<Enter>"):
                    Lang("OK"), }
        if pane.NeedsScroll():
            helpKeys.update({Lang("<Page Up/Down>"): Lang("Scroll"),
                             Lang("<F5>"): Lang("Refresh"), })

        pane.AddKeyHelpField(helpKeys)

    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE' or inKey == 'KEY_ENTER':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_PPAGE':
            self.Pane().ScrollPageUp()
        elif inKey == 'KEY_NPAGE':
            self.Pane().ScrollPageDown()
        else:
            handled = False
        return handled


class BannerDialogue(Dialogue):
    def __init__(self, inText):
        Dialogue.__init__(self)
        self.text = inText
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddWrappedCentredBoldTextField(self.text)

    def HandleKey(self, inKey):
        return True


class QuestionDialogue(Dialogue):
    def __init__(self, inText, inHandler):
        Dialogue.__init__(self,)
        self.text = inText
        self.handler = inHandler
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.ResetPosition()

        pane.AddWrappedCentredBoldTextField(self.text)

        pane.AddKeyHelpField({Lang("<F8>"): Lang("Yes"),
                              Lang("<Esc>"): Lang("No"), })

    def HandleKey(self, inKey):
        handled = True
        if inKey == 'y' or inKey == 'Y' or inKey == 'KEY_F(8)':
            Layout.Inst().PopDialogue()
            self.handler('y')
        elif inKey == 'n' or inKey == 'N' or inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            self.handler('n')
        else:
            handled = False

        return handled


class LoginDialogue(Dialogue):
    def __init__(self, inText=None, inSuccessFunc=None):
        Dialogue.__init__(self)
        self.text = inText
        self.successFunc = inSuccessFunc
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet("Login")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.text is not None:
            pane.AddTitleField(self.text)
        pane.AddInputField(Lang("Username", 14), "root", 'username')
        pane.AddPasswordField(Lang("Password", 14), '', 'password')
        pane.AddKeyHelpField({Lang("<Esc>"): Lang("Cancel"),
                              Lang("<Enter>"): Lang("Next/OK"),
                              Lang("<Tab>"): Lang("Next"), })

    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()
                Layout.Inst().PopDialogue()
                Layout.Inst().DoUpdate()
                try:
                    Auth.Inst().ProcessLogin(inputValues['username'],
                                             inputValues['password'])

                    if self.successFunc is not None:
                        self.successFunc()
                    else:
                        Layout.Inst().\
                        PushDialogue(InfoDialogue(Lang('Login Successful')))

                except Exception, e:
                    Layout.Inst().\
                    PushDialogue(InfoDialogue(Lang('Login Failed: ') + \
                                              Lang(e)))

        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass         # Leave handled as True
        else:
            handled = False
        return handled


class InputDialogue(Dialogue):
    def __init__(self, inLayout=None, inParent=None):
        Dialogue.__init__(self, inLayout, inParent)
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(self.Custom('title'))
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)

    def Custom(self, inKey):
        return self.custom.get(inKey, None)

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.Custom('info') is not None:
            pane.AddWrappedTextField(self.Custom('info'))
            pane.NewLine()

        for field in self.Custom('fields'):
            pane.AddInputField(*field)

        pane.AddKeyHelpField({Lang("<Enter>"): Lang("OK"),
                              Lang("<Esc>"): Lang("Cancel"), })

    def HandleCommit(self, inValues):            # Override this
        Layout.Inst().PopDialogue()

    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                try:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().DoUpdate()
                    title, info = \
                        self.HandleCommit(self.Pane().GetFieldValues())
                    Layout.Inst().PushDialogue(InfoDialogue(title, info))
                except Exception, e:
                    Layout.Inst().\
                        PushDialogue(InfoDialogue(Lang('Failed: ') + Lang(e)))
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':     # BTAB not available on all platforms
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass     # Leave handled as True
        else:
            handled = False
        return handled


class ProgressDialogue(Dialogue):
    def __init__(self, inTask, inText):
        Dialogue.__init__(self)
        self.task = inTask
        self.text = inText

        self.ChangeState('INITIAL')

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()

    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddTitleField(self.text)

        try:
            progressVal = self.task.ProgressValue()
            progressStr = str(int(100 * progressVal)) + '%'
            durationSecs = self.task.DurationSecs()
            elapsedStr = TimeUtils.DurationString(durationSecs)

        except Exception, e:
            progressStr = Lang('<Unavailable>')
            elapsedStr = Lang('<Unavailable>')

        pane.AddWrappedTextField(Lang('Time', 16) + elapsedStr)
        pane.AddWrappedTextField(Lang('Progress', 16) + progressStr)

        helpKeys = {Lang("<Enter>"): Lang("Hide This Window"), }
        if self.task.CanCancel():
            helpKeys[Lang('<Esc>')] = Lang('Cancel Operation')
        pane.AddKeyHelpField(helpKeys)

    def UpdateFieldsCANCEL(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddTitleField(self.text)
        pane.AddWrappedBoldTextField(Lang('Attempting to cancel operation...'))
        pane.NewLine()

        try:
            progressVal = self.task.ProgressValue()
            progressStr = str(int(100 * progressVal)) + '%'
            durationSecs = self.task.DurationSecs()
            elapsedStr = TimeUtils.DurationString(durationSecs)

        except Exception, e:
            progressStr = Lang('<Unavailable>')
            elapsedStr = Lang('<Unavailable>')

        pane.AddWrappedTextField(Lang('Time', 16) + elapsedStr)
        pane.AddWrappedTextField(Lang('Progress', 16) + progressStr)

        helpKeys = {Lang("<Enter>"): Lang("Hide This Window"), }
        pane.AddKeyHelpField(helpKeys)

    def UpdateFieldsCOMPLETE(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddTitleField(self.text)

        message = self.task.Message()
        pane.AddWrappedBoldTextField(message)
        pane.NewLine()

        progressStr = '100%'
        try:
            durationSecs = self.task.DurationSecs()
            elapsedStr = TimeUtils.DurationString(durationSecs)

        except Exception, e:
            elapsedStr = Lang(e)

        pane.AddWrappedTextField(Lang('Time', 16) + elapsedStr)
        pane.AddKeyHelpField({Lang("<Enter>"): Lang("OK"), })

    def UpdateFields(self):
        if self.state != 'COMPLETE' and not self.task.IsPending():
            self.HandleCompletion()
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields' + self.state)()
        # Despatch method named 'UpdateFields'+self.state

    def LiveUpdateFields(self):
        self.UpdateFields()

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()

    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE':
            if self.task.CanCancel():
                self.task.Cancel()
                self.ChangeState('CANCEL')
            else:
                Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            Layout.Inst().PopDialogue()
        else:
            handled = False
        return True

    def HandleCompletion(self):
        # This method is called from UpdateFields,
        # so shouldn't pop the dialogue, etc.
        self.ChangeState('COMPLETE')


class DialogueUtils:
    # Helper for activate
    @classmethod
    def AuthenticatedOnly(cls, inFunc):
        inFunc()

    @classmethod
    def AuthenticatedOrPasswordUnsetOnly(cls, inFunc):
        inFunc()
