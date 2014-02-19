'''
Recreate the database for pyoseo
'''

import pyoseo
#from mixer.backend.sqlalchemy import mixer

def main():
    pyoseo.db.create_all()

if __name__ == '__main__':
    main()
