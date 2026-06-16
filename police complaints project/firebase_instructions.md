# Integrating Firebase Firestore with ReportSafe

This guide explains how to connect the Complaint Registration Web Application to **Firebase Firestore** (a cloud NoSQL database) instead of the default SQLite local database.

---

## Step 1: Install Firebase Admin SDK
Make sure the `firebase-admin` library is installed in your python environment:
```bash
pip install firebase-admin
```

---

## Step 2: Download your Service Account Credentials Key
To authenticate the backend with your cloud database:
1. Open the [Firebase Console](https://console.firebase.google.com/).
2. Select your project (create one if you haven't yet).
3. Click the gear icon next to **Project Overview** in the left sidebar and select **Project Settings**.
4. Go to the **Service Accounts** tab.
5. Click **Generate New Private Key**.
6. A `.json` file containing your private key credentials will download.
7. Move/copy this downloaded file into the root of this project folder and rename it exactly to:
   ```text
   serviceAccountKey.json
   ```

---

## Step 3: Enable Firestore Database in Console
If you haven't activated Firestore:
1. In the left sidebar of the Firebase Console, click on **Build** -> **Firestore Database**.
2. Click **Create database**.
3. Choose a location and start in **Test mode** (or production mode, since we will access it via secure server-side SDK credentials which bypass client security rules).

---

## Step 4: Toggle the Database Type
We created [firebase_db.py](file:///c:/Users/bhavi/Desktop/police%20complaints%20project/firebase_db.py) which fully implements all database operations for user accounts, complaints, comments, and notifications in Firestore.

To switch the application to use Firebase, update [config.py](file:///c:/Users/bhavi/Desktop/police%20complaints%20project/config.py):
```python
# Change DB_TYPE to 'firebase'
DB_TYPE = 'firebase'
```
We can also update [app.py](file:///c:/Users/bhavi/Desktop/police%20complaints%20project/app.py) to dynamically load the selected database backend module.
