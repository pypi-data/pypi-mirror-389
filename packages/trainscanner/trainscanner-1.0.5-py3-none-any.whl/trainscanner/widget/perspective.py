import math
import numpy as np
import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from trainscanner.widget import cv2toQImage
from PyQt6.QtWidgets import QApplication
import sys


class Perspective(QLabel):
    def __init__(self):
        super().__init__()
        # 0,0は画像の中心。マウスでポイントした位置を表す数字。正方形のworkarea上で、1px単位で-500..+500で位置を指定する。
        self.point = (-75, 9)
        self.image = None
        self.expand = 1.2

    def rotation_affine(self, w, h):
        r = math.sqrt(self.point[0] ** 2 + self.point[1] ** 2)
        cosine = self.point[0] / r
        sine = self.point[1] / r
        rh = abs(h * cosine) + abs(w * sine)
        rw = abs(h * sine) + abs(w * cosine)
        self.rh, self.rw = int(rh), int(rw)
        halfw, halfh = w / 2, h / 2
        self.R = np.matrix(
            (
                (cosine, sine, -cosine * halfw - sine * halfh + rw / 2),
                (-sine, cosine, sine * halfw - cosine * halfh + rh / 2),
            )
        )
        return r

    def paintEvent(self, event):
        if self.image is None:
            return

        # まずpointを極座標に変換する。
        theta = math.atan2(self.point[1], self.point[0])

        # 画面の右端は固定し、
        # 右から1/4の部分での収縮の大きさをrにする。
        # これで、4点の座標をとりあえず決めて、warpPerspectiveにもっている。
        h, w = self.image.shape[:2]
        r = self.rotation_affine(w, h)
        pts1 = np.float32([(w, 0), (w, h), (w * 3 // 4, r), (w * 3 // 4, h - r)])
        print(self.R)
        pts2 = (
            np.array(
                [
                    (w, 0, 1),
                    (w, h, 1),
                    (w - (w * self.expand // 4), 0, 1),
                    (w - (w * self.expand // 4), h, 1),
                ]
            )
            @ self.R.T
        ).astype(np.float32)
        print(pts1.shape, pts2.shape)

        # OpenCVのgetPerspectiveTransformはfloat32型が必要
        pts1 = pts1.astype(np.float32)
        pts2 = pts2.astype(np.float32)

        M = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(self.image, M, (int(w * self.expand), h))
        print(warped.shape)
        # なぜ何も表示されない?
        cv2.imshow("warped", warped)
        cv2.waitKey(1)
        return


def main():

    import cv2
    from trainscanner.video import video_loader_factory

    vl = video_loader_factory(
        "/Users/matto/Dropbox/ArtsAndIllustrations/Stitch tmp2/TrainScannerWorkArea/C00015 ShizuTetsu2/C0015.MP4"
    )
    app = QApplication(sys.argv)
    window = Perspective()
    while True:
        frame = vl.next()
        if frame is None:
            break

        # app = QApplication(sys.argv)
        window.image = frame
        window.paintEvent(None)
    cv2.destroyAllWindows()
    # window.show()
    # sys.exit(app.exec())


if __name__ == "__main__":
    main()
