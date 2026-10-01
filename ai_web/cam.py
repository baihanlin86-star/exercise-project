import cv2
import sys
import time
import numpy as np
from collections import defaultdict, deque


# =========================================================
# 1. 基本設定
# =========================================================

DROIDCAM_URL = "http://10.20.30.158:4747/video"

# True：
# 使用 MediaPipe 的 3D world landmarks 算角度
#
# False：
# 使用影像上的 2D pixel 座標算角度
#
# 側面拍攝深蹲等動作時，2D 有時反而比較穩。
# 多方向運動可以嘗試 3D。
USE_3D = True

# 關節點最低可信度
VISIBILITY_THRESHOLD = 0.65

# 最近幾幀角度取中位數，降低抖動
SMOOTHING_WINDOW = 5


# =========================================================
# 2. 角度計算
# =========================================================

def calculate_angle(a, b, c):
    """
    計算 A-B-C 的夾角。
    b 是關節頂點。

    同時支援：
    2D -> [x, y]
    3D -> [x, y, z]
    """

    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    c = np.array(c, dtype=np.float32)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    # 避免除以 0
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)

    # 避免浮點誤差超出 [-1, 1]
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    angle = np.degrees(np.arccos(cosine_angle))

    return float(angle)


# =========================================================
# 3. MediaPipe
# =========================================================

try:
    import mediapipe as mp

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    print("✅ MediaPipe 載入成功")

except Exception as e:
    print(f"❌ MediaPipe 載入失敗：{e}")
    sys.exit()


# =========================================================
# 4. Pose 模型
# =========================================================

pose = mp_pose.Pose(

    # 影片不要每一幀重新 detect
    static_image_mode=False,

    # 0 = Lite
    # 1 = Full
    # 2 = Heavy / 最精準
    model_complexity=2,

    # 平滑 landmark，降低抖動
    smooth_landmarks=True,

    # 我們目前不需要人體 segmentation
    enable_segmentation=False,

    # 提高 detection 門檻
    min_detection_confidence=0.7,

    # 提高 tracking 門檻
    min_tracking_confidence=0.7
)


# =========================================================
# 5. 攝影機
# =========================================================

cap = cv2.VideoCapture(DROIDCAM_URL)

if not cap.isOpened():
    print("❌ 無法連線 DroidCam")
    sys.exit()

# 嘗試降低網路攝影機 buffer
# 某些 backend 不一定支援
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


# =========================================================
# 6. 要監控的關節
# =========================================================

# MediaPipe Pose：
#
# 11 = Left Shoulder
# 12 = Right Shoulder
# 13 = Left Elbow
# 14 = Right Elbow
# 15 = Left Wrist
# 16 = Right Wrist
# 23 = Left Hip
# 24 = Right Hip
# 25 = Left Knee
# 26 = Right Knee
# 27 = Left Ankle
# 28 = Right Ankle

JOINT_CONFIG = {

    # 肩 -> 手肘 -> 手腕
    "Left Elbow": (11, 13, 15),

    # 手肘 -> 肩膀 -> 髖
    "Left Shoulder": (13, 11, 23),

    # 髖 -> 膝 -> 腳踝
    "Left Knee": (23, 25, 27),

    # 右膝
    "Right Knee": (24, 26, 28),

    # 肩 -> 髖 -> 膝
    "Left Hip": (11, 23, 25),

    "Right Hip": (12, 24, 26)
}


# =========================================================
# 7. 每個關節建立角度歷史
# =========================================================

angle_history = defaultdict(
    lambda: deque(maxlen=SMOOTHING_WINDOW)
)


# =========================================================
# 8. FPS
# =========================================================

previous_time = time.perf_counter()


print("🚀 AI Fitness Pose Monitor 啟動")
print("按 q 離開")
print(f"目前模式：{'3D World Landmark' if USE_3D else '2D Pixel'}")


# =========================================================
# 9. 主迴圈
# =========================================================

while cap.isOpened():

    success, frame = cap.read()

    if not success:
        print("⚠️ 無法讀取攝影機畫面")
        break


    # -----------------------------------------------------
    # MediaPipe 建議 RGB
    # -----------------------------------------------------

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # MediaPipe 處理期間不需要修改影像
    rgb.flags.writeable = False

    results = pose.process(rgb)

    rgb.flags.writeable = True


    h, w, _ = frame.shape


    # -----------------------------------------------------
    # 有抓到人體
    # -----------------------------------------------------

    if results.pose_landmarks:

        landmarks = results.pose_landmarks.landmark

        world_landmarks = None

        if results.pose_world_landmarks:
            world_landmarks = results.pose_world_landmarks.landmark


        # -------------------------------------------------
        # 畫骨架
        # -------------------------------------------------

        mp_drawing.draw_landmarks(

            frame,

            results.pose_landmarks,

            mp_pose.POSE_CONNECTIONS,

            mp_drawing.DrawingSpec(
                color=(0, 255, 0),
                thickness=2,
                circle_radius=3
            ),

            mp_drawing.DrawingSpec(
                color=(0, 0, 255),
                thickness=2,
                circle_radius=2
            )
        )


        # -------------------------------------------------
        # 計算每個關節
        # -------------------------------------------------

        y_offset = 60

        for name, points in JOINT_CONFIG.items():

            id1, id2, id3 = points

            lm1 = landmarks[id1]
            lm2 = landmarks[id2]
            lm3 = landmarks[id3]


            # ---------------------------------------------
            # 可信度
            # ---------------------------------------------

            visibility = min(
                lm1.visibility,
                lm2.visibility,
                lm3.visibility
            )


            # 如果任何一個點被遮住
            if visibility < VISIBILITY_THRESHOLD:

                angle_history[name].clear()

                cv2.putText(
                    frame,
                    f"{name}: LOW CONF ({visibility:.2f})",
                    (20, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 165, 255),
                    2,
                    cv2.LINE_AA
                )

                y_offset += 25

                continue


            # ---------------------------------------------
            # 3D 模式
            # ---------------------------------------------

            if USE_3D and world_landmarks is not None:

                w1 = world_landmarks[id1]
                w2 = world_landmarks[id2]
                w3 = world_landmarks[id3]

                p1 = [w1.x, w1.y, w1.z]
                p2 = [w2.x, w2.y, w2.z]
                p3 = [w3.x, w3.y, w3.z]


            # ---------------------------------------------
            # 2D 模式
            # 重要：
            # 一定轉成 pixel 座標
            # 不可以直接拿 normalized x/y 算
            # ---------------------------------------------

            else:

                p1 = [
                    lm1.x * w,
                    lm1.y * h
                ]

                p2 = [
                    lm2.x * w,
                    lm2.y * h
                ]

                p3 = [
                    lm3.x * w,
                    lm3.y * h
                ]


            # ---------------------------------------------
            # 算角度
            # ---------------------------------------------

            raw_angle = calculate_angle(p1, p2, p3)

            if raw_angle is None:
                continue


            # ---------------------------------------------
            # Temporal smoothing
            #
            # 使用最近幾幀的 median
            # median 比平均值比較不怕突然跳點
            # ---------------------------------------------

            angle_history[name].append(raw_angle)

            smooth_angle = float(
                np.median(angle_history[name])
            )


            # ---------------------------------------------
            # 在關節附近顯示角度
            # ---------------------------------------------

            joint_position = (

                int(lm2.x * w),
                int(lm2.y * h)

            )


            cv2.circle(
                frame,
                joint_position,
                8,
                (255, 255, 0),
                -1
            )


            cv2.putText(

                frame,

                f"{smooth_angle:.1f}",

                (
                    joint_position[0] + 10,
                    joint_position[1] - 10
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                (255, 255, 255),

                2,

                cv2.LINE_AA
            )


            # ---------------------------------------------
            # 左上角資訊
            # ---------------------------------------------

            cv2.putText(

                frame,

                f"{name}: {smooth_angle:.1f} deg  conf:{visibility:.2f}",

                (20, y_offset),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                2,

                cv2.LINE_AA
            )

            y_offset += 25


            # ---------------------------------------------
            # 臥推肩膀警告
            #
            # 注意：
            # 這個 80 度只是你原本的示範值，
            # 不應該直接當醫學或健身標準。
            # ---------------------------------------------

            if name == "Left Shoulder":

                if smooth_angle > 80:

                    cv2.putText(

                        frame,

                        "SHOULDER ANGLE HIGH",

                        (50, h - 50),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.9,

                        (0, 0, 255),

                        3,

                        cv2.LINE_AA
                    )


    # -----------------------------------------------------
    # FPS
    # -----------------------------------------------------

    current_time = time.perf_counter()

    dt = current_time - previous_time

    fps = 1 / dt if dt > 0 else 0

    previous_time = current_time


    cv2.putText(

        frame,

        f"FPS: {fps:.1f}",

        (20, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 255, 0),

        2,

        cv2.LINE_AA
    )


    mode_text = "3D" if USE_3D else "2D"

    cv2.putText(

        frame,

        f"Angle mode: {mode_text}",

        (w - 180, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2,

        cv2.LINE_AA
    )


    # -----------------------------------------------------
    # 顯示畫面
    # -----------------------------------------------------

    cv2.imshow(
        "AI Fitness Expert",
        frame
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =========================================================
# 10. Clean up
# =========================================================

cap.release()

pose.close()

cv2.destroyAllWindows()