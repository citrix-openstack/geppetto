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

import sys
import os
import time
import string
import curses

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleImporter import *
from XSConsoleMenus import *
from XSConsoleLang import *
from XSConsoleLayout import *
from XSConsoleLog import *
from XSConsoleRemoteTest import *
from XSConsoleRootDialogue import *
from XSConsoleState import *


class App:
    __instance = None

    @classmethod
    def Inst(cls):
        if cls.__instance is None:
            cls.__instance = App()
        return cls.__instance

    def __init__(self):
        self.cursesScreen = None

    def AssertScreenSize(self):
        if hasattr(self, 'layout'):
            self.layout.AssertScreenSize()

    def Build(self, inDirs=None):
        # Search for the app plugins and include them
        Importer.Reset()
        for dir in inDirs:
            Importer.ImportRelativeDir(dir)

    def Enter(self):
        startTime = time.time()
        #Data.Inst().Update()
        elapsedTime = time.time() - startTime
        XSLog('Loaded initial xapi and system data '
              ' in %.3f seconds' % elapsedTime)

        doQuit = False

        RemoteTest.Inst().SetApp(self)

        while not doQuit:
            try:
                try:
                    # Select default character set, ISO 8859-1 (ISO 2022)
                    sys.stdout.write("\033%@")
                    if os.path.isfile("/bin/setfont"):
                        # Restore the default font
                        os.system("/bin/setfont")
                    if '-f' in sys.argv:
                        # -f means that this is the automatically started
                        # xsonsole on tty1, so set it up to suit xsconsole
                        # Disable Print Screen key as quit
                        os.system('/bin/stty quit ^-')
                        # Disable Ctrl-S as suspend
                        os.system('/bin/stty stop ^-')

                    # Speed up processing of the escape key
                    os.environ["ESCDELAY"] = "50"

                    self.cursesScreen = CursesScreen()
                    self.renderer = Renderer()
                    self.layout = Layout.NewInst()
                    self.layout.ParentSet(self.cursesScreen)
                    self.layout.WriteParentOffset(self.cursesScreen)
                    self.layout.Create()
                    self.layout.\
                        ParentSet(self.layout.Window(self.layout.WIN_MAIN))
                    self.layout.CreateRootDialogue(BlankDialogue())
                    self.layout.\
                        TransientBannerHandlerSet(App.TransientBannerHandler)

                    Importer.ActivateNamedPlugIn('FIRST_TIME_PROMPTS')

                    if State.Inst().PasswordChangeRequired():
                        Importer.ActivateNamedPlugIn('CHANGE_PASSWORD',
                                                     Lang("Please change the "
                                                          "password for user "
                                                          "'root' before "
                                                          "continuing"))
                    elif State.Inst().RebootMessage() is not None:
                        Importer.\
                            ActivateNamedPlugIn('REBOOT',
                                                State.Inst().RebootMessage())
                        State.Inst().RebootMessageSet(None)

                    self.layout.Clear()
                    if not '--dryrun' in sys.argv:
                        self.MainLoop()

                finally:
                    if self.cursesScreen is not None:
                        self.cursesScreen.Exit()

                if self.layout.ExitCommand() is None:
                    doQuit = True
                else:
                    os.system('/usr/bin/reset')
                    if self.layout.ExitBanner() is not None:
                        reflowed = \
                            Language.ReflowText(self.layout.ExitBanner(), 80)
                        for line in reflowed:
                            print(line)
                        sys.stdout.flush()
                    commandList = self.layout.ExitCommand().split()

                    if len(commandList) == 0:
                        doQuit = True
                    else:
                        if self.layout.ExitCommandIsExec():
                            os.execv(commandList[0], commandList)
                            # Does not return
                        else:
                            os.system(self.layout.ExitCommand())

            except KeyboardInterrupt, e:
                XSLog('Resetting due to Ctrl-C')
                # Data.Reset()
                sys.stderr.write("\033[H\033[J" + Lang("Resetting..."))
                try:
                    time.sleep(0.5)
                except Exception, e:
                    pass
            except Exception, e:
                sys.stderr.write(Lang(e) + "\n")
                doQuit = True
                if self.cursesScreen is not None:
                        self.cursesScreen.Exit()
                raise

    def NeedsRefresh(self):
        self.needsRefresh = True

    def HandleKeypress(self, inKeypress):
        handled = True
        Auth.Inst().KeepAlive()
        self.lastWakeSeconds = time.time()
        if self.layout.TopDialogue().HandleKey(inKeypress):
            State.Inst().SaveIfRequired()
            self.needsRefresh = True
        elif inKeypress == 'KEY_ESCAPE':
            # Set root menu choice to the first, to give a fixed
            # start state after lots of escapes
            self.layout.TopDialogue().Reset()
            self.needsRefresh = True
        elif inKeypress == 'KEY_F(5)':
            #Data.Inst().Update()
            self.layout.UpdateRootFields()
            self.needsRefresh = True
        # Ctrl-L
        elif inKeypress == '\014':
            Layout.Inst().Clear()
            self.needsRefresh = True
        else:
            handled = False

        return handled

    def MainLoop(self):
        doQuit = False
        startSeconds = time.time()
        lastDataUpdateSeconds = startSeconds
        lastScreenUpdateSeconds = startSeconds
        lastGarbageCollectSeconds = startSeconds
        self.lastWakeSeconds = startSeconds
        resized = False
        #data = Data.Inst()
        errorCount = 0

        self.layout.DoUpdate()
        while not doQuit:
            self.needsRefresh = False
            gotTestCommand = RemoteTest.Inst().Poll()
            secondsNow = time.time()
            try:
                if gotTestCommand:
                    # Prevent delay whilst waiting for a keypress
                    gotKey = None
                elif secondsNow - self.lastWakeSeconds > \
                                        State.Inst().SleepSeconds():
                    gotKey = None
                    Layout.Inst().\
                        PushDialogue(BannerDialogue(Lang("Press any key "
                                                         "to access this "
                                                         "console")))
                    Layout.Inst().Refresh()
                    Layout.Inst().DoUpdate()
                    XSLog('Entering sleep due to inactivity - xsconsole is '
                          'now blocked waiting for a keypress')
                    self.layout.Window(Layout.WIN_MAIN).GetKeyBlocking()
                    XSLog('Exiting sleep')
                    self.lastWakeSeconds = time.time()
                    self.needsRefresh = True
                    Layout.Inst().PopDialogue()
                else:
                    gotKey = self.layout.Window(Layout.WIN_MAIN).GetKey()

            except Exception, e:
                gotKey = None
                # Catch timeout

            if gotKey == "\011":
                gotKey = "KEY_TAB"
            if gotKey == "\012":
                gotKey = "KEY_ENTER"
            if gotKey == "\033":
                gotKey = "KEY_ESCAPE"
            if gotKey == "\177":
                gotKey = "KEY_BACKSPACE"
            # Handle function key mistranslation on vncterm
            if gotKey == '\xc2':
                gotKey = "KEY_F(5)"
            # Handle function key mistranslation on vncterm
            if gotKey == '\xc5':
                gotKey = "KEY_F(8)"

            if gotKey == 'KEY_RESIZE':
                XSLog('Activity on another console')
                resized = True
            elif resized and gotKey is not None:
                # Restore the default font
                if os.path.isfile("/bin/setfont"):
                    os.system("/bin/setfont")
                resized = False

            # Screen out non-ASCII and unusual characters
            for char in FirstValue(gotKey, ''):
                if char >= "\177":
                    # Characters 128 and greater
                    gotKey = None
                    break

            secondsNow = time.time()
            secondsRunning = secondsNow - startSeconds

            if secondsNow - lastScreenUpdateSeconds >= 2:
                lastScreenUpdateSeconds = secondsNow
                self.layout.UpdateRootFields()
                self.needsRefresh = True

            if gotKey is not None:
                try:
                    self.HandleKeypress(gotKey)

                except Exception, e:
                    if Auth.Inst().IsTestMode():
                        raise
                    message = Lang(e)
                    # Also logs the error
                    if errorCount <= 10:
                        if errorCount == 10:
                            message += Lang('\n\n(No more errors will be '
                                            'reported)')
                        errorCount += 1
                        Layout.Inst().PushDialogue(InfoDialogue(Lang("Error"),
                                                                message))

            if self.layout.ExitCommand() is not None:
                doQuit = True

            timeStr = time.strftime(" %H:%M ", time.localtime())
            self.renderer.RenderStatus(self.layout.Window(Layout.WIN_TOPLINE),
                                       timeStr)

            if self.needsRefresh:
                self.layout.Refresh()
            elif self.layout.LiveUpdateFields():
                self.layout.Refresh()

            self.layout.DoUpdate()

            if secondsNow - lastGarbageCollectSeconds >= 60:
                lastGarbageCollectSeconds = secondsNow
                Task.Inst().GarbageCollect()

    def HandleRestartChoice(self, inChoice):
        pass

    @classmethod
    def TransientBannerHandler(self, inMessage):
        layout = Layout.Inst()
        layout.PushDialogue(BannerDialogue(inMessage))
        layout.Refresh()
        layout.DoUpdate()
        layout.PopDialogue()


class Renderer:
    def RenderStatus(self, inWindow, inText):
        # Store cursor position
        (cursY, cursX) = curses.getsyx()
        inWindow.Win().erase()
        inWindow.AddText(inText, 0, 0)
        inWindow.Refresh()
        if cursX != -1 and cursY != -1:
            # Restore cursor position
            curses.setsyx(cursY, cursX)


class BlankDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

    def HandleKey(self, inKey):
        return False
