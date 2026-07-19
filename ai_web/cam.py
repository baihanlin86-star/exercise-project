import cv2
import sys
import numpy as np

# --- 1. 角度計算函式 ---
def calculate_angle(a, b, c):
    a = np.array(a) # 點 1
    b = np.array(b) # 頂點 (關節處)
    c = np.array(c) # 點 2
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    return angle

# --- 2. 標準載入區 ---
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    print("✅ MediaPipe 載入成功！")
except Exception as e:
    print(f"❌ 載入失敗：{e}")
    sys.exit()

# --- 3. 初始化設定 ---
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# 🔗 請確保 DroidCam IP 正確
url = "http://10.0.39.148:4747/video"
cap = cv2.VideoCapture(url)

# 🛠️ 動作配置字典 (你想測什麼角度，就在這裡定義)
# 格式：[點1, 頂點, 點2]
JOINT_CONFIG = {
    "Left Elbow": [11, 13, 15],   # 左手肘 (肩-肘-腕)
    "Left Shoulder": [13, 11, 23], # 左肩外展 (肘-肩-髖) -> 臥推看這個
    "Left Knee": [23, 25, 27]     # 左膝蓋 (髖-膝-踝) -> 深蹲看這個
}

print("🚀 啟動 AI 健身監測... 按 'q' 退出")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # 影像處理
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)
    h, w, _ = frame.shape # 取得畫面寬高，用來轉換座標

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # 繪製原本的骨架線條
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

        # --- 核心邏輯：遍歷我們要偵測的角度 ---
        for name, points in JOINT_CONFIG.items():
            try:
                # 抓取對應的座標 (x, y)
                p1 = [landmarks[points[0]].x, landmarks[points[0]].y]
                p2 = [landmarks[points[1]].x, landmarks[points[1]].y] # 頂點
                p3 = [landmarks[points[2]].x, landmarks[points[2]].y]

                # 計算角度
                angle = calculate_angle(p1, p2, p3)

                # 將座標轉換為影像上的像素位置 (用來印文字)
                # 我們把文字印在頂點 (p2) 的位置
                text_pos = tuple(np.multiply(p2, [w, h]).astype(int))

                # 在螢幕上印出角度
                cv2.putText(
                    frame, 
                    f"{int(angle)}", 
                    text_pos, 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA
                )
                
                # --- 臥推安全警示 (範例) ---
                if name == "Left Shoulder" and angle > 80:
                    cv2.putText(frame, "WIDE!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

            except Exception as e:
                pass

    cv2.imshow('AI Fitness Expert', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()