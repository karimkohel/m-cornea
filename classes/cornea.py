import cv2
import mediapipe as mp
import numpy as np
import os
import pyautogui


class CorneaReader():
    """Class for reading the cornea location and deriving whatever values are needed from it
    """

    LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    RIGHT_EYE = [133, 33, 7, 163, 144, 145, 153, 154, 155, 173, 157, 158, 159, 160, 161, 246]
    LEFT_IRIS_CENTER = 473
    RIGHT_IRIS_CENTER = 468

    EYESTRIP = [27, 28, 56, 190, 243, 112, 26, 22, 23, 24, 110, 25, 130, 247, 30, 29, 257, 259, 260, 467, 359, 255, 339, 254, 253, 252, 256, 341, 463, 414, 286, 258]
    TARGET = [40, 130]

    def __init__(self) -> None:
        """Start the facemesh solution and be ready to read eye values & fetch eye images

        """
        mp_face_mesh = mp.solutions.face_mesh
        self.faceMesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.data = None

    def readEyes(self, frame: np.ndarray, saveDir: str = None) -> np.ndarray:
        """Method to derive all eye points needed from a frame

        the method saves the eye distances as the first 33 elements of the data array, the xy labels for mouse as the 34th and 35th elements, while the rest is the image data

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
        mousePos = pyautogui.position()
        frame = cv2.flip(frame, 1)
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imgHeigh, imgWidth = frame.shape[:2]
        results = self.faceMesh.process(frameRGB)

        if results.multi_face_landmarks:
            meshPoints = np.array([np.multiply([p.x, p.y], [imgWidth, imgHeigh]).astype(int) for p in results.multi_face_landmarks[0].landmark])

            frame = self.__visualize(frame, meshPoints, meshPoints[self.LEFT_IRIS_CENTER], meshPoints[self.RIGHT_IRIS_CENTER])
            croppedFrame = self.__cropEye(frame, meshPoints)

            leftIrisDistances = np.linalg.norm(meshPoints[self.LEFT_EYE] - meshPoints[self.LEFT_IRIS_CENTER], axis=1)
            rightIrisDistances = np.linalg.norm(meshPoints[self.RIGHT_EYE] - meshPoints[self.RIGHT_IRIS_CENTER], axis=1)
            middleEyeDistance = np.linalg.norm(meshPoints[self.RIGHT_EYE[0]] - meshPoints[self.LEFT_EYE[0]])
            eyesMetrics = np.concatenate((leftIrisDistances, rightIrisDistances, [middleEyeDistance]))

            if saveDir:
                self.__saveDataArray(eyesMetrics, croppedFrame, mousePos, saveDir)

            croppedFrame = self.resizeAspectRatio(croppedFrame)
            
            return (eyesMetrics, croppedFrame), frame
        
        croppedFrame = frame
        return None, frame

    def __visualize(self, frame: np.ndarray, meshPoints: np.ndarray, leftCenter: np.ndarray, rightCenter: np.ndarray) -> np.ndarray:
        """private method to visualize gathered eye data on the current frame"""

        cv2.circle(frame, leftCenter, 1, (0,255,0), 3)
        cv2.circle(frame, rightCenter, 1, (0,255,0), 3)

        return frame

    def __cropEye(self, frame: np.ndarray, meshPoints: np.ndarray) -> np.ndarray:
        """private method to take in the entire frame and crop the eyestrip with max enclosure"""
        eyeStripCoordinates = meshPoints[self.EYESTRIP]
        maxX, maxY = np.amax(eyeStripCoordinates, axis=0)
        minX, minY = np.amin(eyeStripCoordinates, axis=0)
        frame = frame[minY:maxY, minX:maxX]
        return frame


    def __saveDataArray(self, eyesMetrics: np.ndarray, croppedFrame: np.ndarray, mousePos: list[int], saveDir: str) -> None:
        """private method that would save data arrays to memory based on input to read eyes method and current data index"""
        i = 0
        try:
            prevDataFiles = os.listdir(f"data/{saveDir}")
            i = len(prevDataFiles)
        except FileNotFoundError:
            os.mkdir(f"data/{saveDir}")
        np.savez(f"data/{saveDir}/{i}", eyesMetrics=eyesMetrics, croppedFrame=croppedFrame, mousePos=mousePos)

    @staticmethod
    def preProcess(dataDir: str) -> np.ndarray:
        """static method to load the image and metrics data from a given directory"""
        filesPath = f"data/{dataDir}/"
        samplesFilesNames = os.listdir(filesPath)
        numOfSamples = len(samplesFilesNames)
        eyesMetrics = np.zeros((numOfSamples, 33))
        frames = np.zeros((numOfSamples, 40, 120))
        mousePos = np.zeros((numOfSamples, 2))

        for i, file in enumerate(samplesFilesNames):
            file = np.load(filesPath+file)
            eyesMetrics[i] = file['eyesMetrics']
            frames[i] = cv2.resize(file['croppedFrame'], (120, 40))
            mousePos[i] = file['mousePos']

        print(frames.shape)

        return (eyesMetrics, frames, mousePos)

    def __del__(self) -> None:
        self.faceMesh.close()


    def resizeAspectRatio(self, image):
        widthPerc = 0
        heightPerc = 0
        

        heightPerc = self.TARGET[0] - image.shape[0]
        widthPerc = self.TARGET[1] - image.shape[1]

        heightPerc = heightPerc * 100 / self.TARGET[0]
        widthPerc = widthPerc * 100 / self.TARGET[1]

        if heightPerc < widthPerc:
            scale_percent = heightPerc

        else:
            scale_percent = widthPerc        

        width = image.shape[1] + int(self.TARGET[1] * scale_percent / 100)
        height = image.shape[0] + int(self.TARGET[0] * scale_percent / 100)
        dim = (width, height)
        image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

        image = self.paddingRestOfImage(image)   
        
        return image
    
    def paddingRestOfImage(self, image):
            
        # Get the current size of the image
        current_size = image.shape[:2]

        # Compute the amount of padding needed
        padding_width = self.TARGET[1] - current_size[1]
        padding_height = self.TARGET[0] - current_size[0]
        
        image = cv2.copyMakeBorder(image,
                                top=0,
                                bottom=padding_height,
                                left=0,
                                right=padding_width,
                                borderType=cv2.BORDER_CONSTANT,
                                value=(0, 0, 0))
        return image
