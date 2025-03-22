# BARSKA_AX
# Secure Chat Application - Safe Web Domain

## Project Description
**The project is a secure web-based chat application, free from surveillance by major corporations.**  
We provide you with your own private server in a secure environment, allowing safe communication without interference from external entities.

### First, send blessings upon the Messenger of Allah.

---

## How to Run the Project
1.**Load the necessary dependencies in termux**
```bash
pkg update && pkg ugrade -y

 ```
2.**insrall git | python** 
```bash
pkg instal git && pkg install python3 -y
```

3. **Clone the Repository**:
    ```bash
    git clone https://github.com/Mohamed9x60/BARSKA-AX.git


4.**Open the file**
   ```bash
     cd BARSKA-AX
   ```

5.**Run code**
```bach
python3 BARSKA-AX.py
```

 6.**Install Required Dependencies**
Install the necessary packages by running the following command:
```bash
pip install -r requirements.txt
```


---

## Password Management

# The main password file is named paswod.txt. You can open and modify it with the command:
```bash
nano paswod.txt
```
.Press Ctrl + x, y and enter
Set your default passwords here.

Warning: If login fails 3 times, your IP address will be blocked. Blocked IPs are stored in blocked_ips.txt. You can remove a blocked IP by editing this file.



---

Key Management

The application key is stored in key.txt and is automatically generated the first time the application is run.



---

Running on Local Domain

When you start the application, you will see your local domain URL, which could be one of the following:

http://127.0.0.1:5000

http://192.168.137.152:5000




---

## Running on Public Domain

# To run the application on a public domain, install ngrok and follow these steps:

1. **Install ngrok**
2. Visit ngrok's official website to download and install ngrok.
url:
https://dashboard.ngrok.com/get-started/setup/linux
3.**Expose Local Server**
Run one of the following commands to expose your local server to the internet:
```bash
ngrok http http://127.0.0.1:5000
```

Or, specify a different port:
```bash
ngrok http 5000
```

3. Access the Public Link
After running the command, ngrok will generate a public link. Use this link to access the application from anywhere.


---


## Downloading and Running on Linux 


# You can clone this project from GitHub on Termux or Linux by following these steps:


1. **Install Git (if not already installed)**

Run the following commands based on your platform:

Linux (Debian/Ubuntu/kali linux):
```bash
sudo apt update && sudo apt install git
```


2. **Clone the Repository**
Replace USERNAME and REPOSITORY with the GitHub username and repository name for this project:
```bash
git clone https://github.com/Mohamed9x60/BARSKA-AX.git
```

3.**Open the file**
```bash
cd BARSKA-AX
```

4. **Run cod**
  ```bash
   python3 BARSKA-AX.py
  ```

4. ***Install Python Dependencies***
```bash
pip install -r requirements.txt
```

5. **Run the Application**
```bash
./aap.bin
```

---

# Now, your application should be up and running on Termux or Linux.


---

Enjoy your secure and private chat experience!

