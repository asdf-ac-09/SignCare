import sys
import os
import time
import threading
import json
import queue

from flask import Flask, render_template, Response
from flask_socketio import SocketIO

import cv2
import torch
import numpy as np
import mediapipe as mp

from gtts import gTTS
from playsound import playsound

from vosk import Model, KaldiRecognizer
import sounddevice as sd

# ---------------- PATH ----------------
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from utils.motion import add_velocity
from utils.sentence_builder import SentenceBuilder

# ---------------- FLASK ----------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------- SETTINGS ----------------
MODEL_PATH = os.path.join(ROOT_DIR, "weights", "bestest_model_optimized.pt")
LABELS_JSON = os.path.join(ROOT_DIR, "labels.json")
SENTENCE_JSON = os.path.join(ROOT_DIR, "utils", "sentences.json")
VOSK_MODEL_PATH = os.path.join(ROOT_DIR, "vosk_models", "vosk-model-tl-ph-generic-0.6")

CONF_THRESHOLD = 0.75
WINDOW_SIZE = 40
STRIDE = 5
MAX_WORDS = 5

NO_HANDS_LIMIT = 20
COOLDOWN = 1.5

# ---------------- LABELS ----------------
with open(LABELS_JSON, "r", encoding="utf-8") as f:
    labels_dict = json.load(f)

# Convert labels dict to list sorted by key
labels = [labels_dict[str(i)] for i in range(len(labels_dict))]
print("LABELS:", labels)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------- MODEL ----------------
print("Loading TorchScript model...")
# TorchScript model: load directly, no state_dict
model = torch.jit.load(MODEL_PATH, map_location=device)
model.eval()

# ---------------- SENTENCE BUILDER + JSON ----------------
builder = SentenceBuilder()
sentence_map = {}
if os.path.exists(SENTENCE_JSON):
    with open(SENTENCE_JSON, "r", encoding="utf-8") as f:
        sentence_map = json.load(f)
builder.sentence_map = sentence_map

# ---------------- VOSK ----------------
print("Loading Tagalog VOSK model...")
vosk_model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(vosk_model, 16000)
audio_queue = queue.Queue()

# ---------------- STATE ----------------
is_recording = False
no_hands_counter = 0
recorded_sequence = []
last_prediction_time = 0

# ---------------- TTS ----------------
def speak(text):
    def run():
        try:
            tts = gTTS(text=text, lang="tl")
            filename = "temp.mp3"
            tts.save(filename)
            playsound(filename)
            os.remove(filename)
        except:
            pass
    threading.Thread(target=run, daemon=True).start()

# ---------------- AUDIO CALLBACK ----------------
def audio_callback(indata, frames, time_, status):
    audio_queue.put(bytes(indata))

# ---------------- DOCTOR VOICE LISTENER ----------------
def vosk_listener():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=audio_callback):
        print("Doctor microphone listening...")
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text.strip() != "":
                    print("DOCTOR:", text)
                    socketio.emit("new_speech", {"text": text, "sender": "doctor"})

# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_face = mp.solutions.face_mesh

hands = mp_hands.Hands(max_num_hands=2)
pose = mp_pose.Pose()
face = mp_face.FaceMesh()
FACE_POINTS = [10, 234, 454, 127, 356, 6, 152]

# ---------------- FEATURE EXTRACTION ----------------
def extract_frame(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_res = hands.process(rgb)
    pose_res = pose.process(rgb)
    face_res = face.process(rgb)

    features = []

    # HANDS
    hand_feat = []
    if hand_res.multi_hand_landmarks:
        for hand_lm in hand_res.multi_hand_landmarks[:2]:
            for lm in hand_lm.landmark:
                hand_feat += [lm.x, lm.y, lm.z]
    while len(hand_feat) < 126:
        hand_feat.append(0)
    features += hand_feat

    # POSE
    pose_feat = []
    if pose_res.pose_landmarks:
        for lm in pose_res.pose_landmarks.landmark:
            pose_feat += [lm.x, lm.y, lm.z]
    while len(pose_feat) < 99:
        pose_feat.append(0)
    features += pose_feat

    # FACE
    face_feat = []
    if face_res.multi_face_landmarks:
        face_lm = face_res.multi_face_landmarks[0]
        for idx in FACE_POINTS:
            lm = face_lm.landmark[idx]
            face_feat += [lm.x, lm.y, lm.z]
    while len(face_feat) < 21:
        face_feat.append(0)
    features += face_feat

    return np.array(features, dtype=np.float32), hand_res

# ---------------- WORD PREDICTION ----------------
def predict_words(sequence):
    raw_preds = []
    if len(sequence) < WINDOW_SIZE:
        last = sequence[-1]
        while len(sequence) < WINDOW_SIZE:
            sequence.append(last)

    for start in range(0, len(sequence) - WINDOW_SIZE + 1, STRIDE):
        chunk = sequence[start:start + WINDOW_SIZE]
        seq = add_velocity(np.array(chunk))
        seq = torch.tensor(seq).unsqueeze(0).float().to(device)
        with torch.no_grad():
            pred = model(seq)
            prob = torch.softmax(pred, dim=1)
            conf, cls = torch.max(prob, 1)
        word = labels[cls.item()]
        confidence = float(conf)
        if confidence > CONF_THRESHOLD:
            raw_preds.append(word)

    # remove duplicates
    final = []
    for w in raw_preds:
        if len(final) == 0 or final[-1] != w:
            final.append(w)
    return final[:MAX_WORDS]

# ---------------- CAMERA STREAM ----------------
def generate_frames():
    global is_recording, no_hands_counter, recorded_sequence, last_prediction_time
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        frame_small = cv2.resize(frame, (320, 240))
        feat, hand_res = extract_frame(frame_small)
        hands_visible = hand_res.multi_hand_landmarks is not None

        if hands_visible:
            if not is_recording:
                recorded_sequence = []
            is_recording = True
            no_hands_counter = 0
            recorded_sequence.append(feat)
        else:
            no_hands_counter += 1
            if no_hands_counter > NO_HANDS_LIMIT and is_recording:
                is_recording = False
                if len(recorded_sequence) >= 25:
                    words = predict_words(recorded_sequence)
                    if len(words) == 1:
                        sentence = sentence_map.get(words[0], words[0])
                    else:
                        sentence = builder.build_from_words(words)

                    if time.time() - last_prediction_time > COOLDOWN:
                        socketio.emit("new_speech", {"text": sentence, "sender": "deaf"})
                        speak(sentence)
                        last_prediction_time = time.time()
                recorded_sequence = []

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
        )

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("SignCare Server Started")
    threading.Thread(target=vosk_listener, daemon=True).start()
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)