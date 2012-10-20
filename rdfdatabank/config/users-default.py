#-*- coding: utf-8 -*-
"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

_USERS = {
'admin': {'owner': '*', 'first_name': 'Databank', 'last_name': 'Admin', 'role': 'admin', 'description': 'Admin for all silos'}, 
'admin2': {'owner': ['sandbox'], 'first_name': 'Databank', 'last_name': 'Admin-2', 'role': 'admin', 'description': 'Admin for silo Sandbox'},
'admin3': {'owner': ['sandbox2'], 'first_name': 'Databank', 'last_name': 'Admin-3', 'role': 'admin', 'description': 'Admin for silo Sandbox2'},
'sandbox_user': {'owner': ['sandbox'], 'role': 'user', 'name': 'Sandbox user', 'description': 'User for silo Sandbox'},
'sandbox_user2': {'owner': ['sandbox'], 'role': 'user', 'name': 'Sandbox user-2', 'description': 'User for silo Sandbox'},
'sandbox_user3': {'owner': ['sandbox2'], 'role': 'user', 'name': 'Sandbox user-3', 'description': 'User for silo Sandbox2'},
'sandbox_manager': {'owner': ['sandbox'], 'role': 'manager', 'name': 'Sandbox manager', 'description': 'Manager for silo Sandbox'},
'sandbox_manager2': {'owner': ['sandbox'], 'role': 'manager', 'name': 'Sandbox manager-2', 'description': 'Manager for silo Sandbox'},
'sandbox_manager3': {'owner': ['sandbox2'], 'role': 'manager', 'name': 'Sandbox manager-3', 'description': 'Manager for silo Sandbox2'}
}
