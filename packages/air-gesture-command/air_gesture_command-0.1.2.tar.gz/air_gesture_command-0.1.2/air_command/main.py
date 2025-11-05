import cv2
import mediapipe as mp
import pyautogui
import time
import subprocess

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky finger
thumb_tip = 4  # Thumb tip

cap = cv2.VideoCapture(0)
last_action_time = 0
cooldown = 1  # seconds

def count_fingers(hand_landmarks):
    fingers = []

    thumb_tip_x = hand_landmarks.landmark[thumb_tip].x
    thumb_below_x = hand_landmarks.landmark[thumb_tip - 1].x

    fingers.append(1 if thumb_tip_x < thumb_below_x else 0)

    for tip in finger_tips:
        fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y else 0)

    return fingers.count(1)

def change_volume(direction, steps=2):
    for _ in range(steps):
        if direction == "up":
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)   --100%"])
        elif direction == "down":
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10) --100%"])

def main():
    global last_action_time
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        current_finger_count = None

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                current_finger_count = count_fingers(hand_landmarks)
                now = time.time()

                if now - last_action_time > cooldown:
                    if current_finger_count == 0:
                        pyautogui.press('space')
                        print("⏸ Pause Command Sent")
                        last_action_time = now

                    elif current_finger_count == 1:
                        pyautogui.press('space')
                        print("▶ Play Command Sent")
                        last_action_time = now

                    elif current_finger_count == 2:
                        change_volume("up")
                        print("🔊 Volume Up")
                        last_action_time = now

                    elif current_finger_count == 3:
                        change_volume("down")
                        print("🔉 Volume Down")
                        last_action_time = now

                    elif current_finger_count == 4:
                        pyautogui.press('right')
                        print("⏩ Seek Forward")
                        last_action_time = now

                    elif current_finger_count == 5:
                        pyautogui.press('left')
                        print("⏪ Seek Backward")
                        last_action_time = now

        cv2.imshow("YouTube Gesture Controller (Mac)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
