#!/usr/bin/env python3

from Modules import Module
from sqlalchemy import *
from sqlalchemy_utils import database_exists
from os import listdir


class Database(Module):

    def database_create(self):
        link = input("Please provide us the URL of the database:\n > ")
        db_name = input("Please provide the database to create (Default "
                        "is opensips):\n > ")
        if db_name is "":
            db_name = 'opensips'
        engine = create_engine(link)
        conn = engine.connect()

        print("The following modules are available to deploy:\n")
        scripts = []
        script_to_deploy = {}
        cnt = 0
        for f in listdir('/home/dorin/opensips_2_4/scripts/mysql'):
            cnt = cnt + 1
            scripts.append('[{}] {}'.format(cnt, f.split('-')[0]))
            script_to_deploy[cnt] = f
        for a, b, c in zip(scripts[::3], scripts[1::3], scripts[2::3]):
            print('{:<30}{:<30}{:<}'.format(a, b, c))

        modules = input("Please indicate, separated by spaces, which modules "
                        "you would like to deploy:\n > ")
        modules = modules.split(' ')
        print("You have chosen to create the following modules:")
        for i in modules:
            print(scripts[int(i)-1].split(' ')[1], end=' ')
        proc = input('\nWould you like to proceed [Y/n]? > ')
        if proc is 'n':
            return

        # Create the database
        flag = 0
        if database_exists(link + '/' + db_name):
            flag = 1
        if flag is 0:
            conn.execute('CREATE DATABASE ' + db_name)
        conn.execute('USE ' + db_name)

        # Adding the default module(s)
        if flag is 0:
            modules.insert(0, '35')

        # Creating the big script based on the chosen modules
        with open('/home/dorin/OpenSIPS_RSoC/tmp/db_script', 'w') as outfile:
            for ind in n:
                with open('/home/dorin/opensips_2_4/scripts/mysql/' +
                          script_to_deploy[int(ind)]) as infile:
                    for line in infile:
                        outfile.write(line)

        # Running the script
        with open('/home/dorin/OpenSIPS_RSoC/tmp/db_script', 'r') as file:
            # print(file.read())
            conn.execute(file.read())
        conn.close()
        print("The database has been successfully created.")
