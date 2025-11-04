import os
import mysql.connector as msc
from cryptography.fernet import Fernet as fn


# colours
class c:
   P = '\033[95m' #purple
   C = '\033[96m' #cyan
   DC = '\033[36m' #darkcyan
   B = '\033[94m' #blue
   G = '\033[92m' #green
   Y = '\033[93m' #yellow
   R = '\033[91m' #red
   BD = '\033[1m' #bold
   UL = '\033[4m' #underline
   E = '\033[0m' #end



# ---------- encryption setup

home_dir = os.path.expanduser("~")
backup_dir = os.path.join(home_dir, ".bytevault")
os.makedirs(backup_dir, exist_ok=True)

kpath = os.path.join(backup_dir, "secret.key")

def genkey():
    # gen a fernet key and saving to secret.key

    os.makedirs(os.path.dirname(kpath), exist_ok=True)
    
    key = fn.generate_key()
    with open(kpath, 'wb') as keyf:
        keyf.write(key)
    
    print(c.G + "\n- New encryption key generated -" + c.E)

def loadk():
    # loading existing fernet keyy from file

    with open(kpath, 'rb') as keyf:
        key = keyf.read()

    return key

# print("key path: ", kpath)
# print("exist: ", os.path.exists(kpath))

if not os.path.exists(kpath):
    genkey()

# key = loadk()
# fernet = fn(key)
# print(" + Ecryption key loaded")

fernet = fn(loadk())


def lock(text:str) -> bytes:   
    return fernet.encrypt(text.encode())

def unlock(token:bytes) -> str:
    return fernet.decrypt(token).decode()



# ---------- mysql connection

def connect_db():
    try:
        con = msc.connect(
            host = "localhost",
            user = "root",
            password = input(c.P + "\nEnter MySQL password: " + c.E), 
            database = "bytevault"
        )

        cur = con.cursor()
        print(c.G + "\n- Connected to MySQL -" + c.E)
        return con, cur
    
    except Exception as e:
        print(c.R + "\n! Database connection failed !", e, + c.E)
        exit()

con, cur = connect_db()



# ---------- master password

def setp():
    pw = input(c.P + "Set a master password: " + c.E)
    cur.execute(r"INSERT INTO master (id, master_pass) VALUES (1, %s)", (lock(pw),))
    con.commit()
    print(c.G + "\n- Master password set successfully -" + c.E)

def chkmpw():
    cur.execute("SELECT master_pass FROM master WHERE id=1")
    result = cur.fetchone()
    if not result:
        setp()
        return True
    else:
        pw = input(c.P + "\nEnter master password: " + c.E)
        if unlock(result[0]) == pw:
            print(c.G + "\n- Access granted -" + c.E)
            return True
        else:
            print(c.R + "\n! Access denied !" + c.E)
            return False
        


# ---------- pass manager feaatures

def addp():
    site = input(c.P + "Site/App name: " + c.E)
    user = input(c.P + "Username: " + c.E)
    pw = input(c.P + "Password: " + c.E)
    cur.execute(r"INSERT INTO passwords (site, username, password) VALUES (%s, %s, %s)",
               (site, user, lock(pw)))
    con.commit()
    print(c.G + "\n- Password added successfully -" + c.E)

def viewp():
    cur.execute("SELECT id, site, username, password FROM passwords")
    rows = cur.fetchall()
    for r in rows:
        print(c.BD + f"\nID       : {r[0]}" + c.E, f"\n-------------------------- \nSite     : {r[1]} \nUser     : {r[2]} \nPassword : {unlock(r[3])} \n")

def updp():
    id_ = input(c.P + 'Enter ID to update: ' + c.E)
    npw = input(c.P + "New Password: " + c.E)
    cur.execute(r"UPDATE passwords SET password=%s WHERE id=%s", (lock(npw), id_))
    con.commit()
    print(c.G + "\n- Password updated -" + c.E)

def delp():
    id_ = input(c.P + "Enter ID to delete: " + c.E)
    cur.execute(r"DELETE FROM passwords WHERE id=%s", (id_,))
    con.commit()
    print(c.R + "\n-! Password deleted !-" + c.E)



# ---------- menu

def main():
    if not chkmpw():
        return
    

    print(c.B + r'''
______         _           _   _                _  _   
| ___ \       | |         | | | |              | || |  
| |_/ / _   _ | |_   ___  | | | |  __ _  _   _ | || |_ 
| ___ \| | | || __| / _ \ | | | | / _` || | | || || __|
| |_/ /| |_| || |_ |  __/ \ \_/ /| (_| || |_| || || |_ 
\____/  \__, | \__| \___|  \___/  \__,_| \__,_||_| \__|
         __/ |                                       
        |___/                                                                     
''' + c.E)
    

    while True:
        print(c.Y + '''
1. Add Password
2. View Password
3. Update Password
4. Delete Password
5. Exit
''' + c.E)
        
        ch = input(c.P + "Enter your choice: " + c.E) 
        if ch == '1': 
            addp() 
        elif ch == '2': 
            viewp() 
        elif ch == '3': 
            updp() 
        elif ch == '4': 
            delp() 
        elif ch == '5': 
            print(c.G + "Exiting ByteVault..." + c.E) 
            break 
        else: 
            print(c.R + "\n! Invalid choice. Try again! !" + c.E)
        


if __name__ == "__main__":
    main()
    con.close()       
