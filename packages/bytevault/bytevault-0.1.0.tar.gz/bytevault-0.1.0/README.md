[![Athena Award Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Faward.athena.hackclub.com%2Fapi%2Fbadge)](https://award.athena.hackclub.com?utm_source=readme)

# ByteVault

ByteVault is a lightweight program designed for storing passwords in a database securely using cryptography algorithms.

---

## Features

- Master Password for accessing the database itself
- Adding new passwords
- View Passwords
- Update Passwords
- Delete Passwords
- Passwords stored with encryption

---

## Screenshots

**Add Password**
<br>
![Add password](<Screenshots/Add.png>)
<br>

**View Passwords**
<br>
![View Passwords](<Screenshots/View.png>)
<br>

**Update Password**
<br>
![Update password](<Screenshots/Update.png>)
<br>

**Delete Password**
<br>
![Delete password](<Screenshots/Delete.png>)
<br>

**Database View out of program**
<br>
The passwords will look gibberish, it's encrypted.
<br>
![encrypted](<Screenshots/Database.png>)
<br>

## Installation & Usage

#### Clone the repository

```bash
git clone https://github.com/cracking-bytes/ByteVault.git
```

#### Go to directory

```bash
cd ByteVault
```

#### Install dependencies

```bash
pip install -r requirements.txt
```
#### Setup Database

- Use this [program](src/database.py)
- Enter MySQL password to connect (when asked for input)
- Your database is ready for use 

#### Usage

```bash
python3 src/main.py
```
---
#### Note
> You can also see my [notes](notes.txt) to understand the concepts used in this program. But I made those notes for myself while learning so you might not understand some things. :)
---

## Tech Stack

**Language used:**
- Python 3

**Libraries used:**
- `os`
- `mysql.connector`
- `cryptography`

**Development tools:**
- VS Code
- Git & Github for version control

## License

[MIT](https://github.com/cracking-bytes/ByteVault?tab=MIT-1-ov-file)

---

## Author

Bhavika Nagdeo (Cracking Bytes)
- [GitHub](https://github.com/cracking-bytes)  
- [LinkedIn](https://in.linkedin.com/in/bhavikanagdeo)  
- [Instagram](https://www.instagram.com/cracking.bytes/)  
- [Medium](https://crackingbytes.medium.com/)

---

## Feedback
If you have any feedback, ideas, or features to suggest, reach out at bhavikanagdeo83@gmail.com