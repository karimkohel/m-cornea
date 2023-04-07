import cv2
import mediapipe as mp
import numpy as np
mp_face_mesh = mp.solutions.face_mesh

class CorneaReader():
    """Class for reading the cornea location and deriving whatever values are needed from it
    """

    LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    RIGHT_EYE = [133, 33, 7, 163, 144, 145, 153, 154, 155, 173, 157, 158, 159, 160, 161, 246]
    LEFT_IRIS = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]

    def __init__(self) -> None:
        """Start the facemesh solution and be ready to read eye values

        """
        self.faceMesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.data = None

    def readEyes(self, frame: np.array) -> list[np.array]:
        """Method to derive all eye points needed from a frame

        Input:
        -------
        frame: required, numpy array representing the camera frame

        Returns:
        ---------
        frame: the same input frame after processing and applying shapes to visualize points
        leftIrisDistances: a numpy array containing the Euclidean distances from the left eye iris to all left eye points
        rightIrisDistances: a numpy array containing the Euclidean distances from the right eye iris to all right eye points
        middleEyeDistance: the distance between the closest points of each eye

        Output Format:
        --------------
        frame, (left, right, middle)
        """

        frame = cv2.flip(frame, 1)
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imgHeigh, imgWidth = frame.shape[:2]
        results = self.faceMesh.process(frameRGB)

        if results.multi_face_landmarks:
            meshPoints = np.array([np.multiply([p.x, p.y], [imgWidth, imgHeigh]).astype(int) for p in results.multi_face_landmarks[0].landmark])

            (leftCX, leftCY), leftRadius = cv2.minEnclosingCircle(meshPoints[self.LEFT_IRIS])
            (rightCX, rightCY), rightRadius = cv2.minEnclosingCircle(meshPoints[self.RIGHT_IRIS])
            leftCenter = np.array([leftCX, leftCY], dtype=np.int32)
            rightCenter = np.array([rightCX, rightCY], dtype=np.int32)

            eyeLandmarks = np.concatenate((meshPoints[self.LEFT_EYE], meshPoints[self.RIGHT_EYE]))

            leftIrisDistances = np.linalg.norm(meshPoints[self.LEFT_EYE] - leftCenter, axis=1)
            rightIrisDistances = np.linalg.norm(meshPoints[self.RIGHT_EYE] - rightCenter, axis=1)
            middleEyeDistance = np.linalg.norm(meshPoints[self.RIGHT_EYE[0]] - meshPoints[self.LEFT_EYE[0]])

            for eyePoint in eyeLandmarks:
                cv2.circle(frame, eyePoint, 1, (255,0,0), 1)

            for eyePoint in meshPoints[self.LEFT_EYE]:
                cv2.line(frame, eyePoint, leftCenter, (0, 255,255), 1)

            cv2.line(frame, meshPoints[self.RIGHT_EYE[0]], meshPoints[self.LEFT_EYE[0]], (100, 100, 255), 1)
            cv2.circle(frame, leftCenter, 1, (0,255,0), 1)
            cv2.circle(frame, rightCenter, 1, (0,255,0), 1)

            allDists = np.concatenate((leftIrisDistances, rightIrisDistances))
            allDists = np.append(allDists, middleEyeDistance)
            if not type(self.data) is np.ndarray:
                self.data = allDists
            else:
                self.data = np.vstack([self.data, allDists])
            print(self.data)

            return frame, leftIrisDistances, rightIrisDistances, middleEyeDistance
        return frame, None, None, None

        def __cropEye(self, frame: np.array) -> np.array:
            pass


    def __del__(self) -> None:
        self.faceMesh.close()