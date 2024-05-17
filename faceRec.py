import cv2
import face_recognition as fr
import pyrebase
import pyrebase_config as pbc
import firebase_admin
from firebase_admin import credentials, auth, db
import datetime

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

# Verify ID token and get user UID
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

# Load saved face encodings from Firebase Realtime Database
def load_face_encodings_from_firebase():
    db = firebase_admin.db.reference()
    face_encodings = db.child("face_encodings").get()
    
    encodings_dict = {}
    for name, encoding_parts in face_encodings.items():
        # Convert encoding parts to floats and reconstruct the list
        encoding = [float(val) for val in encoding_parts]
        encodings_dict[name] = encoding
    
    return encodings_dict

# Function to log access attempts to Firebase Realtime Database
def log_access_attempt(name, timestamp):
    access_log_ref = db.reference('/access_log')
    access_log_ref.push({
        "name": name,
        "timestamp": timestamp
    })

# Capture a single frame from webcam and encode the face
def capture_and_encode_face():
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
            return face_encoding

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close all OpenCV windows
    video_capture.release()
    cv2.destroyAllWindows()

# Function to compare the captured face encoding with the encodings stored in the Firebase Realtime Database
def compare_face_encodings(captured_encoding, stored_encodings):
    for name, stored_encoding in stored_encodings.items():
        # Compare the captured encoding with each stored encoding
        match = fr.compare_faces([stored_encoding], captured_encoding)
        if match[0]:
            print(f"Hello {name}, you have been authorised.")
            return name
    print("No match found. The captured face does not match any stored encoding, please seek admin support or try again.")
    return None

# Main function
def main():
    # Load saved face encodings from Firebase
    stored_encodings = load_face_encodings_from_firebase()

    # Capture and encode a face from webcam
    captured_encoding = capture_and_encode_face()

    if captured_encoding is not None:
        # Compare the captured face encoding with the stored encodings
        matched_name = compare_face_encodings(captured_encoding, stored_encodings)
        
        # Log access attempt
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_access_attempt(matched_name if matched_name else "Unknown", timestamp)

if __name__ == '__main__':
    main()

