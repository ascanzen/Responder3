#!/usr/bin/env python3.6

import poplib

user = 'alma'
password = 'alma'
Mailbox = poplib.POP3('localhost', '110') 
Mailbox.user(user) 
Mailbox.pass_(password)
