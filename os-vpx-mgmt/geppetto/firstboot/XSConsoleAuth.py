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

import os
import pwd
import re
import sys
import time


from XSConsoleBases import *
from XSConsoleLang import *
from XSConsoleLog import *
from XSConsoleState import *
from XSConsoleUtils import *


class Auth:
    instance = None

    def __init__(self):
        self.isAuthenticated = False
        self.loggedInUsername = ''
        self.loggedInPassword = ''
        self.defaultPassword = ''
        self.testingHost = None
        self.authTimestampSeconds = None

        self.testMode = False
        # The testing.txt file is used for testing only
        testFilename = sys.path[0]
        if testFilename == '':
            testFilename = '.'
        testFilename += '/testing.txt'
        if os.path.isfile(testFilename):
            self.testMode = True
            testingFile = open(testFilename)
            for line in testingFile:
                match = re.match(r'host=([a-zA-Z0-9-]+)', line)
                if match:
                    self.testingHost = match.group(1)
                match = re.match(r'password=([a-zA-Z0-9-]+)', line)
                if match:
                    self.defaultPassword = match.group(1)

            testingFile.close()

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Auth()
        return cls.instance

    def IsTestMode(self):
        return self.testMode

    def AuthAge(self):
        if self.isAuthenticated:
            retVal = time.time() - self.authTimestampSeconds
        else:
            raise(Exception, "Cannot get age - not authenticated")
        return retVal

    def KeepAlive(self):
        if self.isAuthenticated:
            if self.AuthAge() <= State.Inst().AuthTimeoutSeconds():
                # Auth still valid, so update timestamp to now
                self.authTimestampSeconds = time.time()

    def LoggedInUsername(self):
        if (self.isAuthenticated):
            retVal = self.loggedInUsername
        else:
            retVal = None
        return retVal

    def DefaultPassword(self):
        return self.defaultPassword

    def TCPAuthenticate(self, inUsername, inPassword):
        pass

    def PAMAuthenticate(self, inUsername, inPassword):
        pass

    def ProcessLogin(self, inUsername, inPassword):
        pass

    def IsAuthenticated(self):
        if self.isAuthenticated and \
                self.AuthAge() <= State.Inst().AuthTimeoutSeconds():
            retVal = True
        else:
            retVal = False
        return retVal

    def AssertAuthenticated(self):
        if not self.isAuthenticated:
            raise Exception("Not logged in")
        if self.AuthAge() > State.Inst().AuthTimeoutSeconds():
            raise Exception("Session has timed out")

    def AssertAuthenticatedOrPasswordUnset(self):
        if self.IsPasswordSet():
            self.AssertAuthenticated()

    def LogOut(self):
        self.isAuthenticated = False
        self.loggedInUsername = None

    def OpenSession(self):
        self.error = "Ooops"
        return None

    def NewSession(self):
        return self.OpenSession()

    def CloseSession(self, inSession):
        inSession.logout()
        return None

    def IsPasswordSet(self):
        # Security critical - mustn't wrongly return False
        retVal = True

        rootHash = pwd.getpwnam("root")[1]
        if rootHash == '!!':
            retVal = False

        return retVal

    def ChangePassword(self, inOldPassword, inNewPassword):

        if inNewPassword == '':
            raise Exception(Lang('An empty password is not allowed'))
        if re.match(r'\s*$', inNewPassword):
            raise Exception(Lang('Passwords containing only spaces are '
                                 'not allowed'))

        try:
            # Use xapi if possible, to take care of password changes for pools
            session = self.OpenSession()
            try:
                session.xenapi.session.change_password(inOldPassword,
                                                       inNewPassword)
            finally:
                self.CloseSession(session)
        except Exception, e:
            ShellPipe("/usr/bin/passwd", "--stdin", "root").Call(inNewPassword)
            raise Exception(Lang("The underlying Xen API xapi could not "
                                 "be used.  Password changed successfully "
                                 "on this host only."))

        # Caller handles exceptions

    def TimeoutSecondsSet(self, inSeconds):
        Auth.Inst().AssertAuthenticated()
        State.Inst().AuthTimeoutSecondsSet(inSeconds)
