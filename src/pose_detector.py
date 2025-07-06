import cv2
import mediapipe as mp

class MediaPipePoseDetector:
    def __init__(self, static_mode=False, model_complexity=1, smooth_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.keypoints_map = {landmark.name: landmark.value for landmark in self.mp_pose.PoseLandmark}


    def detect_pose(self, image):
        h, w, _ = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)

        keypoints = []
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                keypoints.append((landmark.x, landmark.y, landmark.z, landmark.visibility))
        
        return keypoints, results.pose_landmarks

    def draw_landmarks(self, image, pose_landmarks):
        if pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image,
                pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )

    def get_landmark_index(self, landmark_name):
        return self.keypoints_map.get(landmark_name.upper())