import numpy as np
from math import *
import cv2
from matplotlib import cm
import math
import random
import struct
import tifffile
from PIL import Image, ImageDraw, ImageFont
import time
import os


class ImageProcess:
    @staticmethod  # 查找轮廓
    def findContours(
            binary_img: np.ndarray,
            approx_method: int = cv2.CHAIN_APPROX_SIMPLE,
            hierarchy_min: int = 0,
            hierarchy_max: int = 0,
            min_length: float = 0,
            max_length: float = float('inf'),
            min_area: float = 0,
            max_area: float = float('inf'),
            sort_by: str = 'area_desc',
            max_output: int = 0
    ):
        """
        多条件筛选并排序的轮廓检测函数
        参数：
            binary_img: 二值化图像(0-255)
            approx_method: 轮廓近似方法(cv2.CHAIN_APPROX_*)
            hierarchy_min/max: 层级下限/上限(0为最外层)
            min_length/max_length: 轮廓周长范围(像素)
            min_area/max_area: 轮廓面积范围(像素)
            sort_by: 排序方式('area_desc'面积降序/'length_desc'长度降序)
            max_output: 最大输出轮廓数量(0表示不限制)
        返回：
            (轮廓列表, 面积列表, 周长列表, 外接矩形列表)
        """
        # 检测原始轮廓
        contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_TREE, approx_method)
        if hierarchy is None:
            return [], [], [], []

        hierarchy = hierarchy[0]
        result = []

        # 计算轮廓特征并筛选
        for i, cnt in enumerate(contours):
            # 计算层级深度
            level = 0
            parent_idx = hierarchy[i][3]
            while parent_idx != -1:
                level += 1
                parent_idx = hierarchy[parent_idx][3]

            # 计算轮廓特征
            area = cv2.contourArea(cnt)
            length = cv2.arcLength(cnt, True)
            rect = cv2.boundingRect(cnt)

            # 多条件筛选
            if (hierarchy_min <= level <= hierarchy_max and
                    min_length <= length <= max_length and
                    min_area <= area <= max_area):
                result.append((cnt, area, length, rect))

        # 排序处理
        if sort_by == 'area_desc':
            result.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == 'length_desc':
            result.sort(key=lambda x: x[2], reverse=True)

        # 限制输出数量
        if max_output > 0:
            result = result[:max_output]

        # 解包结果
        contours = [x[0] for x in result]
        areas = [x[1] for x in result]
        lengths = [x[2] for x in result]
        rects = [x[3] for x in result]

        return contours, areas, lengths, rects

    @staticmethod  # 多尺度模板匹配
    def multi_scale_template_match(image, template, resize=1.0, scales=(0.95, 0.97, 1.0, 1.02, 1.05),
                                   method=cv2.TM_CCOEFF_NORMED):
        """
        多尺度模板匹配函数
        参数:
            image: 待搜索图像(BGR或灰度)
            template: 模板图像(BGR或灰度)
            resize:缩放后再进行匹配，提速专用
            scales: 缩放比例列表(默认[0.95,0.97,1.0,1.02,1.05])
            method: 匹配方法(默认cv2.TM_CCOEFF_NORMED)
        返回:
            best_score: 最高匹配得分(0-1)
            best_rect: 最佳匹配矩形(x, y, w, h)
            best_scale: 最佳匹配比例
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if len(template.shape) == 3:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        image = cv2.resize(image, None, fx=resize, fy=resize)
        template = cv2.resize(template, None, fx=resize, fy=resize)
        best_score = -1
        best_rect = None
        best_scale = 1.0
        for scale in scales:
            # 缩放模板
            resized_template = cv2.resize(template, None, fx=scale, fy=scale)
            h, w = resized_template.shape
            # 跳过过大的模板
            if h > image.shape[0] or w > image.shape[1]:
                continue
            # 执行模板匹配
            res = cv2.matchTemplate(image, resized_template, method)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            # 更新最佳匹配
            if max_val > best_score:
                best_score = max_val
                best_rect = (max_loc[0], max_loc[1], w, h)
                best_scale = scale
        best_rect = [int(x / resize) for x in best_rect]
        return best_score, best_rect, best_scale

    @staticmethod  # 合并轮廓，有重叠则取轮廓2的轮廓
    def merge_contours(contours_list1, contours_list2):
        """
        合并两个轮廓列表，处理轮廓间的重叠关系
        参数:
        contours_list1 -- 第一个轮廓列表 [contour1, contour2, ...]
        contours_list2 -- 第二个轮廓列表 [contour3, contour4, ...]
        返回:
        合并后的轮廓列表，满足:
        1. 如果contours_list1中的轮廓与contours_list2中的轮廓重叠，则丢弃contours_list1中的轮廓
        2. 如果没有重叠，则保留各自的轮廓
        3. 返回的列表中轮廓间无重叠
        注意: 假设每个输入列表内部的轮廓本身不重叠
        """

        # 创建用于检查重叠的辅助函数
        def check_overlap(contour_a, contour_b):
            """检查两个轮廓是否重叠"""
            # 获取两个轮廓的边界框
            x1, y1, w1, h1 = cv2.boundingRect(contour_a)
            x2, y2, w2, h2 = cv2.boundingRect(contour_b)

            # 快速检查边界框是否相交
            if x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1:
                return False

            # 计算相交区域的坐标
            x = max(x1, x2)
            y = max(y1, y2)
            w = min(x1 + w1, x2 + w2) - x
            h = min(y1 + h1, y2 + h2) - y

            # 创建小尺寸掩码用于精确检查
            mask1 = np.zeros((h, w), dtype=np.uint8)
            mask2 = np.zeros((h, w), dtype=np.uint8)

            # 调整轮廓坐标到相交区域坐标系
            pts1 = contour_a - [x, y]
            pts2 = contour_b - [x, y]

            # 填充轮廓
            cv2.fillPoly(mask1, [pts1], 255)
            cv2.fillPoly(mask2, [pts2], 255)

            # 检查是否有重叠区域
            intersection = cv2.bitwise_and(mask1, mask2)
            return np.sum(intersection) > 0

        # 筛选contours_list1中不与contours_list2重叠的轮廓
        non_overlapping_contours = []
        for contour1 in contours_list1:
            is_overlapping = False
            for contour2 in contours_list2:
                if check_overlap(contour1, contour2):
                    is_overlapping = True
                    break
            if not is_overlapping:
                non_overlapping_contours.append(contour1)
        # 合并保留的contours_list1和所有的contours_list2
        merged_contours = non_overlapping_contours + contours_list2
        areas = 0
        for i, cnt in enumerate(merged_contours):
            areas += cv2.contourArea(cnt)
        return non_overlapping_contours, contours_list2, areas

    @staticmethod  # 坐标还原  rect,line,pt,circle
    def coord_return(instance, roi_rect, fx=1.0, fy=1.0, to_int=True):
        """
        将检测结果的坐标从裁剪区域映射回原始图像坐标

        Args:
            instance: 检测结果，可以是:
                      - 矩形: [x1, y1, x2, y2]
                      - 线: [x1, y1, x2, y2]
                      - 点: [x, y]
                      - 圆: [x, y, r]
                      - 多边形: [x1, y1, x2, y2, ..., xn, yn]
            roi_rect: 裁剪区域的矩形，格式为 [x, y, width, height]
            fx: x轴缩放因子（相对于原始图像）
            fy: y轴缩放因子（相对于原始图像）
            to_int: 是否将结果转换为整数，默认为True

        Returns:
            映射回原始图像坐标的检测结果，格式与输入相同
        """
        # 处理空输入
        if not instance:
            return []

        # 提取ROI左上角坐标
        roi_x, roi_y = roi_rect[:2]
        result = []

        # 特殊处理圆的情况 (3个元素)
        if len(instance) == 3:
            # 圆: [x, y, r]
            x = (instance[0] + roi_x) * fx
            y = (instance[1] + roi_y) * fy
            r = instance[2] * max(fx, fy)  # 半径使用最大缩放因子

            if to_int:
                return [int(x), int(y), int(r)]
            return [x, y, r]
        # 处理其他几何形状 (点、线、矩形、多边形)
        for i in range(0, len(instance), 2):
            if i + 1 < len(instance):
                x = (instance[i] + roi_x) * fx
                y = (instance[i + 1] + roi_y) * fy

                if to_int:
                    result.append(int(x))
                    result.append(int(y))
                else:
                    result.append(x)
                    result.append(y)
        return result

    @staticmethod  # 图像二值化
    def image_binary(src_img, method='binary', mask_img=None, threshold=127, maxval=255
                     ):
        """
        支持掩码的可选二值化函数
        :param src_img: 源图像(灰度/彩色)
        :param method: 二值化方法('binary','binary_inv','trunc','otsu','triangle')
        :param mask_img: 掩码图像(None或与src_img同尺寸的二值图)
        :param threshold: 手动阈值(自动方法无效)
        :param maxval: 最大值(默认255)
        :return: 二值化结果图像
        """
        # 转换为灰度图
        if len(src_img.shape) > 2:
            gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = src_img.copy()
        # 初始化输出图像
        dst_img = np.zeros_like(gray)
        # 无掩码情况处理全图
        if mask_img is None:
            roi = gray
            mask_area = np.ones_like(gray, dtype=bool)
        else:
            # 处理掩码
            if len(mask_img.shape) > 2:
                mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
            mask_area = mask_img > 0
            roi = gray[mask_area]
        # 空掩码直接返回全黑图
        if mask_img is not None and not np.any(mask_area):
            return dst_img
        # 选择二值化方法
        thresh_type = {
            'binary': cv2.THRESH_BINARY,
            'binary_inv': cv2.THRESH_BINARY_INV,
            'trunc': cv2.THRESH_TRUNC,
            'otsu': cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            'triangle': cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE
        }.get(method, cv2.THRESH_BINARY)
        # 执行阈值处理
        if method in ['otsu', 'triangle']:
            _, thresh = cv2.threshold(roi, 0, maxval, thresh_type)
        else:
            _, thresh = cv2.threshold(roi, threshold, maxval, thresh_type)
        # 填充结果
        if mask_img is None:
            dst_img = thresh.reshape(gray.shape)
        else:
            dst_img[mask_area] = thresh
        return dst_img

    @staticmethod  # 图像形态学操作
    def morphology_operation(src_img, method='dilate', kernel_size=(3, 3)):
        """
        图像形态学操作函数
        :param src_img: 输入图像(灰度或彩色)
        :param method: 操作方法('blur','median','gaussian','dilate','erode',
                       'open','close','tophat','blackhat','gradient')
        :param kernel_size: 卷积核尺寸(宽,高)
        :return: 处理后的图像
        """
        # 创建矩形核
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        # 灰度处理(形态学运算需要单通道)
        if len(src_img.shape) > 2 and method not in ['blur', 'median', 'gaussian']:
            gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = src_img.copy()
        # 执行不同操作
        if method == 'blur':
            result = cv2.blur(src_img, kernel_size)
        elif method == 'median':
            result = cv2.medianBlur(src_img, kernel_size[0])
        elif method == 'gaussian':
            result = cv2.GaussianBlur(src_img, kernel_size, 0)
        elif method == 'dilate':
            result = cv2.dilate(gray, kernel)
        elif method == 'erode':
            result = cv2.erode(gray, kernel)
        elif method == 'open':
            result = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        elif method == 'close':
            result = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        elif method == 'tophat':
            result = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        elif method == 'blackhat':
            result = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        elif method == 'gradient':
            result = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        else:
            raise ValueError("Unsupported method")

        # 保持原通道数
        if len(src_img.shape) > 2 and method not in ['blur', 'median', 'gaussian']:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

        return result

    @staticmethod  # 图像合并
    def merge_images(image1, image2, method='add'):
        """
        合并两幅图像
        :param image1: 第一幅图像(numpy数组或文件路径)
        :param image2: 第二幅图像(numpy数组或文件路径)
        :param method: 合并方法('add','subtract','and','or','xor','xnor','max','min')
        :return: 合并后的图像
        """
        # 如果输入是文件路径则读取图像
        if isinstance(image1, str):
            img1 = cv2.imread(image1, cv2.IMREAD_COLOR)
        else:
            img1 = image1.copy()

        if isinstance(image2, str):
            img2 = cv2.imread(image2, cv2.IMREAD_COLOR)
        else:
            img2 = image2.copy()

        # 确保两图像尺寸相同
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        # 执行不同的合并操作
        method = method.lower()
        if method == 'add':
            result = cv2.add(img1, img2)
        elif method == 'subtract':
            result = cv2.subtract(img1, img2)
        elif method == 'and':
            result = cv2.bitwise_and(img1, img2)
        elif method == 'or':
            result = cv2.bitwise_or(img1, img2)
        elif method == 'xor':
            result = cv2.bitwise_xor(img1, img2)
        elif method == 'xnor':
            result = cv2.bitwise_not(cv2.bitwise_xor(img1, img2))
        elif method == 'max':
            result = np.maximum(img1, img2).astype(np.uint8)
        elif method == 'min':
            result = np.minimum(img1, img2).astype(np.uint8)
        else:
            raise ValueError("Unsupported method. Use 'add','subtract','and','or','xor' or 'xnor'")
        return result

    @staticmethod  # 图像翻转
    def flip_image(one_img, flipCode='水平'):
        try:
            if flipCode == '水平':
                dst_img = cv2.flip(one_img, flipCode=1)
            elif flipCode == '竖直':
                dst_img = cv2.flip(one_img, flipCode=0)
            elif flipCode == '对角线':
                dst_img = cv2.flip(one_img, flipCode=-1)
            else:
                dst_img = one_img
            return dst_img
        except Exception as e:
            return None

    @staticmethod  # 旋转图像
    def roate_image(img, angle):
        height, width = img.shape[:2]
        degree = angle
        # 旋转后的尺寸
        heightNew = int(width * fabs(sin(radians(degree))) + height * fabs(cos(radians(degree))))
        widthNew = int(height * fabs(sin(radians(degree))) + width * fabs(cos(radians(degree))))
        matRotation = cv2.getRotationMatrix2D((int(width / 2), int(height / 2)), degree, 1)
        matRotation[0, 2] += (widthNew - width) / 2  # 重点在这步，目前不懂为什么加这步
        matRotation[1, 2] += (heightNew - height) / 2  # 重点在这步
        imgRotation = cv2.warpAffine(img, matRotation, (widthNew, heightNew), borderValue=(255, 255, 255))
        return imgRotation

    @staticmethod  # 图像锐化
    def sharpening(img, rect=None):  # 图像锐化
        if rect is None: rect = [[0, -1, 0], [-1, 9, -1], [0, -1, 0]]
        kernel = np.array(rect, np.float32)  # 定义一个核
        return cv2.filter2D(img.copy(), -1, kernel=kernel)

    @staticmethod  # 按相邻元素间差值划分数组
    def splitList(iterable, diff=1, key=None):
        """
        :param iterable: 数组
        :param diff: 分组差值
        :param key: 回调函数 数组元素运算后再进行比较 例如 key=lambda x:x[0]
        :return:
        """
        max_diff = diff
        splited_list = []
        prev_element = float('-inf')
        for element in iterable:
            val_ = key(element) if key is not None else element
            if val_ - prev_element > max_diff:
                splited_list.append([])
            splited_list[-1].append(element)
            prev_element = val_
        return splited_list

    @staticmethod  # 筛选连通域
    def filter_connected_components(img, min_w, min_h, max_w, max_h):
        labels, ccm, status, _ = cv2.connectedComponentsWithStats(img)
        roiRect = []
        for i in range(labels):
            idx = np.where(ccm == i)
            if idx[0].shape[0] == 0:
                return None
            if ccm[idx[0][0], idx[1][0]] == 0:
                continue
            if min_w < status[i][2] < max_w and min_h < status[i][3] < max_h:
                pad = 1
                x = status[i][0] - pad
                y = status[i][1] - pad
                w = status[i][2] + 2 * pad
                h = status[i][3] + 2 * pad
                roiRect.append([x, y, x + w, y + h])
            else:
                continue
        return roiRect

    @staticmethod  # 调整亮度
    def adjust_brightness(image, k=2, b=0):
        adjust_bright = np.float16(image) * k + b
        adjust_bright[adjust_bright > 255] = 255
        # adjust_bright[adjust_bright < 0] = 0
        new_image = np.uint8(adjust_bright)
        return new_image

    @staticmethod  # 获取图像归一化矩阵
    def get_normlize_mat(img, min=-10000.0, max=40000.0):
        print('原图像最大最小：', img.max(), img.min())
        mask = (img > min) & (img < max)
        valid_depth = img[mask]
        if valid_depth.size == 0:
            raise ValueError("No valid depth values found")
        maxV = valid_depth.max()
        minV = valid_depth.min()
        print('normlize 有效最大最小值:', maxV, minV)
        normlize_mat = np.zeros_like(img, dtype=np.float32)
        normlize_mat[mask] = (valid_depth - minV) / (maxV - minV)
        return normlize_mat

    @staticmethod  # 将非uint8图像转换为uint8图像
    def normalize2gray(img, min=-10000.0, max=40000.0):
        mask = (img > min) & (img < max)
        mask1 = img >= max
        valid_depth = img[mask]
        if valid_depth.size == 0:
            raise ValueError("No valid depth values found")
        maxV = max
        minV = min
        gray_img = np.zeros_like(img, dtype=np.uint8)
        scale = 255.0 / (maxV - minV)
        gray_img[mask] = ((valid_depth - minV) * scale).astype(np.uint8)
        gray_img[mask1] = 255
        # gray_img[~mask] = 255
        # equalized_img = cv2.equalizeHist(gray_img) # 直方图均衡化
        return gray_img

    @staticmethod  # 查找topk个连通域
    def biggest_component(img, topk=1):
        # 只保留最大topk个连通域，干掉其他的，如果没有白色区域，返回None
        ret_dict = {
            'binary': img,
            'status': [],
        }
        labels, ccm, status, centers = cv2.connectedComponentsWithStats(img)
        max_area = 0
        max_idx = -1
        sort_label = np.argsort(status[:, 4], axis=-1)[::-1]
        if sort_label.shape[0] == 0:
            return ret_dict
        black_lab = None
        h, w = img.shape
        # 四个角大概率是黑的
        corners = [[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]]
        for corner in corners:
            if img[corner[1], corner[0]] == 0:
                black_lab = ccm[corner[1], corner[0]]
                break
        used_labs = []
        for i in range(labels):
            if len(used_labs) == topk:
                break
            lab = sort_label[i]
            if black_lab is not None:
                if lab == black_lab:
                    continue
                else:
                    used_labs.append(lab)
            else:
                idx = np.where(ccm == lab)
                color = img[idx[0][0], idx[1][0]]
                if color == 0:
                    black_lab = lab
                else:
                    used_labs.append(lab)
        base = np.zeros((h, w), np.uint8)
        for lab in used_labs:
            idx = np.where(ccm == lab)
            if status[lab][-1] > 3000:
                base[idx] = 255
                ret_dict['status'].append(status[lab])
        ret_dict['binary'] = base
        #    cv2.imshow('base', base)
        #    cv2.waitKey(0)
        return ret_dict

    @staticmethod  # 将深度图转换为rgba图像
    def get_depth_rgba(depth_map, min=-10, max=10):
        mask = (depth_map > min) & (depth_map < max)
        valid_depth = depth_map[mask]
        if valid_depth.size == 0:
            raise ValueError("No valid depth values found")

        print('裁剪后深度图最大最小值：', depth_map.max(), depth_map.min(), valid_depth.min())
        maxV = valid_depth.max()
        minV = valid_depth.min()
        # print(maxV, minV, '*******************')
        # 确保输入数据在[0,1]范围内
        gray_img = np.zeros_like(depth_map, dtype=np.float32)
        gray_img[mask] = (valid_depth - minV) / (maxV - minV)
        gray_img[~mask] = 0
        # print(gray_img.max(), gray_img.min(), '/////////')
        gray_img = cv2.medianBlur(gray_img, ksize=3)
        # 应用jet色图（返回RGBA格式）
        rgba = cm.jet(gray_img)
        # 转换为0-255范围的RGB数组
        return (rgba[..., :3] * 255).astype(np.uint8)

    @staticmethod  # 计算图像曲率
    def compute_curvature_image(gray, blur_kernel_size=5):
        # 转换为浮点并归一化
        gray = ImageProcess.get_normlize_mat(gray, min=-7, max=7)
        print(gray.max(), gray.min())
        # 高斯模糊减少噪声
        blurred = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)

        # 计算一阶导数 (Sobel算子)
        Ix = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        Iy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

        # 计算二阶导数
        Ixx = cv2.Sobel(Ix, cv2.CV_64F, 1, 0, ksize=3)
        Ixy = cv2.Sobel(Ix, cv2.CV_64F, 0, 1, ksize=3)
        Iyy = cv2.Sobel(Iy, cv2.CV_64F, 0, 1, ksize=3)

        # 计算平均曲率（修复后的表达式）
        numerator = (1 + Ix ** 2) * Iyy - 2 * Ix * Iy * Ixy + (1 + Iy ** 2) * Ixx
        denominator = 2 * (1 + Ix ** 2 + Iy ** 2) ** 1.5
        # 避免除以零
        np.maximum(denominator, 1e-8, out=denominator)
        curvature = numerator / denominator

        # # 归一化并转换为uint8
        curvature_normalized = cv2.normalize(np.abs(curvature), None, 0, 255, cv2.NORM_MINMAX)
        curvature_image = curvature_normalized.astype(np.uint8)
        return curvature_image

    @staticmethod  # 图像裁剪
    def safe_crop(image, rect, left=0, right=0, top=0, bottom=0):
        '''
        image:
        rect: (x, y,w,h)
        left: offset 向左
        '''
        h, w = image.shape[:2]
        x0 = max(0, int(rect[0] - left + 0.5))
        y0 = max(0, int(rect[1] - top + 0.5))
        x1 = min(w - 1, int(rect[2] + rect[0] + right + 0.5))
        y1 = min(h - 1, int(rect[3] + rect[1] + bottom + 0.5))
        if y1 - y0 > 0 and x1 - x0 > 0:
            roi = image[y0:y1, x0:x1]
        else:
            roi = None
        pts = [x0, y0, x1, y1]
        return roi, pts

    @staticmethod  # 拼接图像
    def concat_images(images, x=1, padding='black'):
        lenth_ = len(images)
        assert lenth_ > 2 and lenth_ >= x
        color = (0, 0, 0) if padding == 'black' else (255, 255, 255)
        h_w_arr = np.array([one_image.shape[:2] for one_image in images])
        max_h_idx, max_w_idx = np.argmax(h_w_arr, axis=0)
        if x == 1:
            concat_list = []
            for idx, one_image in enumerate(images):
                right = int(round(h_w_arr[max_w_idx, 1] - h_w_arr[idx, 1] - 0.1))
                one_image = one_image if right == 0 else cv2.copyMakeBorder(one_image, 0, 0, 0, right,
                                                                            cv2.BORDER_CONSTANT, value=color)
                concat_list.append(one_image)
            return np.vstack(concat_list)
        elif len(images) / x == 1 or x == -1:
            concat_list = []
            for idx, one_image in enumerate(images):
                bottom = int(round(h_w_arr[max_h_idx, 0] - h_w_arr[idx, 0] - 0.1))
                one_image = one_image if bottom == 0 else cv2.copyMakeBorder(one_image, 0, bottom, 0, 0,
                                                                             cv2.BORDER_CONSTANT,
                                                                             value=color)  # add border
                concat_list.append(one_image)
            return np.hstack(concat_list)
        else:
            r = int(np.ceil(lenth_ / x))
            concat_image = np.zeros((1, h_w_arr[max_w_idx, 1] * x + 1, 3), dtype=np.uint8)
            for one_r in range(1, r + 1):
                if one_r < r:
                    concat_cols_image = np.zeros((h_w_arr[max_h_idx, 0], 1, 3), dtype=np.uint8)
                    for idx, one_image in enumerate(images[x * (one_r - 1):x * (one_r)]):
                        left, right = 0, int(round(h_w_arr[max_w_idx, 1] - h_w_arr[idx, 1] - 0.1))
                        top, bottom = 0, int(round(h_w_arr[max_h_idx, 0] - h_w_arr[idx, 0] - 0.1))
                        one_image = cv2.copyMakeBorder(one_image, top, bottom, left, right, cv2.BORDER_CONSTANT,
                                                       value=color)  # add border
                        concat_cols_image = np.hstack((concat_cols_image, one_image))
                    concat_image = np.vstack((concat_image, concat_cols_image))
                else:
                    concat_cols_image = np.zeros((h_w_arr[max_h_idx, 0], 1, 3), dtype=np.uint8)
                    for idx, one_image in enumerate(images[x * (one_r - 1):]):
                        left, right = 0, int(round(h_w_arr[max_w_idx, 1] - h_w_arr[idx, 1] - 0.1))
                        top, bottom = 0, int(round(h_w_arr[max_h_idx, 0] - h_w_arr[idx, 0] - 0.1))
                        one_image = cv2.copyMakeBorder(one_image, top, bottom, left, right, cv2.BORDER_CONSTANT,
                                                       value=color)  # add border
                        concat_cols_image = np.hstack((concat_cols_image, one_image))
                    if concat_cols_image.shape[1] < concat_image.shape[1]:
                        right = concat_image.shape[1] - concat_cols_image.shape[1]
                        concat_cols_image = cv2.copyMakeBorder(concat_cols_image, 0, 0, 0, right, cv2.BORDER_CONSTANT,
                                                               value=color)
                    concat_image = np.vstack((concat_image, concat_cols_image))
            return np.delete(np.delete(concat_image, 0, axis=0), 0, axis=1)

    @staticmethod  # 散步截取roi
    def mulity_crop(image, nx=1, ny=1, sw=0, sh=0):
        """
        :param image:
        :param nx: 水平裁剪个数
        :param ny: 竖直裁剪个数
        :param sw: 小图width
        :param sh: 小图height
        :return:
        """
        h, w = image.shape[:2]
        assert sw <= w and sh <= h and nx > 0 and ny > 0
        if sw == 0:
            x_list, x_step = np.linspace(0, w, num=nx, endpoint=False, retstep=True)
        elif sw > 0:
            if nx > 1:
                x_list, x_step = np.linspace(0, w - sw, num=nx - 1, endpoint=False), sw
                x_list = np.append(x_list, w - sw)
            else:
                x_list, x_step = np.linspace(0, w, num=nx, endpoint=False), sw
        if sh == 0:
            y_list, y_step = np.linspace(0, h, num=ny, endpoint=False, retstep=True)
        elif sh > 0:
            if ny > 1:
                y_list, y_step = np.linspace(0, h - sh, num=ny - 1, endpoint=False), sh
                y_list = np.append(y_list, h - sh)
            else:
                y_list, y_step = np.linspace(0, w, num=ny, endpoint=False), sh

        x_coord, y_coord = np.meshgrid(x_list, y_list)
        points = np.hstack([x_coord.reshape(-1, 1), y_coord.reshape(-1, 1)])
        w_h = np.zeros_like(points)
        w_h[:, 0], w_h[:, 1] = x_step, y_step
        rects_array = np.c_[points, w_h]
        small_rois = []
        for _oneRect in rects_array:
            small_rois.append(ImageProcess.safe_crop(image, _oneRect))
        return small_rois, rects_array.tolist()

    @staticmethod  # 连通域转为凸包
    def fill_convex_hulls(binary_img):
        """
        将二值图像中每个连通域替换为其凸包区域
        :param binary_img: 输入二值图像(单通道0-255)
        :return: 凸包填充后的二值图像
        """
        # 确保输入是单通道
        if len(binary_img.shape) > 2:
            binary_img = cv2.cvtColor(binary_img, cv2.COLOR_BGR2GRAY)
        # 创建空白画布
        result = np.zeros_like(binary_img)
        # 查找所有连通域轮廓
        contours, _ = cv2.findContours(
            binary_img,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        # 处理每个连通域
        for cnt in contours:
            # 计算凸包
            hull = cv2.convexHull(cnt)
            # 绘制填充凸包(白色)
            cv2.drawContours(
                result,
                [hull],
                -1,
                255,
                thickness=cv2.FILLED
            )
        return result

    @staticmethod  # 按投影提取roi
    def extract_roi_by_projection(image, rx=0.1, ry=0.1):
        try:
            h, w = image.shape[:2]
            x_white_num, y_whitw_num = int(w * rx), int(h * ry)
            sum_white_per_x = np.sum(image, axis=1) / 255
            fit_rows = np.where(sum_white_per_x > x_white_num)  # 从这里选出小于num像素点个数的横坐标
            y_list = ImageProcess.splitList(fit_rows[0])
            roi_y_coord = max(y_list, key=lambda x: len(x))
            y1, y2 = roi_y_coord[0], roi_y_coord[-1]
            sum_white_per_y = np.sum(image, axis=0) / 255
            fit_cols = np.where(sum_white_per_y > y_whitw_num)  # 从这里选出小于num像素点个数的横坐标
            x_list = ImageProcess.splitList(fit_cols[0])
            roi_x_coord = max(x_list, key=lambda x: len(x))
            x1, x2 = roi_x_coord[0], roi_x_coord[-1]
            return [x1, y1, x2, y2]
        except Exception as e:
            print(str(e))
            return []

    @staticmethod  # 图像显示
    def show(img, window_name, src=None, flag=False, max_size=850):
        if flag:
            # 状态变量
            drawing = False
            moving = False
            ix, iy = -1, -1
            rects = []  # 存储所有矩形 [(x1,y1,x2,y2)]
            selected_rect = None
            base_point = None
            original_img = img.copy()  # 保存原始图像
            h, w = img.shape[:2]
            if h > w:
                ratio = max_size / float(h)
                new_dim = (int(w * ratio), max_size)
            else:
                ratio = max_size / float(w)
                new_dim = (max_size, int(h * ratio))

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
                        rects.append((min(ix, x), min(iy, y), max(ix, x), max(iy, y)))
                        update_display()
                    elif moving:
                        moving = False
                        selected_rect = None

            def draw_all_rects(display_img):
                for i, (x1, y1, x2, y2) in enumerate(rects):
                    if abs(y1 - y2) > 2 and abs(x1 - x2) > 2:
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

            cv2.namedWindow(str(window_name), cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(str(window_name), draw_callback, )
            cv2.resizeWindow(str(window_name), new_dim[0], new_dim[1])
            update_display()
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    @staticmethod  # 计算图像梯度和角度
    def gen_magnitude(img):
        '''
        :param img:
        :return:
        '''
        smoothed = cv2.GaussianBlur(img, (1, 1), 0, sigmaY=0, borderType=cv2.BORDER_REPLICATE)
        sobel_dx = cv2.Sobel(smoothed, cv2.CV_32F, 1, 0, ksize=3, scale=1, delta=0, borderType=cv2.BORDER_REPLICATE)
        sobel_dy = cv2.Sobel(smoothed, cv2.CV_32F, 0, 1, ksize=3, scale=1, delta=0, borderType=cv2.BORDER_REPLICATE)
        magnitude = np.sqrt(sobel_dx * sobel_dx + sobel_dy * sobel_dy)
        sobel_ag = cv2.phase(sobel_dx, sobel_dy, angleInDegrees=True)
        return magnitude, sobel_ag

    @staticmethod  # ransac拟合直线
    def fit_line(points, method='least_squares', sigma=0.5, iters=300, x_std=0.1):  # x_std: x坐标的标准差,用于判断是不是竖直线
        if method == 'least_squares':
            """
            使用最小二乘法拟合直线
            参数:
                points: 点集，格式为[(x1,y1), (x2,y2), ...]或np.array
            返回:
                (k, b): 直线斜率和截距
            """
            if isinstance(points, np.ndarray):
                x = points[:, 0]
                y = points[:, 1]
            elif isinstance(points, list):
                x = np.array([point[0] for point in points])
                y = np.array([point[1] for point in points])
            else:
                raise Exception("Parameter 'coords' is an unsupported type: " + str(type(points)))

            cov = np.cov(x, y, bias=True)
            slope = cov[0, 1] / cov[0, 0]  # 斜率 = cov(x,y)/var(x)
            intercept = np.mean(y) - slope * np.mean(x)
            return slope, intercept
        elif method == 'ransac':
            max_inliers, best_inliers = 0, None
            good_count = 0  # 记录优质模型计数
            n_points = len(points)
            split_idx = n_points // 2  # 前后半部分分界点

            for _ in range(iters):
                # 1. 改进采样策略
                idx1 = random.randint(0, split_idx - 1)
                idx2 = random.randint(split_idx, n_points - 1)
                p1, p2 = points[idx1], points[idx2]

                # 2. 计算直线参数
                if abs(p1[0] - p2[0]) < 1e-20:
                    k = float('inf')
                    b = p1[0]
                else:
                    k = (p2[1] - p1[1]) / (p2[0] - p1[0])
                    b = p1[1] - k * p1[0]

                # 3. 计算内点
                distances = []
                for point in points:
                    if k == float('inf'):
                        dist = abs(point[0] - b)
                    else:
                        dist = abs(k * point[0] - point[1] + b) / np.sqrt(k ** 2 + 1)
                    distances.append(dist)

                inliers = np.where(np.array(distances) < sigma)[0]
                num_inliers = len(inliers)

                # 4. 优质模型检测
                if num_inliers > 0.8 * n_points:
                    good_count += 1
                    if good_count >= 30:
                        break

                # 5. 更新最佳模型
                if num_inliers > max_inliers:
                    max_inliers = num_inliers
                    best_inliers = inliers

            # 6. 最终优化拟合

            if best_inliers is not None and len(best_inliers) > 1:
                inlier_points = points[best_inliers]
                x_points = inlier_points[:, 0]
                print(np.std(x_points))
                if np.std(x_points) < x_std:
                    c = np.mean(x_points)  # 垂直线方程 x = c
                    return math.inf, c
                else:
                    best_a, best_b = np.polyfit(inlier_points[:, 0], inlier_points[:, 1], 1)
                    return best_a, best_b
        else:
            raise ValueError("不支持的拟合方法")

    @staticmethod  # 将K,b直线转换到图像中的两点直线
    def _coeff2pts(coeff, w, h):
        '''
        coeff: coeff[0] * x + coeff[1] = y
        '''
        if not math.isinf(coeff[0]):
            pts = []
            sign = np.sign(coeff[0])
            if sign == 0:
                sign = 1
            inv_k = sign * 1 / max(np.abs(coeff[0]), 0.0001)
            x0 = 0
            y0 = coeff[1]
            if y0 >= 0 and y0 <= h - 1:
                pts.append((x0, y0))
            y0 = 0
            x0 = - coeff[1] * inv_k
            if x0 >= 0 and x0 <= w - 1:
                pts.append((x0, y0))
            if len(pts) == 2:
                pts = [pts[0][0], pts[0][1], pts[1][0], pts[1][1]]
                return pts
            x0 = w - 1
            y0 = coeff[0] * x0 + coeff[1]
            if y0 >= 0 and y0 <= h - 1:
                pts.append((x0, y0))
            if len(pts) == 2:
                pts = [pts[0][0], pts[0][1], pts[1][0], pts[1][1]]
                return pts
            y0 = h - 1
            x0 = (y0 - coeff[1]) * inv_k
            if x0 >= 0 and x0 <= w - 1:
                pts.append((x0, y0))
            pts = [pts[0][0], pts[0][1], pts[1][0], pts[1][1]]
        else:
            pts = [coeff[1], 0, coeff[1], h]

        return pts

    @staticmethod
    def fit_circle(points, method='ransac', iterations=1000, threshold=5):
        """
        拟合圆函数
        参数:
            points: numpy数组(N,2)，每行表示一个点的(x,y)坐标
            method: 拟合方法('least_squares'或'ransac')
            kwargs: 方法特定参数
                - ransac: iterations(迭代次数), threshold(内点阈值)
        返回:
            (cx, cy, radius) 圆心坐标和半径
        """
        if method == 'least_squares':
            """最小二乘法拟合圆"""
            x = points[:, 0]
            y = points[:, 1]
            n = len(points)
            # 构建线性方程组
            A = np.column_stack([2 * x, 2 * y, np.ones(n)])
            b = x ** 2 + y ** 2
            c = np.linalg.lstsq(A, b, rcond=None)[0]
            # 计算圆心和半径
            cx, cy = c[0], c[1]
            radius = np.sqrt(c[2] + cx ** 2 + cy ** 2)
            return (cx, cy, radius)
        elif method == 'ransac':
            """RANSAC方法拟合圆"""
            best_circle = None
            best_inliers = 0
            for _ in range(iterations):
                # 随机采样3个点
                sample = points[random.sample(range(len(points)), 3)]

                # 计算圆参数
                try:
                    A = np.array([
                        [2 * (sample[1, 0] - sample[0, 0]), 2 * (sample[1, 1] - sample[0, 1])],
                        [2 * (sample[2, 0] - sample[0, 0]), 2 * (sample[2, 1] - sample[0, 1])]
                    ])
                    B = np.array([
                        sample[1, 0] ** 2 + sample[1, 1] ** 2 - sample[0, 0] ** 2 - sample[0, 1] ** 2,
                        sample[2, 0] ** 2 + sample[2, 1] ** 2 - sample[0, 0] ** 2 - sample[0, 1] ** 2
                    ])
                    cx, cy = np.linalg.solve(A, B)
                    radius = np.sqrt((sample[0, 0] - cx) ** 2 + (sample[0, 1] - cy) ** 2)
                except:
                    continue
                # 统计内点数量
                distances = np.abs(np.sqrt((points[:, 0] - cx) ** 2 + (points[:, 1] - cy) ** 2) - radius)
                inliers = np.sum(distances < threshold)
                if inliers > best_inliers:
                    best_inliers = inliers
                    best_circle = (cx, cy, radius)
            return best_circle if best_circle is not None else (0, 0, 0)
        else:
            raise ValueError("不支持的拟合方法")

    @staticmethod  # 按点集拟合平面
    def ltsq_plane(ptzs):
        '''
        拟合平面
        :param ptz_list: 每个元素是(x, y, z)
        :return:
        '''
        (rows, cols) = ptzs.shape
        G = np.ones((rows, 3))
        G[:, 0] = ptzs[:, 0]  # X
        G[:, 1] = ptzs[:, 1]  # Y
        items = np.linalg.lstsq(G, ptzs[:, 2], rcond=None)
        a, b, d = items[0]
        c = -1.0
        d = d
        coeff = [a, b, c, d]
        return coeff

    @staticmethod  # 将掩码区域转换成（x,y,z）点集
    def mask2ptzs(image, mask, x_upp, y_upp, z_upp, have_org=False):
        if len(image.shape) > 2:
            image = image[:, :, 0]
        if len(mask.shape) > 2:
            mask = mask[:, :, 0]

        idx = np.where(np.logical_and(mask > 0, image > -50))
        # zs = (image[idx]+20*1000)*65535/2000/20
        zs = image[idx]
        # print(zs,'****',flush=True)
        pts = np.stack(idx).transpose()
        num = pts.shape[0]
        ptzs = np.zeros((num, 3))
        ptzs[:, 0] = pts[:, 1]
        ptzs[:, 1] = pts[:, 0]
        ptzs[:, 2] = zs
        normed_ptzs = np.zeros_like(ptzs)
        normed_ptzs[:, 0] = ptzs[:, 0] * x_upp
        normed_ptzs[:, 1] = ptzs[:, 1] * y_upp
        normed_ptzs[:, 2] = ptzs[:, 2] * z_upp
        if have_org == False:
            return normed_ptzs
        else:
            return normed_ptzs, ptzs

    @staticmethod  # 按掩码拟合平面
    def fit_plane_by_mask(image, mask, iter_num=1, x_upp=1, y_upp=1, z_upp=1):
        # mask = np.clip(max=1)
        if mask is None:
            return []
        t = time.time()
        ptzs = ImageProcess.mask2ptzs(image, mask, x_upp, y_upp, z_upp)
        for i in range(iter_num):
            tt = time.time()
            coeffs = ImageProcess.ltsq_plane(ptzs)

            # dists = flatness_by_pts._dist_ptzs_plane(ptzs, coeffs)
            # # pdb.set_trace()
            # ids = np.argsort(np.abs(dists))
            # num = len(dists)
            # ptzs = ptzs[ids[:-int(num * 0.1)]]
        return coeffs

    @staticmethod  # 按掩码拟合平面
    def fit_plane_by_ptzs(ptzs, x_upp=1, y_upp=1, z_upp=1):
        mask = ptzs[:, 2] > -50
        # 应用掩码过滤数组
        filtered_ptzs = ptzs[mask]
        assert filtered_ptzs.shape[0] > 2, '拟合平面的点数小于3!'
        normed_ptzs = np.zeros_like(filtered_ptzs)
        normed_ptzs[:, 0] = filtered_ptzs[:, 0] * x_upp
        normed_ptzs[:, 1] = filtered_ptzs[:, 1] * y_upp
        normed_ptzs[:, 2] = filtered_ptzs[:, 2] * z_upp
        coeffs = ImageProcess.ltsq_plane(ptzs)
        return coeffs

    @staticmethod  # 计算点集中每个点到平面的距离
    def dist_ptzs2plane(ptzs, coeffs):
        a, b, c, d = coeffs
        normal = max(0.0001, np.sqrt(a * a + b * b + c * c))
        dists = []
        num, _ = ptzs.shape
        for i in range(num):
            ptz = ptzs[i]
            dist = (a * ptz[0] + b * ptz[1] + c * ptz[2] + d) / normal
            dists.append(dist)
        return dists

    @staticmethod  # 按距离筛选点云到几何平面的所有点和mask
    def find_pts_by_pcd2plane(point_cloud, plane_params, threshold=1e-3):
        """
        计算点云数据与平面的交线坐标
        参数:
            point_cloud: 二维高度矩阵(32位浮点型)
            plane_params: 平面方程系数(A,B,C,D), 对应Ax+By+Cz+D=0
            threshold: 交点判定阈值
        返回:
            (N,2)数组, 包含交点的x,y坐标(矩阵索引)
        """
        A, B, C, D = plane_params
        height, width = point_cloud.shape
        x_indices, y_indices = np.meshgrid(np.arange(width), np.arange(height))
        # 计算每个点到平面的距离
        distances = A * x_indices * 0.012 + B * y_indices * 0.1 + C * point_cloud + D
        distances /= np.sqrt(A ** 2 + B ** 2 + C ** 2)  # 归一化

        # 寻找距离接近零的点(潜在交点)
        candidate_mask = distances < threshold
        mask = np.zeros_like(point_cloud, dtype=np.uint8)
        mask[candidate_mask] = 255
        candidate_points = np.column_stack((x_indices[candidate_mask],
                                            y_indices[candidate_mask]))
        # 精确插值定位(提高精度)
        return candidate_points, mask

    @staticmethod  # 生成矩形掩码和坐标点
    def gen_maskPts_by_rect(image, rect):
        """
        根据深度图像和矩形列表生成掩码及矩形区域内所有点的 (x, y, z) 坐标。
        :param image: 深度图像，形状为 (H, W) 或 (H, W, C)，会自动取单通道
        :param rect: 矩形列表，每个元素为 [x, y, w, h]，支持多个矩形
        :return: dict 包含 'mask' 和 'pt_xyz'
                 mask: (H, W) uint8 二值掩码
                 pt_xyz: (N, 3) float32 数组，每行为 [x, y, z]
        """
        assert len(rect) > 0, '生成掩码的矩形个数需大于0！'
        if len(image.shape) == 3:
            depth = image[:, :, 0].astype(np.float32)  # 提取第一通道作为深度
        else:
            depth = image.astype(np.float32)
        h, w = depth.shape
        mask = np.zeros((h, w), dtype=np.uint8)
        # 存储所有符合条件的 (x, y) 坐标
        coords = np.zeros((len(rect), 3)) - 100
        for idx, rect_ in enumerate(rect):
            if len(rect_) == 0:
                continue
            x, y, w_, h_ = rect_
            x1 = max(0, int(x))
            y1 = max(0, int(y))
            x2 = min(w, int(x + w_))
            y2 = min(h, int(y + h_))
            if x1 >= x2 or y1 >= y2:
                continue
            # 绘制掩码
            mask[y1:y2, x1:x2] = 255
            X = (x1 + x2) / 2
            Y = (y1 + y2) / 2
            Z = np.mean(depth[y1:y2, x1:x2])
            # 展平并添加到列表
            coords[idx, :] = X, Y, Z
        return {
            'mask': mask,
            'pt_xyz': coords
        }

    @staticmethod  ## 生成圆环掩码
    def gen_mask_by_rings(image, inner_radius, outter_radius, center, inner_pad, outter_pad):
        one_ret = {
            'mask': [],
        }
        h, w = image.shape[:2]
        if len(image.shape) == 3:
            image = image[:, :, 0]
        if len(center[0]) == 0:
            return one_ret
        cent = (int(center[0][1]), int(center[0][2]))
        # 扩展区域
        in_mask = np.ones((h, w), np.uint8)
        in_pr = int(max(0, inner_radius - inner_pad))
        in_mask = cv2.circle(in_mask, cent, in_pr, 0, -1)
        out_mask = np.zeros((h, w), np.uint8)
        out_pr = int(outter_radius + outter_pad)
        out_mask = cv2.circle(out_mask, cent, out_pr, 1, -1)
        # 计算区域
        in_mask = np.ones((h, w), np.uint8)
        in_pr = int(max(0, inner_radius))
        in_mask = cv2.circle(in_mask, cent, in_pr, 0, -1)
        out_mask = np.zeros((h, w), np.uint8)
        out_pr = int(outter_radius)
        out_mask = cv2.circle(out_mask, cent, out_pr, 1, -1)
        mask = np.logical_and(in_mask, out_mask) * 255
        one_ret['mask'] = mask
        return one_ret

    @staticmethod  # 将(x1,y1,x2,y2)的直线 转换为Ax+By+C=0的直线 返回(A,B,C)     2D测量
    def getLinearEquation(line):
        _, p1x, p1y, p2x, p2y = line
        sign = 1
        a = p2y - p1y
        if a < 0:
            sign = -1
            a = sign * a
        b = sign * (p1x - p2x)
        c = sign * (p1y * p2x - p1x * p2y)
        return (a, b, -c)

    @staticmethod  # 获取直线过矩形框的交点
    def getInnerRectLine(line, rectangle_point):
        intersection_list = []
        point1, point2 = line[0:2], line[2:4]
        a, b, c = ImageProcess.getLinearEquation(line)
        rectangle_point = rectangle_point[0][0][1:-1]
        rectangle_point = [rectangle_point[0], rectangle_point[1], rectangle_point[0] + rectangle_point[2],
                           rectangle_point[1] + rectangle_point[3]]
        x_list = [rectangle_point[0], rectangle_point[2]]
        y_list = [rectangle_point[1], rectangle_point[3]]
        if b == 0:
            y = point1[-1]
            if y_list[0] <= y <= y_list[1]:
                intersection_list.extend([(point1[0], y_list[0]), (point2[0], y_list[1])])
        elif a == 0:
            x = point1[0]
            if x_list[0] <= x <= x_list[1]:
                intersection_list.extend([(x_list[0], point1[1]), (x_list[1], point1[1])])
        else:
            for x in x_list:
                y = (c - a * x) / b
                if rectangle_point[1] <= y <= rectangle_point[3]:
                    intersection_list.append((x, y))
            for y in y_list:
                x = (c - b * y) / a
                if rectangle_point[0] <= x <= rectangle_point[2]:
                    intersection_list.append((x, y))
        try:
            lineSeg = [intersection_list[0][0], intersection_list[0][1], intersection_list[1][0],
                       intersection_list[1][1]]
        except Exception as e:
            lineSeg = line[1:]
        return lineSeg

    @staticmethod  # 获取两条直线y=kx+b 类型的交点
    def cross_point_kb(k1, b1, k2, b2):
        x = (b2 - b1) * 1.0 / (k1 - k2)
        y = k1 * x * 1.0 + b1 * 1.0
        return x, y

    @staticmethod  # 获取两条直线[x1,y1,x2,y2]类型的交点
    def compute_cross_point(line1, line2):  # 计算交点函数
        x1 = line1[0]  # 取四点坐标
        y1 = line1[1]
        x2 = line1[2]
        y2 = line1[3]
        x3 = line2[0]
        y3 = line2[1]
        x4 = line2[2]
        y4 = line2[3]
        if x2 != x1:
            k1 = (y2 - y1) * 1.0 / (x2 - x1)  # 计算k1,由于点均为整数，需要进行浮点数转化
            b1 = y1 * 1.0 - x1 * k1 * 1.0  # 整型转浮点型是关键
        else:
            k1 = None
            b1 = 0
        if (x4 - x3) == 0:  # L2直线斜率不存在操作
            k2 = None
            b2 = 0
        else:
            k2 = (y4 - y3) * 1.0 / (x4 - x3)  # 斜率存在操作
            b2 = y3 * 1.0 - x3 * k2 * 1.0

        if k1 == None and k2 == None:
            x = (x1 + x3) / 2
            return None, x
        elif k2 == None:
            x = x3
            y = k1 * x * 1.0 + b1 * 1.0
        elif k1 == None:
            x = x1
            y = k2 * x * 1.0 + b2 * 1.0
        elif k1 != k2:
            x = (b2 - b1) * 1.0 / (k1 - k2)
            y = k1 * x * 1.0 + b1 * 1.0
        elif k1 == k2:
            mid1 = [(x1 + x3) / 2, (y1 + y3) / 2]
            mid2 = [(x1 + x4) / 2, (y1 + y4) / 2]
            mid3 = [(x2 + x3) / 2, (y2 + y3) / 2]
            mid4 = [(x2 + x4) / 2, (y2 + y4) / 2]
            listPoints = [mid1, mid2, mid3, mid4]
            sortList = sorted(listPoints, key=lambda x: x[0])
            midline = [sortList[0][0], sortList[0][1], sortList[-1][0], sortList[-1][1]]
            return midline, None
        return x, y

    @staticmethod  # 获取两条直线[x1,y1,x2,y2]类型的交点
    def point_to_line_distance(pts, k, b):
        """
        计算点到直线的距离
        :param pts: 点集，numpy数组，形状为(n,2)
        :param k: 直线斜率
        :param b: 直线截距
        :return: 距离列表
        """
        # 将直线方程转换为一般式：kx - y + b = 0
        A = k
        B = -1
        C = b

        # 提取点的x和y坐标
        x = pts[:, 0]
        y = pts[:, 1]

        # 计算分子 |Ax + By + C|
        numerator = A * x + B * y + C

        # 计算分母 sqrt(A^2 + B^2)
        denominator = np.sqrt(A ** 2 + B ** 2)

        # 计算距离
        distances = numerator / denominator

        return distances

    @staticmethod  # 获取两条直线的中线
    def getMidLine(line1, line2):
        x, y = ImageProcess.cross_point(line1, line2)
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
        if x is not None and y is not None:
            x0, y0 = x, y
            midLine = ImageProcess._bisectorLine_of_angle(x0, y0, line1, line2)
        elif x is None:
            midLine = [y, min([y1, y2, y3, y4]), y, max([y1, y2, y3, y4])]
        elif y is None:
            midLine = x
        return midLine

    @staticmethod  # 计算点到直线的距离 直线 [x1,y1,x2,y2]
    def dist_pt2line(point, line):
        """
        点到线段的距离
        Args:
            point: [x0, y0]
            line: [x1, y1, x2, y2]
        """
        line_point1, line_point2 = np.array(line[0:2]), np.array(line[2:])
        vec1 = line_point1 - point
        vec2 = line_point2 - point
        distance = np.abs(np.cross(vec1, vec2)) / np.linalg.norm(line_point1 - line_point2)
        return distance

    @staticmethod  # 按数量均匀提取直线上的点
    def ExtractLinePoint(line, ptsNum=10):
        x0, y0, x1, y1 = line
        halfNum = int(ptsNum // 2)
        if x0 != x1:
            k = (y1 - y0) / (x1 - x0)
            b = y0 - k * x0
            if x1 > x0:
                midx = (x1 + x0) / 2
                xleftPoints = np.linspace(x0, midx, halfNum, endpoint=False)
                xrightPoints = np.linspace(midx, x1, halfNum, endpoint=False)
                xPoints = np.append(xleftPoints, midx)
                xPoints = np.append(xPoints, xrightPoints[1:])
                xPoints = np.append(xPoints, x1)
            else:
                midx = (x1 + x0) / 2
                xleftPoints = np.linspace(x1, midx, halfNum, endpoint=False)
                xrightPoints = np.linspace(midx, x0, halfNum, endpoint=False)
                xPoints = np.append(xleftPoints, midx)
                xPoints = np.append(xPoints, xrightPoints[1:])
                xPoints = np.append(xPoints, x0)
            yPoints = xPoints * k + b
        else:
            if y1 > y0:
                yPoints = np.linspace(y0, y1, ptsNum + 2, endpoint=False)
            else:
                yPoints = np.linspace(y1, y0, ptsNum + 2, endpoint=False)
            xPoints = np.linspace(x0, x0, ptsNum + 2, endpoint=False)
        points = np.stack([xPoints, yPoints], axis=1)
        return points

    @staticmethod  # 计算两条直线的距离
    def LineDistance(Line1, Line2, ptsNum=10):
        points1 = ImageProcess.ExtractLinePoint(Line1, ptsNum)
        points2 = ImageProcess.ExtractLinePoint(Line2, ptsNum)
        allDist = []
        for pt1, pt2 in zip(points1, points2):
            dist1 = ImageProcess.dist_pt2line(pt1, Line2)
            dist2 = ImageProcess.dist_pt2line(pt2, Line1)
            allDist.append(dist1)
            allDist.append(dist2)
        aveDist = np.mean(allDist)
        return aveDist

    @staticmethod  # 计算点到直线的距离 直线方程:y=kx+b
    def dist_pt2kbline(outpoint, datum_k, datum_b):
        top_val = datum_k * outpoint[0] - outpoint[1] + datum_b
        down_val = np.sqrt(datum_k ** 2 + 1)
        return abs(top_val / down_val)

    @staticmethod  # 计算点到直线的距离 直线方程:y=kx+b
    def dist_pts2kbline(outpoint, datum_k, datum_b):
        top_val = datum_k * outpoint[:, 0] - outpoint[:, 1] + datum_b
        down_val = np.sqrt(datum_k ** 2 + 1)
        return np.abs(top_val / down_val)

    @staticmethod  # 过滤掉边缘点集中相邻距离比较大的点
    def filter_points(pts, diff=3, expand=5, iter=1, min_pts_num=50):
        flag = 0
        while iter > 0:
            pts = list(pts)
            length = len(pts)
            disLst = []
            for idx in range(-1, -length + 1, -1):
                pt = pts[idx]
                next_pt = pts[idx - 1]
                dis = np.sqrt((next_pt[1] - pt[1]) ** 2 + (next_pt[0] - pt[0]) ** 2)
                disLst.insert(0, dis)
            arrLst = np.array(disLst)
            index_ = np.where(arrLst > diff + flag * expand)
            if len(index_[0]) > 0:
                c = index_[0] + 1
                expand_c = []
                for anchor in c:
                    expand_num = expand - flag
                    if expand_num > 0:
                        for ggg in range(expand_num):
                            if anchor - ggg > 0:
                                expand_c.append(anchor - ggg)
                            if anchor + ggg < length:
                                expand_c.append(anchor + ggg)
                    else:
                        expand_c = c
                        break
                setexpandc = set(expand_c)
                final_c = sorted(list(setexpandc), reverse=True)
                for ind in final_c:
                    pts.pop(ind)
                    if ind < length - 10:
                        roi_pts = pts[ind:ind + 5]
                        area_dis = []
                        for area_idx in range(-1, -len(roi_pts) + 1, -1):
                            pt = pts[area_idx]
                            next_pt = pts[area_idx - 1]
                            dis = np.sqrt((next_pt[1] - pt[1]) ** 2 + (next_pt[0] - pt[0]) ** 2)
                            area_dis.insert(0, dis)
                        area_dis = np.array(area_dis)
                        index_ = np.where(area_dis > diff + flag * expand)
                        #
                        if len(index_[0]) > 1:
                            d = index_[0] + 1
                            expand_d = []
                            for anchor in d:
                                expand_num = 1
                                for ggg in range(expand_num):
                                    if anchor + ggg < length:
                                        expand_d.append(anchor + ggg)
                            setexpandd = set(expand_d)
                            final_d = sorted(list(setexpandd), reverse=True)
                            for inde in final_d:
                                pts.pop(inde)
            if len(pts) < min_pts_num:
                break
            flag += 1
            iter -= 1
        #  todo 连接相邻断点
        # constant_pts = []
        # for pt_idx in range(len(pts) - 1):
        #     dist = np.sqrt((pts[pt_idx + 1][1] - pts[pt_idx][1]) ** 2 + (pts[pt_idx + 1][0] - pts[pt_idx][0]) ** 2)
        #     if dist < diff:
        #         constant_pts.append(pts[pt_idx])
        #     else:
        #         x1, y1 = pts[pt_idx + 1]
        #         x0, y0 = pts[pt_idx]
        #         k_ = (y1 - y0) / (x1 - x0)
        #         if abs(x1 - x0) > abs(y1 - y0):
        #             x_ = np.linspace(x0 // 1, x1 // 1, abs(int(x1 - x0)), endpoint=False)
        #             b = y1 - k_ * x1
        #             y_ = x_ * k_ + b
        #             points = np.stack([x_, y_], axis=1)[1:]
        #         else:
        #             y_ = np.linspace(y0 // 1, y1 // 1, abs(int(y1 - y0)), endpoint=False)
        #             b = y1 - k_ * x1
        #             x_ = (y_ - b) / k_
        #             points = np.stack([x_, y_], axis=1)[1:]
        #         for add_pt in points:
        #             constant_pts.append(add_pt)
        #     # print(constant_pts)
        # pdb.set_trace()
        return pts

    @staticmethod  # 将矩形框的四个顶点进行排序，最终顺序为（左下,左上,右上,右下)
    def order_points(pts):
        xSorted = pts[np.argsort(pts[:, 0]), :]
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]
        if leftMost[0, 1] != leftMost[1, 1]:
            leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        else:
            leftMost = leftMost[np.argsort(leftMost[:, 0])[::-1], :]
        (tl, bl) = leftMost
        if rightMost[0, 1] != rightMost[1, 1]:
            rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
        else:
            rightMost = rightMost[np.argsort(rightMost[:, 0])[::-1], :]
        (tr, br) = rightMost
        return np.array([tl, tr, br, bl], dtype="float32")

    @staticmethod  # 绘制中文字体
    def draw_text(img, text, pos, font_size=60, line_spacing=10):
        font_path = os.path.dirname(__file__) + os.sep + 'SimHei.ttf'
        # 转换OpenCV图像为PIL格式
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype(font=font_path, size=font_size)
        draw = ImageDraw.Draw(img_pil)
        x, y = pos
        for line in text.split('\\n'):
            if '#' in line:
                color_str, one_text = line.split('#')
                nums = color_str.strip("()").split(",")
                draw.text((x, y), one_text, font=font, fill=tuple(int(num) for num in nums))
                y += font_size + line_spacing  # 更新y坐标实现换行

        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    @staticmethod  # 读取中文路径图像
    def cv_read_chinese(path, flag=-1):
        # 读取原始二进制数据
        raw_data = np.fromfile(path, dtype=np.uint8)
        # 保持原始数据类型（浮点型）
        img = cv2.imdecode(raw_data, flags=cv2.IMREAD_UNCHANGED)  # 或 flags=-1
        return img

    @staticmethod  # 保存中文路径图像
    def cv_imwrite_chinese(path, img, quality=95):
        # 根据文件扩展名设置编码格式
        ext = path.split('.')[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            # 编码并写入文件
            success, encoded_img = cv2.imencode(f'.{ext}', img, encode_param)
            if success:
                encoded_img.tofile(path)
            return success
        elif ext == 'tif' or ext == 'tiff':
            tifffile.imwrite(path, img)
        else:
            encode_param = []
            success, encoded_img = cv2.imencode(f'.{ext}', img, encode_param)
            if success:
                encoded_img.tofile(path)
            return success

    @staticmethod  # 绘制矩形
    def draw_defect_pts(img, ret, name=''):
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
        return draw

    @staticmethod  # 寻找上边缘
    def find_top_edge(src_img, inv):
        h, w = src_img.shape[:2]
        if inv:
            sum_top = np.sum(src_img, axis=1) / 255
            high_black_col_all = np.where(sum_top < w / 2)  # 从这里选出小于num像素点个数的横坐标
            low_black_col_all_top = np.where(sum_top == w)  # 从这里选出最小全255像素点的横坐标
            top_sum = 0
            top_aver = 0
            if low_black_col_all_top[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                top_aver = -1
            else:
                high_black_col_top = np.max(high_black_col_all)
                low_black_col_top = min(high_black_col_top + 1, h - 1)
                top_sum = top_sum + high_black_col_top * sum_top[high_black_col_top]
                top_sum = top_sum + low_black_col_top * (w - sum_top[high_black_col_top])
                top_aver = top_sum / w
        else:
            sum_top = np.sum(src_img, axis=1) / 255
            high_black_col_all = np.where(sum_top == 0)  # 从这里选出小于num像素点个数的横坐标
            low_black_col_all_top = np.where(sum_top == w)  # 从这里选出最小全255像素点的横坐标
            top_sum = 0
            top_aver = 0
            if low_black_col_all_top[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                top_aver = -1
            else:
                high_black_col_top = np.max(high_black_col_all)
                low_black_col_top = min(high_black_col_top + 1, h - 1)
                top_sum = top_sum + low_black_col_top * (w - sum_top[low_black_col_top])
                top_sum = top_sum + high_black_col_top * (sum_top[low_black_col_top])
                top_aver = top_sum / w
        return top_aver

    @staticmethod  # 寻找下边缘
    def find_down_edge(src_img, inv):
        h, w = src_img.shape[:2]
        if inv:
            sum_down = np.sum(src_img, axis=1) / 255
            high_black_col_all = np.where(sum_down < w / 2)
            down_sum = 0
            down_aver = 0
            low_black_col_all = np.where(sum_down == w)
            if low_black_col_all[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                down_aver = -1
            else:
                high_black_col_down = np.min(high_black_col_all)
                low_black_col_down = max(high_black_col_down - 1, 0)  # 纯白

                down_sum = down_sum + high_black_col_down * sum_down[high_black_col_down]
                down_sum = down_sum + (w - sum_down[high_black_col_down]) * low_black_col_down
                down_aver = down_sum / w
        else:
            sum_down = np.sum(src_img, axis=1) / 255
            high_black_col_all = np.where(sum_down == 0)
            down_sum = 0
            down_aver = 0
            low_black_col_all = np.where(sum_down == w)
            if low_black_col_all[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                down_aver = -1
            else:
                high_black_col_down = np.min(high_black_col_all)
                low_black_col_down = max(high_black_col_down - 1, 0)
                down_sum = down_sum + low_black_col_down * (w - sum_down[low_black_col_down])
                down_sum = down_sum + sum_down[low_black_col_down] * high_black_col_down
                down_aver = down_sum / w
        return down_aver

    @staticmethod  # 寻找左边缘
    def find_left_edge(src_img, inv):
        h, w = src_img.shape[:2]
        if inv:
            sum_right = np.sum(src_img, axis=0) / 255
            high_black_col_all = np.where(sum_right < h / 2)  # 从这里选出最小的横坐标1
            low_black_col_all_right = np.where(sum_right == h)  # 从这里选出最小的横坐标2
            right_sum = 0
            left_aver = 0
            if low_black_col_all_right[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                left_aver = -1
            else:
                high_black_col_right = np.max(high_black_col_all)
                low_black_col_right = min(high_black_col_right + 1, w - 1)
                right_sum = right_sum + high_black_col_right * sum_right[high_black_col_right]
                right_sum = right_sum + low_black_col_right * (h - sum_right[high_black_col_right])
                left_aver = right_sum / h
        else:
            sum_right = np.sum(src_img, axis=0) / 255
            high_black_col_all = np.where(sum_right == 0)  # 从这里选出最小的横坐标1
            low_black_col_all_right = np.where(sum_right == h)  # 从这里选出最小的横坐标2
            right_sum = 0
            left_aver = 0
            if low_black_col_all_right[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                left_aver = -1
            else:
                high_black_col_right = np.max(high_black_col_all)
                low_black_col_right = min(high_black_col_right + 1, w - 1)
                right_sum = right_sum + low_black_col_right * (h - sum_right[low_black_col_right])
                right_sum = right_sum + high_black_col_right * sum_right[low_black_col_right]
                left_aver = right_sum / h

        return left_aver

    @staticmethod  # 寻找右边缘
    def find_right_edge(src_img, inv):
        h, w = src_img.shape[:2]
        if inv:
            sum_left = np.sum(src_img, axis=0) / 255
            high_black_col_all = np.where(sum_left < h / 2)  # 从这里选出包涵0像素的列的横坐标1
            low_black_col_all = np.where(sum_left == h)  # 从这里选出列只为0像素的横坐标2
            left_sum = 0
            right_aver = 0
            if low_black_col_all[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                right_aver = -1
            else:
                high_black_col_left = np.min(high_black_col_all)
                low_black_col_left = max(high_black_col_left - 1, 0)
                left_sum = left_sum + high_black_col_left * sum_left[high_black_col_left]
                left_sum = left_sum + (h - sum_left[high_black_col_left]) * low_black_col_left
                right_aver = left_sum / h
        else:
            sum_left = np.sum(src_img, axis=0) / 255
            high_black_col_all = np.where(sum_left == 0)  #
            low_black_col_all = np.where(sum_left == h)  # 从这里选出列只为0像素的横坐标2
            left_sum = 0
            right_aver = 0
            if low_black_col_all[0].shape[0] < 3 or high_black_col_all[0].shape[0] < 3:
                right_aver = -1
            else:
                high_black_col_left = np.min(high_black_col_all)
                low_black_col_left = max(high_black_col_left - 1, 0)
                left_sum = left_sum + low_black_col_left * (h - sum_left[low_black_col_left])
                left_sum = left_sum + sum_left[low_black_col_left] * high_black_col_left
                right_aver = left_sum / h
        return right_aver

    @staticmethod  # 标准化向量
    def _normalize(x, y):
        dis = math.sqrt(x ** 2 + y ** 2)
        return x / dis, y / dis

    @staticmethod  # 计算角平分线已知p0p1和p0p2，计算角平分线上指定距离的一个点
    def _bisectorLine_of_angle(x0, y0, line1, line2):
        x1, y1, x3, y3 = line1
        x2, y2, _, _ = line2
        x01, y01 = ImageProcess._normalize(x1 - x0, y1 - y0)  # 标准化向量p0p1
        x02, y02 = ImageProcess._normalize(x2 - x0, y2 - y0)  # 标准化向量p0p2
        x, y = ImageProcess._normalize((x01 + x02) / 2, (y01 + y02) / 2)  # 计算角平分线的标准化向量
        dis1 = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        dis2 = np.sqrt((x3 - x0) ** 2 + (y3 - y0) ** 2)
        p2 = (x0 + x * dis1, y0 + y * dis1)
        p1 = (x0 + x * dis2, y0 + y * dis2)
        return [p1[0], p1[1], p2[0], p2[1]]  # 按指定长度计算角平分线上的点

    @staticmethod  # 极坐标下的点转换到笛卡尔坐标
    def polar_to_cartesian(polar_points, center, min_radius, max_radius, polar_img_shape):
        """
        将极坐标下的点映射回笛卡尔坐标系
        :param polar_points: 极坐标下的点列表[(r, theta)]或ndarray
        :param center: 原图圆心坐标(x,y)
        :param min_radius: 极坐标转换时使用的最小半径
        :param max_radius: 极坐标转换时使用的最大半径
        :param polar_img_shape: 极坐标图像的形状(height, width)
        :return: 笛卡尔坐标系下的点列表[(x,y)]
        """
        cartesian_points = []
        polar_height, polar_width = polar_img_shape

        for point in polar_points:
            x, y = point
            # 将像素坐标转换为极坐标(r, theta)
            r = min_radius + x  # 行对应半径
            theta = 2 * math.pi * y / polar_height  # 列对应角度(弧度)
            x_cart = center[0] + r * math.cos(theta)
            y_cart = center[1] + r * math.sin(theta)
            cartesian_points.append((x_cart, y_cart))
        return cartesian_points

    @staticmethod  # 极坐标转换
    def polar_transform(image, center, min_radius, max_radius):
        # 计算输出图像尺寸
        output_width = int(2 * np.pi * max_radius)  # 周长
        # 使用OpenCV内置函数 (flags=cv2.WARP_POLAR_LINEAR表示线性插值)
        polar_img = cv2.warpPolar(
            image,
            (max_radius, output_width),
            center,
            max_radius,
            cv2.WARP_POLAR_LINEAR
        )
        # 裁剪掉超出最小半径的部分
        if min_radius > 0:
            polar_img = polar_img[:, min_radius:]
        return polar_img


def ecd2tif(ecd_path, output_path):
    data = None
    data_info = None
    rc = -1
    if os.path.exists(ecd_path):
        with open(ecd_path, 'rb') as f:
            header = f.read(10240)
            info = struct.unpack("<Iiidd32s", header[:60])
            data_info = {
                "version": info[0],
                "width": info[1],
                "height": info[2],
                "xInterval": info[3],
                "yInterval": info[4],
                "Info": info[5]
            }
            print(data_info)
            data = []
            width_size = data_info['width'] * 4
            for _ in range(data_info['height']):
                buf = f.read(width_size)
                for j in range(0, width_size, 4):
                    data.append(struct.unpack('i', buf[j:j + 4])[0] / 100000)
            data = np.array(data, dtype=np.float32).reshape(data_info['height'], data_info['width'])
            tifffile.imwrite(output_path, data)
            print(f"TIFF文件已保存至 {output_path}")
            rc = 0

    return rc, data_info, data


class show_3d:
    def __init__(self):
        self.w, self.h = 600, 2500

    def get_img(self, path):
        self.old_img = img = ImageProcess.cv_read_chinese(path)
        if self.old_img is None:
            raise Exception('深度图读取失败')
        print('深度图尺寸:', self.old_img.shape)
        # cv_img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
        # cv_img = cv_img.astype(np.uint8)
        cv_img = ImageProcess.normlize2gray(img, min=-7, max=7)
        cv2.imwrite('_.jpg', cv_img)
        self.img = cv2.imread('_.jpg', 0)
        # self.img = cv2.equalizeHist(self.img) #直方图均衡化
        return self.img

    def mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            width = x
            height = y
            print('height,width', height, width)
            print('x坐标:', x, 'y坐标:', y, '高度:', self.old_img[height, width], '灰度值:', self.img[height, width]
                  # (self.old_img[height:height + 1, width:width + 1][0][0]) * 0.8 / 1000
                  )

    def get_depth_and_gray_img(self):
        return self.old_img, self.img

    def show(self, path, flag=False):
        img = self.get_img(path)
        if flag:
            cv2.namedWindow('img', cv2.WINDOW_NORMAL)
            cv2.setMouseCallback('img', self.mouse)
            cv2.resizeWindow('img', 400, 800)
            cv2.imshow('img', img)
            cv2.waitKey(0)


from skimage.feature import greycomatrix, greycoprops


class TextureMatcher:  # 灰度共生矩阵
    def __init__(self, ref_img_path, roi_rect):
        """
        :param ref_img_path: 基准图像路径
        :param roi_rect: (x,y,w,h)格式的目标区域矩形
        """
        self.ref_img = cv2.imread(ref_img_path, cv2.IMREAD_GRAYSCALE)
        self.roi = self.ref_img[roi_rect[1]:roi_rect[1] + roi_rect[3],
                   roi_rect[0]:roi_rect[0] + roi_rect[2]]
        self.ref_features = self._extract_glcm_features(self.roi)

    def _extract_glcm_features(self, img):
        """提取GLCM特征向量"""
        glcm = greycomatrix(img, [1], [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                            symmetric=True, normed=True)
        features = {
            'contrast': greycoprops(glcm, 'contrast').mean(),
            'homogeneity': greycoprops(glcm, 'homogeneity').mean(),
            'energy': greycoprops(glcm, 'energy').mean()
        }
        return features

    def _match_texture(self, img):
        """计算当前图像与基准特征的相似度"""
        test_features = self._extract_glcm_features(img)
        # 计算欧氏距离作为相似度指标
        distance = np.sqrt(sum(
            (self.ref_features[k] - test_features[k]) ** 2
            for k in self.ref_features.keys()
        ))
        return distance

    def detect_in_batch(self, test_dir, threshold=0.2):
        """批量检测目标位置"""
        results = {}
        for fname in os.listdir(test_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(test_dir, fname)
                test_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

                # 滑动窗口检测
                window_size = (self.roi.shape[1], self.roi.shape[0])
                step = 20  # 步长像素

                for y in range(0, test_img.shape[0] - window_size[1], step):
                    for x in range(0, test_img.shape[1] - window_size[0], step):
                        window = test_img[y:y + window_size[1], x:x + window_size[0]]
                        score = self._match_texture(window)

                        if score < threshold:
                            results.setdefault(fname, []).append((x, y, window_size[0], window_size[1]))
        return results


# if __name__ == "__main__":
#     # 初始化检测器（参数需根据实际图像调整）
#     matcher = TextureMatcher(
#         ref_img_path="reference.jpg",
#         roi_rect=(100, 150, 80, 60)  # (x,y,w,h)
#     )
#     # 批量检测测试目录
#     detections = matcher.detect_in_batch("test_images/", threshold=0.15)
#     # 可视化结果
#     for fname, boxes in detections.items():
#         img = cv2.imread(f"test_images/{fname}")
#         for (x, y, w, h) in boxes:
#             cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
#         cv2.imwrite(f"result_{fname}", img)

if __name__ == '__main__':
    import os
