import cv2
import face_recognition as fr
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, db

# Pyrebase config
config = pbc.config

# Initialize Pyrebase
firebase = pyrebase.initialize_app(config)
auth_pyrebase = firebase.auth()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("certificate.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://facerecproj-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Authenticate user with email and password using Pyrebase
# Authenticate user with email and password
email = pbc.email
password = pbc.password
try:
    user = auth_pyrebase.sign_in_with_email_and_password(email, password)
    id_token = user['idToken']
    print('Successfully authenticated user')
except Exception as e:
    print('Authentication failed:', e)
    exit()

# Function to verify ID token and get user UID using Firebase Admin SDK
def verify_id_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        print('Successfully verified ID token:', uid)
        return uid
    except Exception as e:
        print('Error verifying ID token:', e)
    return None

authenticated_user_uid = verify_id_token(id_token)
if authenticated_user_uid is None:
    print("ID token verification failed!")
    exit()

# Function to save the encoding of the detected face to Firebase Realtime Database
def save_face_encoding_to_firebase(encoding, name):
    db = firebase_admin.db.reference()
    # Save the face encoding under the provided name in Firebase Realtime Database
    db.child("face_encodings").child(name).set(encoding.tolist())
    print(f"Face encoding saved to Firebase for {name}")

# Function to capture a single frame from webcam, encode the face, and save the encoding to Firebase
def capture_and_save_face_encoding():
    # Open the webcam
    video_capture = cv2.VideoCapture(0)

    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()

        # Convert the frame from BGR color (OpenCV format) to RGB color (face_recognition format)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find all the faces in the current frame
        face_locations = fr.face_locations(rgb_frame)

        # Encode the first face found in the frame (if any)
        if face_locations:
            top, right, bottom, left = face_locations[0]
            face_encoding = fr.face_encodings(rgb_frame, [face_locations[0]])[0]

            # Prompt user to enter a name for the face encoding
            name = input("Enter the name for this face encoding: ")

            # Save the face encoding to Firebase
            save_face_encoding_to_firebase(face_encoding, name)
            break

        # Display the frame
        cv2.imshow('Video', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close all OpenCV windows
    video_capture.release()
    cv2.destroyAllWindows()

# Main function
def main():
    # Capture a single frame from webcam, encode the face, and save the encoding to Firebase
    capture_and_save_face_encoding()

if __name__ == '__main__':
    main()
