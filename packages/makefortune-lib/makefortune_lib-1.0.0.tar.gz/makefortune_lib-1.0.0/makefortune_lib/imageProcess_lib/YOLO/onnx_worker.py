"""
要求: cuda, cudnn, onnxruntime, onnxruntime-gpu 相互适配, 否则可用 cpu
"""
import onnxruntime as ort
from typing import Dict, List, Union, Tuple
import numpy as np
import cv2


def show(img, window_name, src=None, flag=True, max_size=800):
    # 状态变量
    drawing = False
    moving = False
    ix, iy = -1, -1
    rects = []  # 存储所有矩形 [(x1,y1,x2,y2)]
    selected_rect = None
    base_point = None
    original_img = img.copy()  # 保存原始图像

    def draw_callback(event, x, y, flags, param):
        nonlocal drawing, moving, ix, iy, selected_rect, base_point, src
        if event == cv2.EVENT_LBUTTONDBLCLK:
            width = x
            height = y
            if src is not None:
                print('x坐标:', x, 'y坐标:', y, '高度:', src[height, width], '灰度值:', img[height, width]
                      )
            else:
                print('x坐标:', x, 'y坐标:', y, '灰度值:', img[height, width]
                      )
        # 绘制新矩形模式
        elif event == cv2.EVENT_LBUTTONDOWN:
            # 检查是否点击了已有矩形
            for i, (x1, y1, x2, y2) in enumerate(rects):
                if x1 <= x <= x2 and y1 <= y <= y2:
                    selected_rect = i
                    moving = True
                    ix, iy = x, y
                    return

            # 设置基准点模式(按住SHIFT)
            if flags & cv2.EVENT_FLAG_SHIFTKEY:
                base_point = (x, y)
                print(f"基准点设置为: ({x}, {y})")
                update_display()
                return

            # 开始绘制新矩形
            drawing = True
            ix, iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:  # 绘制新矩形中
                display_img = original_img.copy()
                draw_all_rects(display_img)
                cv2.rectangle(display_img, (ix, iy), (x, y), (0, 0, 255), 2)

                cv2.imshow(window_name, display_img)

            elif moving and selected_rect is not None:  # 移动矩形中
                dx, dy = x - ix, y - iy
                ix, iy = x, y
                # 更新矩形位置
                x1, y1, x2, y2 = rects[selected_rect]
                rects[selected_rect] = (x1 + dx, y1 + dy, x2 + dx, y2 + dy)

                # 计算偏移量
                if base_point:
                    offset_x = (x1 + dx) - base_point[0]
                    offset_y = (y1 + dy) - base_point[1]
                    print(f"偏移量x,y: ,{offset_x},{offset_y}")

                update_display()
        elif event == cv2.EVENT_LBUTTONUP:
            if drawing:
                drawing = False
                if ix == x or iy == y:
                    pass
                else:
                    rects.append((min(ix, x), min(iy, y), max(ix, x), max(iy, y)))

                update_display()
            elif moving:
                moving = False
                selected_rect = None

    def draw_all_rects(display_img):
        for i, (x1, y1, x2, y2) in enumerate(rects):
            color = (0, 255, 0) if i == selected_rect else (0, 0, 255)
            cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 5)
            cv2.putText(display_img, f"{abs(x2 - x1)}x{abs(y2 - y1)}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
        if base_point:
            cv2.circle(display_img, base_point, 5, (255, 0, 0), -1)

    def update_display():
        display_img = original_img.copy()
        draw_all_rects(display_img)
        cv2.imshow(window_name, display_img)

    # 初始化窗口
    if flag:
        cv2.namedWindow(str(window_name), cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(str(window_name), draw_callback, )
        # 计算缩放比例
        h, w = img.shape[:2]
        scale = min(max_size / max(h, w), 1.0)

        # 计算新尺寸
        new_w = int(w * scale)
        new_h = int(h * scale)
        cv2.resizeWindow(str(window_name), new_w, new_h)
        update_display()
        cv2.waitKey(0)


def draw_defect_pts(img, ret, name='', ):
    # pts_list = defect_ret['defect_pts_list']
    pad = 0
    if img.ndim == 2 or img.shape[-1] == 1:
        draw = cv2.merge((img, img, img))
        # ret = cv2.rectangle(np.stack([img, img, img], axis=-1), (pts[0, 0], pts[0, 1]), (pts[1, 0], pts[1,1]), (255, 0, 0), 4)
    else:
        draw = img

    ih, iw = draw.shape[:2]
    for i, one_rect in enumerate(ret['pts_list']):
        np_pred = [one_rect[0][0], one_rect[0][1], one_rect[1][0], one_rect[1][1], ret['conf_list'][i],
                   ret['lab_list'][i]]
        x0, y0, x1, y1, pred_thresh, pred_cls = np_pred[:6]
        w_, h_ = x1 - x0, y1 - y0
        x0, y0 = max(0, int(x0) - pad), max(0, int(y0) - pad)
        # x1, y1 = min(iw, int(x + w) + pad), min(ih, int(y + h) + pad)
        x1, y1 = min(iw, int(x1) + pad), min(ih, int(y1) + pad)
        cv2.rectangle(draw, (x0, y0), (x1, y1), (0, 0, 255), 1)
        # cv2.putText(draw, str(int(pred_cls)), (x0, max(0, y0 - 2)), 0, 0.5, [255, 0, 0], thickness=1,
        #             lineType=cv2.LINE_AA)
        cv2.putText(draw, str(round(pred_thresh, 3)), (x0 + 10, max(0, y0 - 2)), 0, 0.5, [0, 0, 255], thickness=1,
                    lineType=cv2.LINE_AA)
        # -------------------------
        # cv2.putText(draw, str(round(h_ * 0.0025, 2)), (x0 + 10, max(0, y0 - 2)), 0, 0.5, [0, 0, 255], thickness=1,
        #             lineType=cv2.LINE_AA)
        #
        # cv2.putText(draw, str(int(pred_cls)), (x0, max(0, y0 - 2)), 0, 0.5, [255, 0, 0], thickness=1,
        #             lineType=cv2.LINE_AA)
    # cv2.putText(draw, name.split('.')[0] if name != '' else '', (5, 16), 0, 0.5, [0, 0, 255],
    #             thickness=1,
    #             lineType=cv2.LINE_AA)
    # cv2.imwrite(save_path, draw)

    return draw


class FasterRcnn_onnx:
    pass


class Yolo_onnx:
    def __init__(self, model_path: str, task: str = 'detect', device: str = 'cuda',
                 size=(640, 640)):
        """
        初始化YOLO ONNX模型
        """
        self.model_path = model_path
        self.task = task.lower()
        self.device = device.lower()
        if self.task not in ['detect', 'segment', 'pose', 'classify']:
            raise ValueError(f"Unsupported task: {self.task}")
        providers = ['CUDAExecutionProvider'] if self.device == 'cuda' else [
            'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]
        self.input_height, self.input_width = size
        self.target_size = (self.input_height, self.input_width)
        self.names = self.session.get_modelmeta().custom_metadata_map["names"]
        self.nc = len(eval(self.names).keys())
        print(self.nc)
        self._get_keypoint_count()

    def preprocess(self, bgr_frame: np.ndarray) -> np.ndarray:
        """
        图像预处理
        :param image: 输入图像(BGR格式)
        :return: 预处理后的图像
        """
        # Convert the image color space from BGR to RGB
        img = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        img, pad = self._letterbox(img, (self.input_width, self.input_height))
        # Normalize the image data by dividing it by 255.0
        image_data = np.array(img) / 255.0
        # Transpose the image to have the channel dimension as the first dimension
        image_data = np.transpose(image_data, (2, 0, 1))  # Channel first
        # Expand the dimensions of the image data to match the expected input shape
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)

        return image_data, pad

    def inference(self, input: np.ndarray) -> List[np.ndarray]:
        """
        执行推理
        :param input_tensor: 预处理后的输入张量
        :return: 模型输出
        """
        outputs = self.session.run(self.output_names, {self.input_name: input})
        return outputs

    def postprocess(self, preds, target_shape, src_shape, **kwargs):
        """后处理，根据任务类型处理输出"""
        if self.task == 'detect':
            return self._postprocess_detect(preds, target_shape, src_shape, **kwargs)
        elif self.task == 'segment':
            return self._postprocess_segment(preds, target_shape, src_shape, **kwargs)
        elif self.task == 'classify':
            return self._postprocess_classify(preds)
        elif self.task == 'pose':
            return self._postprocess_pose(preds, target_shape, src_shape, **kwargs)

    def _postprocess_detect(self, preds: List[np.ndarray], target_shape, src_shape, **kwargs) -> np.ndarray:
        conf = kwargs.get('conf')
        iou = kwargs.get('iou')
        ret_dict = {
            'pts_list': [],
            'lab_list': [],
            'conf_list': []
        }
        # Transpose and squeeze the output to match the expected shape
        outputs = np.transpose(np.squeeze(preds[0]))
        pad = kwargs.get('pad')
        # Get the number of rows in the outputs array
        rows = outputs.shape[0]

        # Lists to store the bounding boxes, scores, and class IDs of the detections
        boxes = []
        scores = []
        class_ids = []
        # Calculate the scaling factors for the bounding box coordinates
        gain = min(target_shape[0] / src_shape[0][0], target_shape[1] / src_shape[0][1])
        outputs[:, 0] -= pad[1]
        outputs[:, 1] -= pad[0]
        # Iterate over each row in the outputs array
        for i in range(rows):
            # Extract the class scores from the current row
            classes_scores = outputs[i][4:]

            # Find the maximum score among the class scores
            max_score = np.amax(classes_scores)

            # If the maximum score is above the confidence threshold
            if max_score >= conf:
                # Get the class ID with the highest score
                class_id = np.argmax(classes_scores)
                # Extract the bounding box coordinates from the current row
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]

                # Calculate the scaled coordinates of the bounding box
                left = int((x - w / 2) / gain)
                top = int((y - h / 2) / gain)
                width = int(w / gain)
                height = int(h / gain)

                # Add the class ID, score, and box coordinates to the respective lists
                class_ids.append(class_id)
                scores.append(max_score)
                boxes.append([left, top, width, height])

        # 按类别分组执行NMS
        unique_classes = set(class_ids)
        final_indices = []
        for cls in unique_classes:
            cls_mask = [i for i, c in enumerate(class_ids) if c == cls]
            cls_boxes = [boxes[i] for i in cls_mask]
            cls_scores = [scores[i] for i in cls_mask]
            indices = cv2.dnn.NMSBoxes(cls_boxes, cls_scores, conf, iou)  # boxes 为x,y,w,h
            final_indices.extend([cls_mask[i] for i in indices])

        b, c, s = [], [], []
        for i in final_indices:
            # Get the box, score, and class ID corresponding to the index
            box = boxes[i]
            box_xyxy = [box[0], box[1], box[0] + box[2], box[1] + box[3]]
            score = scores[i]
            class_id = class_ids[i]
            b.append(box_xyxy)
            c.append(class_id)
            s.append(score)
        ret_dict['pts_list'].append(b)
        ret_dict['lab_list'].append(c)
        ret_dict['conf_list'].append(s)
        return ret_dict

    def _postprocess_segment(self,
                             preds,
                             target_shape,
                             src_shape,
                             **kwargs
                             ):
        ret_dict = {
            'pts_list': [],
            'lab_list': [],
            'conf_list': [],
            'xy': []
        }
        conf = kwargs.get('conf')
        iou = kwargs.get('iou')
        det_output, mask_proto = preds
        pad = kwargs.get('pad')  # yolo letterbox预处理时得到的top,left
        gain = min(target_shape[0] / src_shape[0][0], target_shape[1] / src_shape[0][1])

        # 1. 检测输出转置 [8400,116]
        detections = det_output[0].T
        # 2. 提取边界框和类别
        bboxes = detections[:, :4]  # [cx,cy,w,h]
        scores = detections[:, 4:4 + self.nc]
        mask_coeff = detections[:, 4 + self.nc:]

        # 获取最高类别置信度
        max_conf = scores.max(axis=1)
        class_ids = scores.argmax(axis=1)

        # 3. 应用置信度阈值
        conf_mask = max_conf > conf

        if not conf_mask.any():
            # 没有有效检测，返回空结果
            return {
                'pts_list': [[]],
                'lab_list': [[]],
                'conf_list': [[]],
                'xy': [[]]
            }

        bboxes = bboxes[conf_mask]
        scores = max_conf[conf_mask]
        class_ids = class_ids[conf_mask]
        mask_coeff = mask_coeff[conf_mask]

        bboxes[:, 0] -= pad[1]
        bboxes[:, 1] -= pad[0]

        # 4. 边界框坐标转换 [x1,y1,x2,y2]
        x1 = bboxes[:, 0] - bboxes[:, 2] / 2
        y1 = bboxes[:, 1] - bboxes[:, 3] / 2
        w = bboxes[:, 2]
        h = bboxes[:, 3]

        bboxes = np.stack([x1, y1, w, h], axis=1)
        bboxes /= gain  # 边界框已还原到原图
        # 5. 非极大值抑制
        final_boxes = []
        final_scores = []
        final_class_ids = []
        final_mask_coeff = []
        for cls_id in np.unique(class_ids):
            cls_mask = (class_ids == cls_id)
            cls_boxes = bboxes[cls_mask]
            cls_scores = scores[cls_mask]
            cls_mask_coeff = mask_coeff[cls_mask]

            indices = cv2.dnn.NMSBoxes(
                cls_boxes.tolist(),
                cls_scores.tolist(),
                score_threshold=conf,
                nms_threshold=iou
            )

            if len(indices) > 0:
                indices = indices.flatten()
                for i in indices:
                    boxes = [cls_boxes[i][0], cls_boxes[i][1],
                             cls_boxes[i][0] + cls_boxes[i][2], cls_boxes[i][1] + cls_boxes[i][3]]
                    final_boxes.append(boxes)
                    final_scores.append(cls_scores[i])
                    final_class_ids.append(cls_id)
                    final_mask_coeff.append(cls_mask_coeff[i])
        # 如果 NMS 后无结果
        if len(final_boxes) == 0:
            return {
                'pts_list': [[]],
                'lab_list': [[]],
                'conf_list': [[]],
                'xy': [[]]
            }

        # 掩膜生成
        proto_mask = mask_proto[0]
        # print('掩膜尺寸:', proto_mask.shape)
        c, mh, mw = proto_mask.shape
        final_mask_coeff = np.array(final_mask_coeff)
        # print('final_mask_coeff:', final_mask_coeff.shape, final_mask_coeff)
        y = proto_mask.reshape(c, -1)
        # print('y:', y.shape)
        masks = self._sigmoid(final_mask_coeff @ y)
        masks = masks.reshape(-1, mh, mw)
        # 掩膜后处理
        resized_masks = np.zeros((src_shape[0][0], src_shape[0][1], final_mask_coeff.shape[0]))
        for i, (mask, bbox) in enumerate(zip(masks, final_boxes)):
            # 调整到目标尺寸
            mask = cv2.resize(mask, (target_shape[1], target_shape[0]),
                              interpolation=cv2.INTER_LINEAR)
            # 还原到原始图像尺寸
            mask = self._crop_mask(mask, pad, src_shape[0], bbox)
            resized_masks[:, :, i] = mask

        # 将掩码转换成多边形
        resized_masks = resized_masks.transpose(2, 0, 1)
        segments = self._masks2segments(resized_masks)
        ret_dict['pts_list'].append(final_boxes)
        ret_dict['lab_list'].append(final_class_ids)
        ret_dict['conf_list'].append(final_scores)
        ret_dict['xy'].append(segments)
        return ret_dict

    def _postprocess_classify(self, preds):
        preds = preds[0] if isinstance(preds, (list, tuple)) else preds
        preds_np = np.array(preds)
        max_indices = np.argmax(preds_np, axis=1)
        print(preds_np, type(preds_np), max_indices)
        return preds_np

    def _postprocess_pose(self,
                          preds,
                          target_shape, src_shape, **kwargs,
                          ):
        conf = kwargs.get('conf')
        iou = kwargs.get('iou')
        ret_dict = {
            'pts_list': [],
            'lab_list': [],
            'conf_list': [],
            'kpts': []
        }
        # Transpose and squeeze the output to match the expected shape
        outputs = np.transpose(np.squeeze(preds[0]))
        pad = kwargs.get('pad')
        # Get the number of rows in the outputs array
        rows = outputs.shape[0]

        # Lists to store the bounding boxes, scores, and class IDs of the detections
        boxes = []
        scores = []
        class_ids = []
        kpts_lst = []
        # Calculate the scaling factors for the bounding box coordinates
        gain = min(target_shape[0] / src_shape[0][0], target_shape[1] / src_shape[0][1])
        outputs[:, 0] -= pad[1]
        outputs[:, 1] -= pad[0]
        # Iterate over each row in the outputs array
        for i in range(rows):
            # Extract the class scores from the current row
            classes_scores = outputs[i][4:4 + self.nc]

            # Find the maximum score among the class scores
            max_score = np.amax(classes_scores)

            # If the maximum score is above the confidence threshold
            if max_score >= kwargs.get('conf'):
                # Get the class ID with the highest score
                class_id = np.argmax(classes_scores)
                # Extract the bounding box coordinates from the current row
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
                kpts = outputs[i][4 + self.nc:]
                return_kpts = []
                for _idx in range(0, len(kpts), 3):
                    return_pt = (
                        int((kpts[_idx] - pad[1]) / gain), int((kpts[_idx + 1] - pad[0]) / gain), kpts[_idx + 2])
                    return_kpts.append(return_pt)
                # Calculate the scaled coordinates of the bounding box
                left = int((x - w / 2) / gain)
                top = int((y - h / 2) / gain)
                width = int(w / gain)
                height = int(h / gain)

                # Add the class ID, score, and box coordinates to the respective lists
                class_ids.append(class_id)
                scores.append(max_score)
                boxes.append([left, top, width, height])
                kpts_lst.append(return_kpts)
        # 按类别分组执行NMS
        unique_classes = set(class_ids)
        final_indices = []
        for cls in unique_classes:
            cls_mask = [i for i, c in enumerate(class_ids) if c == cls]
            cls_boxes = [boxes[i] for i in cls_mask]
            cls_scores = [scores[i] for i in cls_mask]
            indices = cv2.dnn.NMSBoxes(cls_boxes, cls_scores, conf, iou)
            final_indices.extend([cls_mask[i] for i in indices])

        b, c, s, k = [], [], [], []
        for i in final_indices:
            # Get the box, score, and class ID corresponding to the index
            box = boxes[i]
            box_xyxy = [[box[0], box[1]], [box[0] + box[2], box[1] + box[3]]]
            score = scores[i]
            class_id = class_ids[i]
            pose = kpts_lst[i]
            b.append(box_xyxy)
            c.append(class_id)
            s.append(score)
            k.append(pose)
        ret_dict['pts_list'].append(b)
        ret_dict['lab_list'].append(c)
        ret_dict['conf_list'].append(s)
        ret_dict['kpts'].append(k)
        return ret_dict

    def _crop_mask(self, mask, pad, src_shape, bbox):
        """裁剪掩膜到原始图像区域"""
        h, w = src_shape
        mh, mw = mask.shape[:2]
        mask = mask[int(pad[0]):int(mh - pad[0]),
               int(pad[1]):int(mw - pad[1])]
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
        mask = (mask > 0.5).astype(np.float32)
        output = np.zeros_like(mask)
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        x1, y1 = np.clip(x1, 0, w - 1), np.clip(y1, 0, h - 1)
        x2, y2 = np.clip(x2, 0, w), np.clip(y2, 0, h)
        output[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
        return output

    def _sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def _min_index(self, arr1: np.ndarray, arr2: np.ndarray):
        """
            该函数实现了计算两个二维点集之间最短距离对应的索引对，核心通过NumPy的广播机制和矩阵运算高效完成距离计算‌
        """
        dis = ((arr1[:, None, :] - arr2[None, :, :]) ** 2).sum(-1)
        return np.unravel_index(np.argmin(dis, axis=None), dis.shape)

    def _merge_multi_segment(self, segments):
        """
        将多个分割点集 根据最小距离连接合并
        所有分割点集之间使用一根细线连接
        Merge multiple segments into one list by connecting the coordinates with the minimum distance between each segment.
        This function connects these coordinates with a thin line to merge all segments into one.
        """
        s = []
        segments = [np.array(i).reshape(-1, 2) for i in segments]
        idx_list = [[] for _ in range(len(segments))]
        # Record the indexes with min distance between each segment
        for i in range(1, len(segments)):
            idx1, idx2 = self._min_index(segments[i - 1], segments[i])
            idx_list[i - 1].append(idx1)
            idx_list[i].append(idx2)
        # Use two round to connect all the segments
        for k in range(2):
            # Forward connection
            if k == 0:
                for i, idx in enumerate(idx_list):
                    # Middle segments have two indexes, reverse the index of middle segments
                    if len(idx) == 2 and idx[0] > idx[1]:
                        idx = idx[::-1]
                        segments[i] = segments[i][::-1, :]

                    segments[i] = np.roll(segments[i], -idx[0], axis=0)
                    segments[i] = np.concatenate([segments[i], segments[i][:1]])
                    # Deal with the first segment and the last one
                    if i in {0, len(idx_list) - 1}:
                        s.append(segments[i])
                    else:
                        idx = [0, idx[1] - idx[0]]
                        s.append(segments[i][idx[0]: idx[1] + 1])
            else:
                for i in range(len(idx_list) - 1, -1, -1):
                    if i not in {0, len(idx_list) - 1}:
                        idx = idx_list[i]
                        nidx = abs(idx[1] - idx[0])
                        s.append(segments[i][nidx:])
        return s

    def _masks2segments(self, masks, strategy: str = "all"):
        segments = []
        for x in masks.astype("uint8"):
            c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            if c:
                if strategy == "all":  # merge and concatenate all segments
                    c = (
                        np.concatenate(self._merge_multi_segment([x.reshape(-1, 2) for x in c]))
                        if len(c) > 1
                        else c[0].reshape(-1, 2)
                    )
                elif strategy == "largest":  # select largest segment
                    c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
            else:
                c = np.zeros((0, 2))  # no segments found
            segments.append(c.astype("float32"))
        return segments

    def _get_keypoint_count(self):
        output_shape = [out.shape for out in self.session.get_outputs()]
        if self.task == 'pose':
            self.nkpt = (output_shape[0][1] - 4 - self.nc) // 3

    def _letterbox(self, img: np.ndarray, new_shape: Tuple[int, int] = (640, 640)) -> Tuple[
        np.ndarray, Tuple[int, int]]:
        shape = img.shape[:2]  # current shape [height, width]
        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = (new_shape[1] - new_unpad[0]) / 2, (new_shape[0] - new_unpad[1]) / 2  # wh padding
        if shape[::-1] != new_unpad:  # resize
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return img, (top, left)

    def __call__(self, image: np.ndarray, conf=0.5, iou=0.4) -> Union[List, Dict]:
        im, pad = self.preprocess(image)
        outputs = self.inference(im)
        target_shape, src_shape = im.shape[2:], [image.shape[:2]]
        return self.postprocess(outputs, target_shape, src_shape, conf=conf, iou=iou, pad=pad)


if __name__ == '__main__':
    import os
    import time

    task = {
        0: 'detect',  # 目标检测
        1: 'segment',  # 语义分割
        2: 'classify',  # 分类
        3: 'pose',  # 关键点检测
    }
    select_task = 1
    if task[select_task] == 'detect':
        model_path = 'yolo_detect.onnx'
        imgpath = 'coco8/images/val'
        infer = Yolo_onnx(model_path=model_path, task=task[select_task])
        for path in os.listdir(imgpath):
            one_path = os.path.join(imgpath, path)
            img = cv2.imread(one_path)
            ret = infer(img)
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i]
                }
                print(one_ret)
                draw = draw_defect_pts(img, one_ret)
                show(draw, 'draw')

    elif task[select_task] == 'segment':
        model_path = r'D:\1-GUOXUAN\Code\vision_template\template\best.onnx'
        imgpath = r'D:\Data\OK\20251030\inference'
        infer = Yolo_onnx(model_path=model_path, task=task[select_task])
        for path in os.listdir(imgpath):
            one_path = os.path.join(imgpath, path)
            print('----------------------------------------------------------------------------------------------')
            print(path)
            img = cv2.imread(one_path)
            a0 = time.time()
            ret = infer(img, conf=0.5, iou=0.45)
            a1 = time.time()
            print('infer time one image:', a1 - a0)
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i],
                    'xy': ret['xy'][i]
                }
                print("lab:--", one_ret['lab_list'])

    elif task[select_task] == 'classify':
        model_path = 'yolo_classify.onnx'
        imgpath = 'animal_classify'
        infer = Yolo_onnx(model_path=model_path, task=task[select_task])
        for path in os.listdir(imgpath):
            one_path = os.path.join(imgpath, path)
            img = cv2.imread(one_path)
            ret = infer(img)
            print(ret)

    elif task[select_task] == 'pose':
        model_path = 'yolo_pose.onnx'
        imgpath = 'coco8-pose/images/val'
        infer = Yolo_onnx(model_path=model_path, task=task[select_task])
        for path in os.listdir(imgpath):
            one_path = os.path.join(imgpath, path)
            img = cv2.imread(one_path)
            ret = infer(img)
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i],
                    'kpts': ret['kpts'][i]
                }
                draw = draw_defect_pts(img, one_ret)
                for pts in one_ret['kpts']:
                    for one_pt in pts:
                        if one_pt[-1] > 0.5:
                            cv2.circle(draw, (int(one_pt[0]), int(one_pt[1])), 2, (0, 0, 255), -1)
                show(draw, 'draw')
