import os
import firebase_admin

credential_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
credential = firebase_admin.credentials.Certificate(credential_path)

firebase_admin.initialize_app(credential)