import glob
import os
import sys
import cv2
from PIL import Image

# pytorch版本需要源码路径
ROOT_PATH = r'C:\Users\yiche\Desktop\2_Dihuge_Projects_code\Deeplearning\ultralytics_main_20250702'
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)
from ultralytics.nn.autobackend import AutoBackend
from ultralytics.data.augment import LetterBox
from typing import List, Union
import torch
import numpy as np
from ultralytics.utils import ops
import json


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
        # cv2.putText(draw, str(round(pred_thresh, 3)), (x0 + 10, max(0, y0 - 2)), 0, 0.5, [0, 0, 255], thickness=1,
        #             lineType=cv2.LINE_AA)
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


# 将推理结果写入原json文件 使用labelme打开对比检测框与标注框
def write_inferret2json(labels, pts, image_name, json_dir):
    json_path = json_dir + os.sep + image_name
    if os.path.exists(json_path):
        print(json_path)
        json_dict = json.load(open(json_path))
        shapes = json_dict['shapes']
        for l, p in zip(labels, pts):
            one_dict = {
                "label": str(l + 50),
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {},
                "points": p,
            }
            shapes.append(one_dict)
        json_dict['shapes'] = shapes
        print(json_dict)
        json.dump(json_dict, open(json_path, 'w'))


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


class BaseWorker(object):
    def __init__(self):
        pass

    def preprocess(self, im: Union[torch.Tensor, List[np.ndarray]]) -> torch.Tensor:
        """
        Prepare input image before inference.

        Args:
            im (torch.Tensor | List[np.ndarray]): Images of shape (N, 3, H, W) for tensor, [(H, W, 3) x N] for list.

        Returns:
            (torch.Tensor): Preprocessed image tensor of shape (N, 3, H, W).
        """
        """Convert input images to model-compatible tensor format with appropriate normalization."""
        not_tensor = not isinstance(im, torch.Tensor)
        if not_tensor:
            im = np.stack([self.letterbox(image=x) for x in im])
            if im.shape[-1] == 3:
                im = im[..., ::-1]  # BGR to RGB
            im = im.transpose((0, 3, 1, 2))  # BHWC to BCHW, (n, 3, h, w)
            im = np.ascontiguousarray(im)  # contiguous
            im = torch.from_numpy(im)
        im = im.to(self.device[0])
        im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
        if not_tensor:
            im /= 255  # 0 - 255 to 0.0 - 1.0
        return im

    def postprocess(self, preds, target_shape, src_shape, **kwargs):
        return ops.non_max_suppression(
            preds,
            kwargs.get('conf'),
            kwargs.get('iou'),
            max_det=300,
            nc=0 if self.task == "detect" else len(self.model.names)
        )

    def ret2pts_list(self, ret):
        pts_list = []
        lab_list = []
        conf_list = []
        for i in range(len(ret)):  # 考虑多张图片的情况
            if isinstance(ret[i], torch.Tensor):
                one_ret = ret[i].cpu().numpy()
            else:
                one_ret = ret[i]
            one_pts_list = []
            one_lab_list = []
            one_conf_list = []
            for one_list in one_ret:
                pts = (
                    (float(one_list[0]), float(one_list[1])),
                    (float(one_list[2]), float(one_list[3]))
                )
                one_pts_list.append(np.array(pts))
                one_lab_list.append(int(one_list[5]))
                one_conf_list.append(round(float(one_list[4]), 2))

            pts_list.append(one_pts_list)
            lab_list.append(one_lab_list)
            conf_list.append(one_conf_list)

        ret_dict = {
            'pts_list': pts_list,
            'lab_list': lab_list,
            'conf_list': conf_list
        }
        return ret_dict  # 三维列表


class Yolo_torch(BaseWorker):
    def __init__(self, weight_path='', workers=0, imgsz=512, conf=0.2, iou=0.5, batch=1, save=False, half=False,
                 device='cuda:0', task='detect'):
        self.task = task.lower()
        assert self.task in ['detect', 'segment', 'classify', 'pose'], \
            f"Unsupported task: {task}, must be one of ['detect','segment','classify','pose']"
        self.device = torch.device(device) if torch.cuda.is_available() else torch.device("cpu"),
        self.imgsz = imgsz
        self.kwargs = \
            {
                'workers': workers,
                'imgsz': imgsz,
                'conf': conf,
                'batch': batch,
                'save': save,
                'device': self.device[0],
                'iou': iou,
                'half': half
            }
        self.model = self.setup_model(weight_path)

        same_shapes = False
        self.letterbox = LetterBox(new_shape=(self.imgsz, self.imgsz), auto=same_shapes and self.model.pt,
                                   stride=self.model.stride)
        if self.task == 'classify':
            self.transforms = self.model.model.transforms
        warmimg = np.ones((640, 640, 3), dtype=np.uint8)  # 预热模型
        print(self.model.names)
        self([warmimg])
        del warmimg
        print('model init done')

    def setup_model(self, model, verbose=False):
        """Initialize YOLO model with given parameters and set it to evaluation mode."""
        self.model = AutoBackend(weights=model,
                                 device=self.device[0],
                                 dnn=False,
                                 fp16=self.kwargs.get('half', False),
                                 batch=self.kwargs.get('batch', 1),
                                 fuse=True,
                                 verbose=verbose,
                                 )
        self.model.to(self.device[0])
        self.model.eval()
        return self.model

    def preprocess(self, im: Union[torch.Tensor, List[np.ndarray]]) -> torch.Tensor:
        """
        Prepare input image before inference.

        Args:
            im (torch.Tensor | List[np.ndarray]): Images of shape (N, 3, H, W) for tensor, [(H, W, 3) x N] for list.

        Returns:
            (torch.Tensor): Preprocessed image tensor of shape (N, 3, H, W).
        """
        """Convert input images to model-compatible tensor format with appropriate normalization."""
        if self.task == 'classify':
            if not isinstance(im, torch.Tensor):
                im = torch.stack(
                    [self.transforms(Image.fromarray(cv2.cvtColor(x, cv2.COLOR_BGR2RGB))) for x in im], dim=0
                )
            im = (im if isinstance(im, torch.Tensor) else torch.from_numpy(im)).to(self.model.device)
            return im.half() if self.model.fp16 else im.float()  # Convert uint8 to fp16/32
        else:
            return super().preprocess(im)

    def inference(self, im):
        """Runs inference on a given image using the specified model and arguments."""
        return self.model(im, augment=False, visualize=False, embed=None)

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

    def _postprocess_detect(self, preds, target_shape, src_shape, **kwargs):
        preds = super().postprocess(preds, target_shape, src_shape, **kwargs)
        new_preds = []
        for pred, orig_img_shape, in zip(preds, src_shape):
            pred[:, :4] = ops.scale_boxes(target_shape, pred[:, :4], orig_img_shape)
            new_preds.append(pred[:, :6])
        ret = self.ret2pts_list(new_preds)
        return ret

    def _postprocess_segment(self, preds, target_shape, src_shape, **kwargs):

        protos = preds[1][-1] if isinstance(preds[1], tuple) else preds[1]
        preds = super().postprocess(preds[0], target_shape, src_shape, **kwargs)
        new_preds = []
        xy_pts = []
        for i, (pred, orig_img_shape, proto) in enumerate(zip(preds, src_shape, protos)):
            if not len(pred):  # save empty boxes
                masks = None
            elif kwargs.get('retina_masks', 0):
                pred[:, :4] = ops.scale_boxes(target_shape, pred[:, :4], orig_img_shape)
                masks = ops.process_mask_native(proto, pred[:, 6:], pred[:, :4], orig_img_shape[:2])  # HWC
            else:
                masks = ops.process_mask(proto, pred[:, 6:], pred[:, :4], target_shape, upsample=True)  # HWC
                pred[:, :4] = ops.scale_boxes(target_shape, pred[:, :4], orig_img_shape)

            if masks is not None:
                keep = masks.sum((-2, -1)) > 0  # only keep predictions with masks
                pred, masks = pred[keep], masks[keep]
                mask_polygons = [
                    ops.scale_coords(target_shape, x, orig_img_shape, normalize=False)
                    for x in ops.masks2segments(masks)]
                new_preds.append(pred[:, :6])
                xy_pts.append(mask_polygons)
            else:
                new_preds.append([])
                xy_pts.append([])

        ret = self.ret2pts_list(new_preds)
        ret['xy'] = xy_pts
        return (ret)

    def _postprocess_classify(self, preds):
        preds = preds[0] if isinstance(preds, (list, tuple)) else preds
        if torch.is_tensor(preds):
            preds_np = preds.cpu().numpy()
        else:
            preds_np = np.array(preds)
        max_indices = np.argmax(preds_np, axis=1)
        name = [self.model.names[x] for x in max_indices]
        print(preds_np, type(preds_np), name)
        return preds_np

    def _postprocess_pose(self, preds, target_shape, src_shape, **kwargs):

        preds = super().postprocess(preds, target_shape, src_shape, **kwargs)
        new_preds = []
        kpts = []
        for pred, orig_img_shape in zip(preds, src_shape):
            pred[:, :4] = ops.scale_boxes(target_shape, pred[:, :4], orig_img_shape).round()
            new_preds.append(pred[:, :6])
            pred_kpts = pred[:, 6:].view(len(pred), *self.model.kpt_shape) if len(pred) else pred[:, 6:]
            pred_kpts = ops.scale_coords(target_shape, pred_kpts, orig_img_shape)  # [(x1,y1,conf),(x2,y2.conf)...]
            if isinstance(pred_kpts, torch.Tensor):
                pred_kpts = pred_kpts.cpu().numpy()
            else:
                pred_kpts = np.array(pred_kpts)
            kpts.append(pred_kpts)
        ret = self.ret2pts_list(new_preds)
        ret['kpts'] = kpts
        return ret

    def __call__(self, im0s):
        torch.cuda.synchronize()
        a = time.time()
        im = self.preprocess(im0s)
        b = time.time()
        preds = self.inference(im)
        print(preds[0].shape)
        c = time.time()
        src_shape = [x.shape for x in im0s]
        target_shape = im.shape[2:]
        ret = self.postprocess(preds, target_shape, src_shape, conf=self.kwargs['conf'], iou=self.kwargs['iou'])
        torch.cuda.synchronize()
        return ret


if __name__ == '__main__':
    import time
    from pathlib import Path

    task = {
        0: 'detect',  # 目标检测
        1: 'segment',  # 语义分割
        2: 'classify',  # 分类
        3: 'pose',  # 关键点检测
    }
    select_task = 2
    yolo_worker = Yolo_torch(
        weight_path=r'C:\Users\yiche\Desktop\2_Dihuge_Projects_code\Deeplearning\ultralytics_main_20250702\runs\classify\train9\weights\best.pt',

        imgsz=224, conf=0.25, iou=0.6, task=task[select_task], batch=1)
    # indir = r"C:\Users\yiche\Desktop\2_Dihuge_Projects_code\Deeplearning\ultralytics_main_20250702\datasets\coco8-seg\images\val"
    # indir = r'C:\Users\yiche\Desktop\2_Dihuge_Projects_code\Deeplearning\ultralytics_main_20250702\datasets\coco8\images\val'
    indir = r'D:\Data\my_classify\val\5'
    pth_lst = glob.glob(indir + os.sep + '*.*')
    # write_json_dir = r'E:\samples\liuzhou_maoci_sample\val\jsonsss'

    for one_path in pth_lst:
        image_name = os.path.basename(one_path)
        json_name = Path(image_name).with_suffix('.json')
        image = cv2.imread(one_path)
        aaa = time.time()
        ims = [image]
        ret = yolo_worker(ims)
        if task[select_task] == 'detect':
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i]
                }
                draw = draw_defect_pts(ims[i], one_ret)
                show(draw, 'draw')
                b = time.time()
                print(b - aaa)
        elif task[select_task] == 'segment':
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i],
                    'xy': ret['xy'][i]
                }
                draw = draw_defect_pts(ims[i], one_ret)
                for polygon in one_ret['xy']:
                    pts = polygon.reshape((-1, 1, 2)).astype(np.int32)
                    cv2.polylines(draw, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                show(draw, 'draw')
                b = time.time()
                print(b - aaa)
        elif task[select_task] == 'classify':
            # print(ret)
            pass
        elif task[select_task] == 'pose':
            for i in range(len(ret['pts_list'])):
                one_ret = {
                    'pts_list': ret['pts_list'][i],
                    'lab_list': ret['lab_list'][i],
                    'conf_list': ret['conf_list'][i],
                    'kpts': ret['kpts'][i]
                }
                draw = draw_defect_pts(ims[i], one_ret)
                for pts in one_ret['kpts']:
                    for one_pt in pts:
                        if one_pt[-1] > 0.5:
                            cv2.circle(draw, (int(one_pt[0]), int(one_pt[1])), 2, (0, 0, 255), -1)
                show(draw, 'draw')
                b = time.time()
                print(b - aaa)
