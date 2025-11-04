import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from time import sleep
from typing import Union, Tuple, List, Optional, Dict, Any

import cnocr
import uiautomator2 as u2
import cv2
import numpy as np
from PIL import Image
from loguru import logger

# 添加CnOCR导入
try:
    from cnocr import CnOcr

    CNOCR_AVAILABLE = True
except ImportError:
    CNOCR_AVAILABLE = False
    logger.warning("CnOCR未安装，文字识别功能不可用")


class AutomationToolkit:
    """
    自动化测试工具包，提供设备控制、元素定位、图像识别等功能

    Args:
        device: 设备标识（IP地址或序列号）
        img_path: 图片资源路径
        task_id: 任务标识符
        debug_img: 调试图片保存路径
        sleep_time: 连接后等待时间
        max_retries: 最大重试次数
        is_sleep: 是否在连接后等待
        accidental_processing: 意外弹窗处理配置
    """

    def __init__(self, device: str, img_path: str, task_id: str = None,
                 debug_img: str = None, max_retries: int = 10,
                 accidental_processing: list = None) -> None:

        self.device = device
        self.task_id = task_id or "default"
        self.img_path = img_path
        self.debug_img = debug_img or "./debug_images"
        self.accidental_processing = accidental_processing
        self.last_debug_image = None

        # 创建必要的目录
        os.makedirs(self.debug_img, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)

        # 初始化OCR
        self.ocr_engine = cnocr.CnOcr()
        # 设备连接
        self._connect_device(max_retries)

    def _connect_device(self, max_retries: int) -> None:
        """连接设备"""
        start_time = time.time()
        for i in range(max_retries):
            try:
                self.d = u2.connect(self.device)
                total_time = time.time() - start_time
                logger.debug(f'成功连接到设备: {self.device}, 耗时: {total_time:.3f}s')
                break
            except Exception as e:
                logger.warning(f'第{i + 1}次连接失败: {e}')
                if i == max_retries - 1:
                    total_time = time.time() - start_time
                    raise ConnectionError(f'无法连接到设备 {self.device}, 总耗时: {total_time:.3f}s') from e
                sleep(1)

    def ocr_find_text(self, target_text: str,
                      region: Tuple[int, int, int, int] = None,
                      debug: bool = False) -> Union[Dict[str, Any], bool]:
        """
        使用OCR识别文字位置，计算目标文字在文本框内的精确位置
        简化版本：只在必要时进行字符修正
        """
        start_time = time.time()
        if self.ocr_engine is None:
            logger.error("OCR引擎未初始化，无法进行文字识别")
            return False

        # 精简的易混淆字符映射
        CONFUSING_CHARS = {
            '莱': '菜',
            '未': '末',
            '己': '已',
            '人': '入',
            '八': '入',
        }

        try:
            # 获取屏幕截图
            screenshot = self.d.screenshot(format='opencv')
            if screenshot is None:
                logger.error("无法获取屏幕截图")
                return False

            # 处理区域
            if region:
                x1, y1, x2, y2 = region
                height, width = screenshot.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(x1 + 1, min(x2, width))
                y2 = max(y1 + 1, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    logger.error(f"无效的区域设置: {region}")
                    return False

                region_screenshot = screenshot[y1:y2, x1:x2]
                region_offset = (x1, y1)
                ocr_screenshot = region_screenshot
            else:
                region_screenshot = screenshot
                region_offset = (0, 0)
                ocr_screenshot = screenshot

            # 转换为RGB
            if len(ocr_screenshot.shape) == 3 and ocr_screenshot.shape[2] == 3:
                region_screenshot_rgb = cv2.cvtColor(ocr_screenshot, cv2.COLOR_BGR2RGB)
            else:
                if len(ocr_screenshot.shape) == 2:
                    ocr_screenshot = cv2.cvtColor(ocr_screenshot, cv2.COLOR_GRAY2BGR)
                region_screenshot_rgb = cv2.cvtColor(ocr_screenshot, cv2.COLOR_BGR2RGB)

            # 使用OCR识别文字
            ocr_results = self.ocr_engine.ocr(region_screenshot_rgb)

            # 首先尝试直接匹配
            for result in ocr_results:
                if isinstance(result, dict) and 'text' in result:
                    text = result['text']
                    confidence = result.get('score', 0.0)
                    position = result.get('position', [])

                    if target_text in text:
                        logger.debug(f"直接匹配到目标文字 '{target_text}' 在文本: '{text}'")
                        target_position = self._calculate_target_text_position(
                            text, target_text, position, region_offset, screenshot.shape
                        )

                        result_info = {
                            'text': text,
                            'target_text': target_text,
                            'confidence': confidence,
                            'position': position,
                            'target_position': target_position,
                            'screen_position': target_position['screen_position'],
                            'center_point': target_position['screen_position']['center'],
                            'region': region,
                            'region_offset': region_offset,
                            'corrected': False
                        }

                        total_time = time.time() - start_time
                        logger.info(
                            f"{self.task_id}--找到目标文字: '{target_text}' "
                            f"(在文字 '{text}' 中), 置信度: {confidence:.3f}, "
                            f"总耗时: {total_time:.3f}s"
                        )

                        if debug:
                            self._save_ocr_debug_image(
                                ocr_screenshot, result, target_position['screen_position'],
                                target_text, region_offset
                            )

                        return result_info

            # 检查目标文字是否需要字符修正
            needs_correction = False
            for char in target_text:
                if char in CONFUSING_CHARS.values():
                    needs_correction = True
                    break

            # 只有在目标文字包含需要修正的字符时才进行修正匹配
            if needs_correction:
                for result in ocr_results:
                    if isinstance(result, dict) and 'text' in result:
                        original_text = result['text']
                        confidence = result.get('score', 0.0)
                        position = result.get('position', [])

                        # 修正易混淆字符
                        corrected_text = original_text
                        for wrong_char, correct_char in CONFUSING_CHARS.items():
                            corrected_text = corrected_text.replace(wrong_char, correct_char)

                        # 检查修正后的文本是否包含目标文字
                        if corrected_text != original_text and target_text in corrected_text:
                            logger.debug(f"通过字符修正找到目标: '{original_text}' -> '{corrected_text}'")

                            target_position = self._calculate_target_text_position(
                                corrected_text, target_text, position, region_offset, screenshot.shape
                            )

                            result_info = {
                                'text': corrected_text,
                                'target_text': target_text,
                                'confidence': confidence,
                                'position': position,
                                'target_position': target_position,
                                'screen_position': target_position['screen_position'],
                                'center_point': target_position['screen_position']['center'],
                                'region': region,
                                'region_offset': region_offset,
                                'corrected': True,
                                'original_text': original_text
                            }

                            total_time = time.time() - start_time
                            logger.info(
                                f"{self.task_id}--通过字符修正找到目标文字: '{target_text}' "
                                f"(原文本: '{original_text}', 修正后: '{corrected_text}'), "
                                f"总耗时: {total_time:.3f}s"
                            )

                            if debug:
                                self._save_ocr_debug_image(
                                    ocr_screenshot, result, target_position['screen_position'],
                                    target_text, region_offset
                                )

                            return result_info

            total_time = time.time() - start_time
            logger.debug(
                f"{self.task_id}--未找到目标文字: '{target_text}', "
                f"总耗时: {total_time:.3f}s"
            )
            return False

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--OCR文字识别失败: {e}, 耗时: {total_time:.3f}s")
            return False

    def batch_ocr_check(self, text_checks: List[dict]) -> Dict[str, Any]:
        """
        批量OCR检查，使用同一张截图检查多个文本
        text_checks示例:
        [
            {"text": "进入游戏", "region": None},
            {"text": "密码错误", "region": (729, 464, 1534, 570)},
            {"text": "验证码错误", "region": (785, 452, 1499, 636)}
        ]
        """
        start_time = time.time()
        try:
            # 预获取截图
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            screenshot_time = time.time() - screenshot_start
            if screenshot is None:
                return {"found": False, "result": None}

            results = {}
            check_count = len(text_checks)

            for i, check in enumerate(text_checks):
                check_start = time.time()
                target_text = check["text"]
                region = check.get("region")

                # 使用预获取的截图进行OCR
                if self.ocr_engine is None:
                    continue

                # 处理区域截图
                region_process_start = time.time()
                if region:
                    x1, y1, x2, y2 = region
                    height, width = screenshot.shape[:2]
                    x1 = max(0, min(x1, width - 1))
                    y1 = max(0, min(y1, height - 1))
                    x2 = max(x1 + 1, min(x2, width))
                    y2 = max(y1 + 1, min(y2, height))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    region_screenshot = screenshot[y1:y2, x1:x2]
                    region_offset = (x1, y1)
                else:
                    region_screenshot = screenshot
                    region_offset = (0, 0)
                region_process_time = time.time() - region_process_start

                # 转换为RGB
                convert_start = time.time()
                if len(region_screenshot.shape) == 3 and region_screenshot.shape[2] == 3:
                    region_screenshot_rgb = cv2.cvtColor(region_screenshot, cv2.COLOR_BGR2RGB)
                else:
                    if len(region_screenshot.shape) == 2:
                        region_screenshot = cv2.cvtColor(region_screenshot, cv2.COLOR_GRAY2BGR)
                    region_screenshot_rgb = cv2.cvtColor(region_screenshot, cv2.COLOR_BGR2RGB)
                convert_time = time.time() - convert_start

                # OCR识别
                ocr_start = time.time()
                ocr_results = self.ocr_engine.ocr(region_screenshot_rgb)
                ocr_time = time.time() - ocr_start

                # 检查是否包含目标文字
                found = False
                for result in ocr_results:
                    logger.debug(result)
                    if isinstance(result, dict) and 'text' in result:
                        text = result['text']

                        if target_text in text:
                            found = True
                            break

                results[target_text] = found
                check_time = time.time() - check_start

                logger.debug(
                    f"{self.task_id}--批量OCR检查第{i + 1}/{check_count}: '{target_text}' "
                    f"{'找到' if found else '未找到'}, 单次检查耗时: {check_time:.3f}s "
                    f"(区域处理: {region_process_time:.3f}s, 转换: {convert_time:.3f}s, OCR: {ocr_time:.3f}s)"
                )

                # 如果找到就立即返回
                if found:
                    total_time = time.time() - start_time
                    return {
                        "found": True,
                        "matched_text": target_text,
                        "all_results": results,
                        "processing_time": total_time,
                        "screenshot_time": screenshot_time
                    }

            total_time = time.time() - start_time
            return {
                "found": False,
                "all_results": results,
                "processing_time": total_time,
                "screenshot_time": screenshot_time
            }

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"批量OCR检查失败: {e}, 耗时: {total_time:.3f}s")
            return {"found": False, "error": str(e), "processing_time": total_time}

    def _enhance_image(self, image):
        """图像增强处理"""
        start_time = time.time()
        try:
            # 对比度增强
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced_lab = cv2.merge([l, a, b])
            enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

            enhance_time = time.time() - start_time
            if enhance_time > 0.1:
                logger.debug(f"{self.task_id}--图像增强耗时: {enhance_time:.3f}s")
            return enhanced_image
        except Exception as e:
            enhance_time = time.time() - start_time
            logger.warning(f"图像增强失败: {e}, 耗时: {enhance_time:.3f}s")
            return image

    def _calculate_target_text_position(self, full_text: str, target_text: str,
                                        textbox_position, region_offset, full_screenshot_shape):
        """
        计算目标文字在文本框内的精确位置

        Args:
            full_text: OCR识别到的完整文本
            target_text: 要查找的目标文字
            textbox_position: 整个文本框的位置
            region_offset: 区域偏移量
            full_screenshot_shape: 全屏截图形状
        """
        start_time = time.time()
        try:
            # 找到目标文字在完整文本中的位置
            start_index = full_text.find(target_text)
            if start_index == -1:
                logger.error(f"目标文字 '{target_text}' 不在文本 '{full_text}' 中")
                return None

            end_index = start_index + len(target_text)

            # 计算目标文字在文本框中的相对位置（按字符比例）
            text_length = len(full_text)
            if text_length == 0:
                return None

            # 获取文本框的四个点坐标
            if hasattr(textbox_position, 'tolist'):
                textbox_position = textbox_position.tolist()

            if isinstance(textbox_position, list) and len(textbox_position) == 4:
                # 文本框的四个点：左上、右上、右下、左下
                left_top = textbox_position[0]  # [x1, y1]
                right_top = textbox_position[1]  # [x2, y2]
                right_bottom = textbox_position[2]  # [x3, y3]
                left_bottom = textbox_position[3]  # [x4, y4]

                # 计算文本框的宽度（取上边和下边的平均值）
                top_width = right_top[0] - left_top[0]
                bottom_width = right_bottom[0] - left_bottom[0]
                avg_width = (top_width + bottom_width) / 2

                # 计算每个字符的大概宽度
                char_width = avg_width / text_length

                # 计算目标文字的起始和结束位置（在文本框内的相对位置）
                target_start_x = left_top[0] + (start_index * char_width)
                target_end_x = left_top[0] + (end_index * char_width)

                # 目标文字的高度（取文本框高度）
                target_top_y = min(left_top[1], right_top[1])
                target_bottom_y = max(left_bottom[1], right_bottom[1])

                # 计算目标文字的中心点（在区域内的相对位置）
                target_center_x = (target_start_x + target_end_x) / 2
                target_center_y = (target_top_y + target_bottom_y) / 2

                # 转换为屏幕绝对坐标
                x_offset, y_offset = region_offset
                screen_bbox = (
                    target_start_x + x_offset,
                    target_top_y + y_offset,
                    target_end_x + x_offset,
                    target_bottom_y + y_offset
                )
                screen_center = (
                    int(target_center_x + x_offset),
                    int(target_center_y + y_offset)
                )

                target_position = {
                    'relative_bbox': (target_start_x, target_top_y, target_end_x, target_bottom_y),
                    'relative_center': (target_center_x, target_center_y),
                    'screen_position': {
                        'bbox': screen_bbox,
                        'center': screen_center
                    }
                }

                calc_time = time.time() - start_time
                if calc_time > 0.05:
                    logger.debug(
                        f"目标文字位置计算 - 文本: '{full_text}', 目标: '{target_text}', "
                        f"耗时: {calc_time:.3f}s"
                    )

                return target_position

            else:
                logger.error(f"无效的文本框位置格式: {textbox_position}")
                return None

        except Exception as e:
            calc_time = time.time() - start_time
            logger.error(f"计算目标文字位置时出错: {e}, 耗时: {calc_time:.3f}s")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _save_ocr_debug_image(self, screenshot, ocr_result, screen_position,
                              target_text, region_offset):
        """保存OCR调试图像"""
        start_time = time.time()
        try:
            debug_img = screenshot.copy()

            # 绘制文字边界框
            if (screen_position.get('bounding_box') and
                    screen_position['bounding_box'].get('top_left_relative')):
                top_left = screen_position['bounding_box']['top_left_relative']
                bottom_right = screen_position['bounding_box']['bottom_right_relative']

                # 绘制边界框
                cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)

                # 绘制中心点
                center = screen_position['center']
                center_relative = (center[0] - region_offset[0], center[1] - region_offset[1])
                cv2.drawMarker(debug_img, center_relative, (0, 0, 255),
                               cv2.MARKER_CROSS, 20, 2)

            # 添加文本信息
            text = ocr_result.get('text', '')
            confidence = ocr_result.get('score', 0.0)

            info_lines = [
                f"Target: {target_text}",
                f"Found: {text}",
                f"Confidence: {confidence:.3f}",
                f"Center: {screen_position['center']}"
            ]

            for i, line in enumerate(info_lines):
                cv2.putText(debug_img, line, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(debug_img, line, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"ocr_debug_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            save_time = time.time() - start_time
            logger.debug(f"{self.task_id}--OCR调试图像已保存: {debug_path}, 耗时: {save_time:.3f}s")

        except Exception as e:
            save_time = time.time() - start_time
            logger.warning(f"{self.task_id}--保存OCR调试图像失败: {e}, 耗时: {save_time:.3f}s")

    def ocr_click_text(self, target_text: str,
                       region: Tuple[int, int, int, int] = None,
                       offset_x: int = 0,
                       offset_y: int = 0) -> bool:
        """
        使用OCR找到文字并点击

        Args:
            target_text: 要点击的目标文字
            region: 识别区域
            offset_x: X轴偏移
            offset_y: Y轴偏移

        Returns:
            bool: 是否点击成功
        """
        start_time = time.time()
        find_start = time.time()
        result = self.ocr_find_text(target_text, region)
        find_time = time.time() - find_start

        if not result:
            total_time = time.time() - start_time
            logger.debug(
                f"{self.task_id}--未找到可点击的文字: '{target_text}', "
                f"总耗时: {total_time:.3f}s (查找: {find_time:.3f}s)"
            )
            return False

        try:
            center_x, center_y = result['center_point']
            target_x = center_x + offset_x
            target_y = center_y + offset_y

            click_start = time.time()
            self.d.click(target_x, target_y)
            click_time = time.time() - click_start

            total_time = time.time() - start_time
            logger.info(
                f"{self.task_id}--OCR点击文字 '{target_text}' "
                f"位置: ({target_x}, {target_y}), "
                f"总耗时: {total_time:.3f}s (查找: {find_time:.3f}s, 点击: {click_time:.3f}s)"
            )
            time.sleep(1.5)
            return True

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--OCR点击文字失败: {e}, 耗时: {total_time:.3f}s")
            return False

    def open_url(self, url: str, time_sleep: float = 0.5) -> None:
        """打开URL"""
        start_time = time.time()
        self.d.open_url(url)
        open_time = time.time() - start_time
        logger.debug(f'{self.task_id}--打开链接: {url}, 耗时: {open_time:.3f}s')
        sleep(time_sleep)

    def virtual_key(self, key: str, time_sleep: float = 1) -> None:
        """
        模拟虚拟按键操作

        Args:
            key: 按键类型 ('back', 'delete', 'enter')
            time_sleep: 操作后等待时间
        """
        start_time = time.time()
        valid_keys = {'back', 'delete', 'enter'}
        if key not in valid_keys:
            logger.warning(f'不支持的按键类型: {key}, 支持的按键: {valid_keys}')
            return

        if key == 'delete':
            for _ in range(30):
                self.d.press(key)
        else:
            self.d.press(key)

        key_time = time.time() - start_time
        logger.debug(f'{self.task_id}--执行 {key} 操作，耗时: {key_time:.3f}s，等待 {time_sleep} 秒')
        sleep(time_sleep)

    # def swipe_direction(self, direction: str, scale: float = 0.9,
    #                     times: int = 1, duration: float = 1.0, **kwargs) -> None:
    #     """
    #     通用滑动方法
    #
    #     Args:
    #         direction: 滑动方向 ('up', 'down', 'left', 'right')
    #         scale: 滑动比例
    #         times: 滑动次数
    #         duration: 滑动持续时间
    #     """
    #     start_time = time.time()
    #     valid_directions = {'up', 'down', 'left', 'right'}
    #     if direction not in valid_directions:
    #         logger.warning(f'{self.task_id}--不支持的滑动方向: {direction}')
    #         return
    #
    #     for _ in range(times):
    #         self.d.swipe_ext(direction, scale, duration=duration, **kwargs)
    #
    #     swipe_time = time.time() - start_time
    #     logger.debug(f'{self.task_id}--向{direction}滑动成功, 耗时: {swipe_time:.3f}s')
    #     sleep(times)
    #
    # def up(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
    #     """上滑操作"""
    #     start_time = time.time()
    #     self.swipe_direction('up', scale, times, duration, **kwargs)
    #     total_time = time.time() - start_time
    #     logger.debug(f'{self.task_id}--上滑操作完成, 总耗时: {total_time:.3f}s')
    #
    # def down(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
    #     """下滑操作"""
    #     start_time = time.time()
    #     self.swipe_direction('down', scale, times, duration, **kwargs)
    #     total_time = time.time() - start_time
    #     logger.debug(f'{self.task_id}--下滑操作完成, 总耗时: {total_time:.3f}s')
    #
    # def left(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
    #     """左滑操作"""
    #     start_time = time.time()
    #     self.swipe_direction('left', scale, times, duration, **kwargs)
    #     total_time = time.time() - start_time
    #     logger.debug(f'{self.task_id}--左滑操作完成, 总耗时: {total_time:.3f}s')
    #
    # def right(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
    #     """右滑操作"""
    #     start_time = time.time()
    #     self.swipe_direction('right', scale, times, duration, **kwargs)
    #     total_time = time.time() - start_time
    #     logger.debug(f'{self.task_id}--右滑操作完成, 总耗时: {total_time:.3f}s')

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              steps: int = 70) -> None:
        """自定义滑动"""
        start_time = time.time()
        self.d.swipe(start_x, start_y, end_x, end_y, steps=steps)
        swipe_time = time.time() - start_time
        logger.debug(
            f'{self.task_id}--从({start_x},{start_y})滑动到({end_x},{end_y}), '
            f'耗时: {swipe_time:.3f}s'
        )

    def wait_until_element_found(self, locator: Tuple[str, str],
                                 max_retries: int = 1, retry_interval: float = 1) -> bool:
        """
        等待元素出现

        Args:
            locator: 元素定位器 (定位类型, 定位值)
            max_retries: 最大重试次数
            retry_interval: 重试间隔

        Returns:
            bool: 是否找到元素
        """
        start_time = time.time()
        if not isinstance(locator, tuple) or len(locator) != 2:
            logger.error(f'{self.task_id}--元素定位器格式错误: {locator}')
            return False

        locator_type, locator_value = locator

        if locator_type not in {'xpath', 'id'}:
            logger.error(f'{self.task_id}--不支持的定位类型: {locator_type}')
            return False

        for i in range(max_retries):
            check_start = time.time()
            element = self.d.xpath(locator_value) if locator_type == 'xpath' else self.d(resourceId=locator_value)
            check_time = time.time() - check_start

            if element.exists:
                total_time = time.time() - start_time
                logger.debug(
                    f'{self.task_id}--找到元素: {locator_value}, '
                    f'总耗时: {total_time:.3f}s (第{i + 1}次检查: {check_time:.3f}s)'
                )
                return True

            if i < max_retries - 1:
                logger.debug(
                    f'{self.task_id}--未找到元素: {locator_value}, 第{i + 1}次重试, '
                    f'本次检查耗时: {check_time:.3f}s'
                )
                sleep(retry_interval)

        total_time = time.time() - start_time
        logger.debug(
            f'{self.task_id}--未找到元素: {locator}, 超出最大重试次数 {max_retries}, '
            f'总耗时: {total_time:.3f}s'
        )
        return False

    def _get_element_object(self, locator: Tuple[str, str]) -> Optional[Any]:
        """获取元素对象"""
        start_time = time.time()
        locator_type, locator_value = locator
        if locator_type == 'id':
            element = self.d(resourceId=locator_value)
        elif locator_type == 'xpath':
            element = self.d.xpath(locator_value)
        else:
            element = None

        get_time = time.time() - start_time
        if get_time > 0.1:
            logger.debug(f'{self.task_id}--获取元素对象耗时: {get_time:.3f}s')
        return element

    def positioning_element_obj(self, locator: Tuple[str, str], max_retries: int = 1,
                                report_error: int = 1) -> Optional[Any]:
        """
        定位元素对象

        Args:
            locator: 元素定位器
            max_retries: 最大重试次数
            report_error: 错误报告级别 (1: 报错, 2: 不报错)

        Returns:
            Optional[Any]: 元素对象或None
        """
        start_time = time.time()
        found = self.wait_until_element_found(locator, max_retries)

        if found:
            element = self._get_element_object(locator)
            total_time = time.time() - start_time
            logger.debug(f'{self.task_id}--定位元素对象成功: {locator}, 耗时: {total_time:.3f}s')
            return element

        total_time = time.time() - start_time
        if report_error == 1:
            raise Exception(f'{self.task_id}--定位元素失败: {locator}, 耗时: {total_time:.3f}s')
        else:
            logger.debug(f'{self.task_id}--未找到元素: {locator}, 忽略错误, 耗时: {total_time:.3f}s')
            return None

    def click_element(self, locator: Tuple[str, str], max_retries: int = 1,
                      retry_interval: float = 1, report_error: int = 1,
                      click_type: int = 1, height_threshold: int = 1380,
                      long_click: bool = False) -> bool:
        """
        点击元素

        Args:
            locator: 元素定位器
            max_retries: 最大重试次数
            retry_interval: 点击后等待时间
            report_error: 错误报告级别
            click_type: 点击类型
            height_threshold: 高度阈值
            long_click: 是否长按

        Returns:
            bool: 是否点击成功
        """
        start_time = time.time()
        positioning_start = time.time()
        element_obj = self.positioning_element_obj(
            locator, max_retries, report_error
        )
        positioning_time = time.time() - positioning_start

        if not element_obj:
            total_time = time.time() - start_time
            logger.debug(f'{self.task_id}--点击元素失败: 未找到元素 {locator}, 耗时: {total_time:.3f}s')
            return False

        sleep(0.5)

        # # 处理需要滚动的情况
        # scroll_start = time.time()
        # if click_type == 2:
        #     try:
        #         bounds = element_obj.bounds
        #         element_center_y = (bounds[1] + bounds[3]) / 2
        #         if element_center_y >= height_threshold:
        #             self.up(0.3, duration=0.1)
        #     except Exception as e:
        #         logger.warning(f'{self.task_id}--获取元素位置失败: {e}')
        # scroll_time = time.time() - scroll_start

        # 执行点击操作
        click_start = time.time()
        try:
            if long_click:
                element_obj.long_click()
            else:
                element_obj.click()

            click_time = time.time() - click_start
            sleep(retry_interval)

            total_time = time.time() - start_time
            logger.debug(
                f'{self.task_id}--点击元素成功: {locator}, '
                f'总耗时: {total_time:.3f}s (定位: {positioning_time:.3f}s, '
                f'点击: {click_time:.3f}s)'
            )
            return True

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f'{self.task_id}--点击元素失败: {e}, 耗时: {total_time:.3f}s')
            if report_error == 1:
                raise Exception(f'{self.task_id}--点击元素失败: {e}')
            return False

    def input_element(self, locator: Tuple[str, str], text: str, clear: bool = True,
                      max_retries: int = 1, retry_interval: float = 1,
                      report_error: int = 1) -> bool:
        """
        输入文本到元素

        Args:
            locator: 元素定位器
            text: 输入的文本
            clear: 是否清空原文本
            max_retries: 最大重试次数
            retry_interval: 输入后等待时间
            report_error: 错误报告级别

        Returns:
            bool: 是否输入成功
        """
        start_time = time.time()
        positioning_start = time.time()
        element_obj = self.positioning_element_obj(
            locator, max_retries, report_error
        )
        positioning_time = time.time() - positioning_start

        if not element_obj:
            total_time = time.time() - start_time
            logger.debug(f'{self.task_id}--输入文本失败: 未找到元素 {locator}, 耗时: {total_time:.3f}s')
            return False

        try:
            input_start = time.time()
            if clear:
                element_obj.clear_text()

            element_obj.set_text(text)
            input_time = time.time() - input_start
            sleep(retry_interval)

            total_time = time.time() - start_time
            logger.debug(
                f'{self.task_id}--输入文本成功: {text}, '
                f'总耗时: {total_time:.3f}s (定位: {positioning_time:.3f}s, 输入: {input_time:.3f}s)'
            )
            return True

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f'{self.task_id}--输入文本失败: {e}, 耗时: {total_time:.3f}s')
            if report_error == 1:
                raise
            return False

    def send_keys(self, text: str, report_error: int = 1) -> bool:
        """发送按键"""
        start_time = time.time()
        try:
            self.d.send_keys(text, clear=report_error != 1)
            send_time = time.time() - start_time
            logger.debug(f'{self.task_id}--输入文本: {text}, 耗时: {send_time:.3f}s')
            return True
        except Exception as e:
            send_time = time.time() - start_time
            logger.error(f'{self.task_id}--输入文本失败: {e}, 耗时: {send_time:.3f}s')
            if report_error == 1:
                raise
            return False

    def u2_adb_shell(self, command: str) -> str:
        """执行u2-ADB shell命令"""
        start_time = time.time()
        result = self.d.shell(command)
        shell_time = time.time() - start_time
        sleep(1)
        logger.debug(f'{self.task_id}--执行u2 ADB命令: {command}, 耗时: {shell_time:.3f}s')
        return result.output

    def adb_shell(self, command: str) -> str:
        """执行原生ADB shell命令"""
        start_time = time.time()
        try:
            # 构建完整的ADB命令
            full_command = ['adb', '-s', self.device, 'shell'] + command.split()
            # 执行命令并获取结果
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 设置超时时间
            )

            adb_time = time.time() - start_time
            logger.debug(f"{self.task_id}--{self.device}ADB命令成功: {command}, 耗时: {adb_time:.3f}s")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            adb_time = time.time() - start_time
            raise Exception(f"ADB命令执行超时: {command}, 耗时: {adb_time:.3f}s")
        except subprocess.CalledProcessError as e:
            adb_time = time.time() - start_time
            raise Exception(f"ADB命令执行失败: {command}, 错误: {e.stderr}, 耗时: {adb_time:.3f}s")
        except Exception as e:
            adb_time = time.time() - start_time
            raise Exception(f"执行ADB命令时发生未知错误: {e}, 耗时: {adb_time:.3f}s")

    def positioning_element_list_obj(self, locator: Tuple[str, str], max_retries: int = 10,
                                     report_error: int = 1) -> Optional[List[Any]]:
        """
        定位多个元素对象

        Returns:
            Optional[List[Any]]: 元素对象列表或None
        """
        start_time = time.time()
        found = self.wait_until_element_found(locator, max_retries)

        if found:
            element_obj = self._get_element_object(locator)
            if hasattr(element_obj, 'all'):
                elements = element_obj.all()
            else:
                elements = [element_obj]

            total_time = time.time() - start_time
            logger.debug(
                f'{self.task_id}--定位多个元素对象成功: {locator}, 找到{len(elements)}个元素, 耗时: {total_time:.3f}s')
            return elements

        total_time = time.time() - start_time
        if report_error == 1:
            raise Exception(f'{self.task_id}--定位元素失败: {locator}, 耗时: {total_time:.3f}s')
        else:
            logger.debug(f'{self.task_id}--未找到元素: {locator}, 忽略错误, 耗时: {total_time:.3f}s')
            return None

    def _load_image(self, image_data: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """加载并统一图像格式为3通道BGR"""
        start_time = time.time()
        if isinstance(image_data, str):
            image_path = os.path.join(self.img_path, image_data)
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise FileNotFoundError(f"{self.task_id}--无法加载图像: '{image_path}'")
        elif isinstance(image_data, np.ndarray):
            image = image_data
        elif isinstance(image_data, Image.Image):
            image = np.array(image_data)
        else:
            raise TypeError(f"不支持的图像类型: {type(image_data)}")

        # 处理图像通道
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 4:
            # RGBA转BGR
            bg = np.ones_like(image[..., :3]) * 255
            rgb = image[..., :3]
            alpha = image[..., 3:] / 255.0
            image = (alpha * rgb + (1 - alpha) * bg).astype(np.uint8)
        elif image.ndim == 3 and image.shape[2] == 3:
            pass  # 已经是BGR格式
        else:
            raise ValueError(f"{self.task_id}--不支持的图像格式: {image.shape}")

        load_time = time.time() - start_time
        if load_time > 0.05:
            logger.debug(f"{self.task_id}--图像加载耗时: {load_time:.3f}s")
        return image

    def img_match(self, image_data: Union[str, np.ndarray, Image.Image],
                  min_similarity: float = 0.9, debug: bool = False,
                  region: Tuple[int, int, int, int] = None,
                  is_recursive_call: bool = False,
                  max_matches: int = 1) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        图像匹配（支持单个模板在屏幕上找多个匹配位置）
        """
        start_time = time.time()
        try:
            # 加载模板
            template_load_start = time.time()
            template = self._load_image(image_data)
            template_height, template_width = template.shape[:2]
            template_load_time = time.time() - template_load_start

            # 获取设备信息
            device_width, device_height = self.d.window_size()

            # 获取全屏截图（用于计算缩放比例）
            screenshot_start = time.time()
            full_screenshot = self.d.screenshot(format='opencv')
            full_height, full_width = full_screenshot.shape[:2]
            screenshot_time = time.time() - screenshot_start

            # 计算全屏的缩放比例（固定值）
            scale_x = device_width / full_width
            scale_y = device_height / full_height

            # 获取目标截图（支持区域截图）
            region_start = time.time()
            if region:
                x1, y1, x2, y2 = region
                # 确保区域在截图范围内
                x1 = max(0, min(x1, full_width - 1))
                y1 = max(0, min(y1, full_height - 1))
                x2 = max(x1 + 1, min(x2, full_width))
                y2 = max(y1 + 1, min(y2, full_height))

                # 检查区域是否有效
                if x2 <= x1 or y2 <= y1:
                    logger.warning(f"{self.task_id}--无效的区域设置: {region}")
                    return None

                screenshot = full_screenshot[y1:y2, x1:x2]
                region_offset = (x1, y1)
            else:
                screenshot = full_screenshot
                region_offset = (0, 0)
            region_time = time.time() - region_start

            screenshot_height, screenshot_width = screenshot.shape[:2]

            # 检查截图区域是否有效
            if screenshot_width <= 0 or screenshot_height <= 0:
                logger.warning(f"{self.task_id}--截图区域无效: {screenshot_width}x{screenshot_height}")
                return None

            # 检查模板是否大于截图区域
            resize_start = time.time()
            template_too_large = False
            if template_width > screenshot_width or template_height > screenshot_height:
                logger.warning(
                    f"{self.task_id}--模板尺寸({template_width}x{template_height})大于截图区域({screenshot_width}x{screenshot_height})")
                template_too_large = True

                # 调整模板大小以适应截图区域
                scale_factor = min(screenshot_width / template_width, screenshot_height / template_height)
                new_width = max(10, int(template_width * scale_factor * 0.95))
                new_height = max(10, int(template_height * scale_factor * 0.95))

                if new_width < 10 or new_height < 10:
                    logger.warning(f"{self.task_id}--调整后的模板尺寸太小({new_width}x{new_height})，无法匹配")
                    return None

                template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_AREA)
                template_height, template_width = template.shape[:2]
                logger.debug(f"{self.task_id}--模板已调整为: {template_width}x{template_height}")

            # 如果模板仍然太大，使用边缘裁剪策略
            if template_width > screenshot_width or template_height > screenshot_height:
                logger.warning(f"{self.task_id}--模板调整后仍然太大，尝试边缘裁剪")
                width_excess = max(0, template_width - screenshot_width)
                height_excess = max(0, template_height - screenshot_height)

                start_x = width_excess // 2
                start_y = height_excess // 2
                end_x = template_width - (width_excess - start_x)
                end_y = template_height - (height_excess - start_y)

                if end_x > start_x and end_y > start_y:
                    template = template[start_y:end_y, start_x:end_x]
                    template_height, template_width = template.shape[:2]
                    logger.debug(f"{self.task_id}--模板裁剪后尺寸: {template_width}x{template_height}")
                else:
                    logger.warning(f"{self.task_id}--模板裁剪失败，尺寸仍然不匹配")
                    return None
            resize_time = time.time() - resize_start

            # 执行模板匹配
            match_start = time.time()
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            match_time = time.time() - match_start

            # 寻找所有匹配位置（使用非极大值抑制）
            find_matches_start = time.time()
            locations = []
            for _ in range(max_matches):
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # 如果最大相似度低于阈值，停止搜索
                if max_val < min_similarity:
                    break

                # 记录匹配位置
                locations.append((max_loc, max_val))

                # 将已找到的区域置为最小值，避免重复检测
                x, y = max_loc
                h, w = template_height, template_width
                cv2.rectangle(result, (x, y), (x + w, y + h), 0, -1)
            find_matches_time = time.time() - find_matches_start

            all_results = []

            # 处理匹配结果
            process_results_start = time.time()
            for loc, similarity in locations:
                top_left_relative = loc
                bottom_right_relative = (top_left_relative[0] + template_width,
                                         top_left_relative[1] + template_height)
                center_x_relative = (top_left_relative[0] + bottom_right_relative[0]) // 2
                center_y_relative = (top_left_relative[1] + bottom_right_relative[1]) // 2

                # 转换为全屏坐标
                top_left_full = (top_left_relative[0] + region_offset[0],
                                 top_left_relative[1] + region_offset[1])
                bottom_right_full = (bottom_right_relative[0] + region_offset[0],
                                     bottom_right_relative[1] + region_offset[1])
                center_x_full = center_x_relative + region_offset[0]
                center_y_full = center_y_relative + region_offset[1]

                # 转换为设备坐标
                phys_x = int(center_x_full * scale_x)
                phys_y = int(center_y_full * scale_y)

                result_info = {
                    "similarity": similarity,
                    "point": (phys_x, phys_y),
                    "match_area": (top_left_full, bottom_right_full),
                    "screen_size": (device_width, device_height),
                    "region_offset": region_offset,
                    "region": region if region else (0, 0, full_width, full_height),
                    "relative_coords": {
                        "relative_center": (center_x_relative, center_y_relative),
                        "relative_top_left": top_left_relative,
                        "relative_bottom_right": bottom_right_relative
                    },
                    "template_adjusted": template_too_large,
                    "template_name": image_data if isinstance(image_data, str) else "image_data"
                }

                all_results.append(result_info)

                logger.debug(
                    f"{self.task_id}--匹配到目标: {image_data if isinstance(image_data, str) else '图像'} "
                    f"相似度: {similarity:.2f} 位置: ({phys_x}, {phys_y})"
                )
            process_results_time = time.time() - process_results_start

            total_time = time.time() - start_time

            if all_results:
                logger.debug(
                    f"{self.task_id}--图像匹配成功: {image_data if isinstance(image_data, str) else '图像'}, "
                    f"找到{len(all_results)}个匹配, 总耗时: {total_time:.3f}s "
                    f"(模板加载: {template_load_time:.3f}s, 截图: {screenshot_time:.3f}s, "
                    f"区域处理: {region_time:.3f}s, 尺寸调整: {resize_time:.3f}s, "
                    f"模板匹配: {match_time:.3f}s, 找位置: {find_matches_time:.3f}s, "
                    f"处理结果: {process_results_time:.3f}s)"
                )
            else:
                logger.debug(
                    f"{self.task_id}--图像匹配失败: {image_data if isinstance(image_data, str) else '图像'}, "
                    f"总耗时: {total_time:.3f}s (模板加载: {template_load_time:.3f}s, "
                    f"截图: {screenshot_time:.3f}s, 匹配: {match_time:.3f}s)"
                )

            # 只在非递归调用时处理意外弹窗
            if not all_results and not is_recursive_call:
                if self.accidental_processing:
                    logger.debug(f"{self.task_id}--匹配失败，开始意外弹窗处理")
                    popup_start = time.time()
                    processed = self._handle_accidental_popups(self.accidental_processing)
                    popup_time = time.time() - popup_start
                    if processed:
                        logger.debug(f"{self.task_id}--弹窗处理耗时: {popup_time:.3f}s，重新尝试匹配")
                        return self.img_match(
                            image_data=image_data,
                            min_similarity=min_similarity,
                            debug=debug,
                            region=region,
                            is_recursive_call=True,
                            max_matches=max_matches
                        )

            if debug and all_results:
                debug_start = time.time()
                # 保存调试图像（显示所有匹配区域）
                debug_img = screenshot.copy()
                for i, result in enumerate(all_results):
                    rel_coords = result["relative_coords"]
                    top_left = rel_coords["relative_top_left"]
                    bottom_right = rel_coords["relative_bottom_right"]
                    center = rel_coords["relative_center"]

                    # 绘制匹配区域
                    cv2.rectangle(debug_img, top_left, bottom_right, (0, 0, 255), 2)
                    cv2.drawMarker(debug_img, center, (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

                    # 添加编号
                    cv2.putText(debug_img, str(i + 1),
                                (top_left[0] + 5, top_left[1] + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_path = os.path.join(self.debug_img, f"multi_match_debug_{timestamp}.png")
                cv2.imwrite(debug_path, debug_img)
                self.last_debug_image = debug_path
                debug_time = time.time() - debug_start
                logger.debug(f"{self.task_id}--调试图像保存耗时: {debug_time:.3f}s")

            # 返回格式处理
            if not all_results:
                return None

            # 关键：根据匹配数量和 max_matches 决定返回格式
            if max_matches == 1:
                # 单个匹配时返回字典
                return all_results[0]
            else:
                # max_matches > 1 时：
                if len(all_results) == 1:
                    # 只找到一个匹配，返回字典
                    return all_results[0]
                else:
                    # 找到多个匹配，返回列表
                    return all_results

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--图像匹配失败: {e}, 耗时: {total_time:.3f}s")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def compare_region_similarity(self, full_image_data: Union[str, np.ndarray, Image.Image],
                                  region: Tuple[int, int, int, int],
                                  min_similarity: float = 0.8,
                                  debug: bool = False) -> bool:
        """
        比较指定区域的图片相似度
        """
        start_time = time.time()
        try:
            # 1. 从原图片中截取指定区域作为模板
            template_load_start = time.time()
            full_image = self._load_image(full_image_data)
            x1, y1, x2, y2 = region

            # 确保区域在图片范围内
            img_height, img_width = full_image.shape[:2]
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(x1 + 1, min(x2, img_width))
            y2 = max(y1 + 1, min(y2, img_height))

            if x2 <= x1 or y2 <= y1:
                logger.error(f"{self.task_id}--无效的区域设置: {region}, 图片尺寸: {img_width}x{img_height}")
                return False

            # 截取模板区域
            template = full_image[y1:y2, x1:x2]
            template_height, template_width = template.shape[:2]
            template_load_time = time.time() - template_load_start

            logger.debug(f"{self.task_id}--从原图截取模板区域: {region}, 模板尺寸: {template_width}x{template_height}")

            # 2. 获取当前屏幕截图并截取相同区域
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            if screenshot is None:
                raise Exception("无法获取屏幕截图")
            screenshot_time = time.time() - screenshot_start

            # 确保区域在屏幕截图范围内
            screen_height, screen_width = screenshot.shape[:2]
            x1_screen = max(0, min(x1, screen_width - 1))
            y1_screen = max(0, min(y1, screen_height - 1))
            x2_screen = max(x1_screen + 1, min(x2, screen_width))
            y2_screen = max(y1_screen + 1, min(y2, screen_height))

            if x2_screen <= x1_screen or y2_screen <= y1_screen:
                logger.error(f"{self.task_id}--区域超出屏幕范围: {region}, 屏幕尺寸: {screen_width}x{screen_height}")
                return False

            # 截取屏幕区域
            screen_region = screenshot[y1_screen:y2_screen, x1_screen:x2_screen]
            screen_region_height, screen_region_width = screen_region.shape[:2]

            logger.debug(
                f"{self.task_id}--从屏幕截取区域: {region}, 屏幕区域尺寸: {screen_region_width}x{screen_region_height}")

            # 3. 调整模板尺寸以匹配屏幕区域尺寸（如果需要）
            resize_start = time.time()
            if template_width != screen_region_width or template_height != screen_region_height:
                logger.debug(f"{self.task_id}--调整模板尺寸以匹配屏幕区域")
                template = cv2.resize(template, (screen_region_width, screen_region_height),
                                      interpolation=cv2.INTER_AREA)
                template_height, template_width = template.shape[:2]
                logger.debug(f"{self.task_id}--模板调整后尺寸: {template_width}x{template_height}")
            resize_time = time.time() - resize_start

            # 4. 执行模板匹配
            match_start = time.time()
            result = cv2.matchTemplate(screen_region, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            match_time = time.time() - match_start

            similarity = max_val

            if debug:
                debug_start = time.time()
                # 保存调试图像
                self._save_region_comparison_debug_image(
                    full_image, template, screenshot, screen_region,
                    region, similarity, min_similarity
                )
                debug_time = time.time() - debug_start
                logger.debug(f"{self.task_id}--区域比较调试图像保存耗时: {debug_time:.3f}s")

            # 5. 判断相似度是否达到阈值
            total_time = time.time() - start_time
            if similarity >= min_similarity:
                logger.debug(
                    f"{self.task_id}--区域相似度匹配成功: "
                    f"相似度 {similarity:.3f} >= 阈值 {min_similarity:.2f}, "
                    f"区域: {region}, 总耗时: {total_time:.3f}s "
                    f"(模板加载: {template_load_time:.3f}s, 截图: {screenshot_time:.3f}s, "
                    f"尺寸调整: {resize_time:.3f}s, 匹配: {match_time:.3f}s)"
                )
                return True
            else:
                logger.debug(
                    f"{self.task_id}--区域相似度匹配失败: "
                    f"相似度 {similarity:.3f} < 阈值 {min_similarity:.2f}, "
                    f"区域: {region}, 总耗时: {total_time:.3f}s"
                )
                return False

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--区域相似度比较失败: {e}, 耗时: {total_time:.3f}s")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _save_region_comparison_debug_image(self, full_image, template, screenshot, screen_region,
                                            region, similarity, min_similarity):
        """保存区域比较的调试图像"""
        start_time = time.time()
        try:
            # 创建对比图像
            template_rgb = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            screen_region_rgb = cv2.cvtColor(screen_region, cv2.COLOR_BGR2RGB)

            # 调整图像大小以便对比显示
            max_height = 300
            scale_factor = max_height / max(template_rgb.shape[0], screen_region_rgb.shape[0])

            template_display = cv2.resize(template_rgb,
                                          (int(template_rgb.shape[1] * scale_factor),
                                           int(template_rgb.shape[0] * scale_factor)))
            screen_display = cv2.resize(screen_region_rgb,
                                        (int(screen_region_rgb.shape[1] * scale_factor),
                                         int(screen_region_rgb.shape[0] * scale_factor)))

            # 创建水平对比图
            if template_display.shape[0] != screen_display.shape[0]:
                # 调整高度一致
                max_h = max(template_display.shape[0], screen_display.shape[0])
                template_display = cv2.copyMakeBorder(template_display, 0, max_h - template_display.shape[0],
                                                      0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                screen_display = cv2.copyMakeBorder(screen_display, 0, max_h - screen_display.shape[0],
                                                    0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))

            comparison = np.hstack([template_display, screen_display])

            # 添加文本信息
            text_lines = [
                f"Region: {region}",
                f"Similarity: {similarity:.3f}",
                f"Threshold: {min_similarity:.2f}",
                f"Result: {'PASS' if similarity >= min_similarity else 'FAIL'}"
            ]

            for i, text in enumerate(text_lines):
                cv2.putText(comparison, text, (10, 20 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(comparison, text, (10, 20 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 添加标签
            label_y = comparison.shape[0] - 10
            cv2.putText(comparison, "Template", (10, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(comparison, "Screen Region",
                        (template_display.shape[1] + 10, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"region_comparison_{timestamp}.png")
            cv2.imwrite(debug_path, comparison)

            save_time = time.time() - start_time
            logger.debug(f"{self.task_id}--区域比较调试图像已保存: {debug_path}, 耗时: {save_time:.3f}s")

        except Exception as e:
            save_time = time.time() - start_time
            logger.warning(f"{self.task_id}--保存区域比较调试图像失败: {e}, 耗时: {save_time:.3f}s")

    def _handle_accidental_popups(self, accidental_processing: List[dict]) -> bool:
        """
        处理意外弹窗
        """
        start_time = time.time()
        try:
            if not accidental_processing:
                return False

            logger.debug(f"{self.task_id}--开始检查意外弹窗，共 {len(accidental_processing)} 种弹窗配置")

            # 遍历每种弹窗配置
            for popup_config in accidental_processing:
                popup_image = popup_config.get("popup_images")  # 单个图片路径
                close_button = popup_config.get("close_button")
                max_attempts = popup_config.get("max_attempts", 3)

                if not popup_image:
                    continue

                logger.debug(f"{self.task_id}--检查弹窗: {popup_image}，最多尝试 {max_attempts} 次")

                # 检查当前配置的弹窗
                for attempt in range(max_attempts):
                    popup_check_start = time.time()
                    popup_result = self.img_match(
                        image_data=popup_image,
                        min_similarity=0.7,
                        is_recursive_call=True  # 标记为递归调用
                    )
                    popup_check_time = time.time() - popup_check_start

                    if popup_result:
                        logger.debug(
                            f"{self.task_id}--检测到弹窗: {popup_image}，相似度: {popup_result['similarity']:.2f}, "
                            f"检查耗时: {popup_check_time:.3f}s")

                        # 如果有关闭按钮，尝试点击关闭
                        if close_button:
                            if isinstance(close_button, list):
                                for i in close_button:
                                    close_check_start = time.time()
                                    close_result = self.img_match(
                                        image_data=i,
                                        min_similarity=0.7,
                                        is_recursive_call=True
                                    )
                                    close_check_time = time.time() - close_check_start
                                    if close_result:
                                        click_start = time.time()
                                        self.d.click(close_result["point"][0], close_result["point"][1])
                                        click_time = time.time() - click_start
                                        logger.warning(
                                            f"{self.task_id}--点击关闭按钮成功, "
                                            f"检查耗时: {close_check_time:.3f}s, 点击耗时: {click_time:.3f}s"
                                        )
                                        time.sleep(1)  # 等待弹窗关闭
                                    else:
                                        logger.warning(f"{self.task_id}--检测到弹窗但未找到关闭按钮: {close_button}")
                            else:
                                close_check_start = time.time()
                                close_result = self.img_match(
                                    image_data=close_button,
                                    min_similarity=0.7,
                                    is_recursive_call=True
                                )
                                close_check_time = time.time() - close_check_start

                                if close_result:
                                    click_start = time.time()
                                    self.d.click(close_result["point"][0], close_result["point"][1])
                                    click_time = time.time() - click_start
                                    logger.warning(
                                        f"{self.task_id}--点击关闭按钮成功, "
                                        f"检查耗时: {close_check_time:.3f}s, 点击耗时: {click_time:.3f}s"
                                    )
                                    time.sleep(1)  # 等待弹窗关闭
                                    total_time = time.time() - start_time
                                    logger.debug(f"{self.task_id}--弹窗处理完成, 总耗时: {total_time:.3f}s")
                                    return True
                                else:
                                    logger.warning(f"{self.task_id}--检测到弹窗但未找到关闭按钮: {close_button}")
                        time.sleep(1)
                        total_time = time.time() - start_time
                        logger.debug(f"{self.task_id}--弹窗处理完成, 总耗时: {total_time:.3f}s")
                        return True

                    # 如果当前配置没有检测到弹窗，直接跳出内层循环，检查下一个配置
                    logger.debug(
                        f"{self.task_id}--未检测到弹窗: {popup_image}，尝试次数: {attempt + 1}, "
                        f"本次检查耗时: {popup_check_time:.3f}s"
                    )
                    break  # 跳出当前配置的尝试循环，检查下一个配置

            total_time = time.time() - start_time
            logger.debug(f"{self.task_id}--所有弹窗配置检查完毕，未检测到意外弹窗, 总耗时: {total_time:.3f}s")
            return False

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--处理意外弹窗时出错: {e}, 耗时: {total_time:.3f}s")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _log_debug_info(self, device_width, device_height, screenshot_width,
                        screenshot_height, template_width, template_height):
        """记录调试信息"""
        start_time = time.time()
        logger.debug(f"设备分辨率: {device_width}x{device_height}")
        logger.debug(f"截图尺寸: {screenshot_width}x{screenshot_height}")
        logger.debug(f"模板尺寸: {template_width}x{template_height}")
        logger.debug(f"缩放比例: x:{device_width / screenshot_width:.2f}, y:{device_height / screenshot_height:.2f}")
        log_time = time.time() - start_time
        if log_time > 0.01:
            logger.debug(f"{self.task_id}--调试信息记录耗时: {log_time:.3f}s")

    def img_click(self, image_data: Union[str, np.ndarray, Image.Image],
                  min_similarity: float = 0.8, offset_x: int = 0,
                  offset_y: int = 0, debug: bool = False) -> bool:
        """图像匹配并点击"""
        start_time = time.time()
        try:
            sleep(1)  # 等待界面稳定
            match_start = time.time()
            result = self.img_match(image_data, min_similarity, debug)
            match_time = time.time() - match_start

            if not result:
                total_time = time.time() - start_time
                error_msg = f"{self.task_id}--{self.device}---{image_data}匹配失败, 总耗时: {total_time:.3f}s (匹配: {match_time:.3f}s)"
                logger.error(error_msg)
                return False

            click_start = time.time()
            x, y = result["point"]
            target_x, target_y = x + offset_x, y + offset_y

            self.d.click(target_x, target_y)
            click_time = time.time() - click_start

            total_time = time.time() - start_time
            logger.warning(
                f"点击位置: ({target_x}, {target_y}) - {image_data if isinstance(image_data, str) else '图像'}, "
                f"总耗时: {total_time:.3f}s (匹配: {match_time:.3f}s, 点击: {click_time:.3f}s)"
            )
            time.sleep(1.5)
            return True
        except Exception as e:
            total_time = time.time() - start_time
            logger.warning(f"图片点击操作失败: {image_data}, 耗时: {total_time:.3f}s, 错误: {e}")
            return False

    def _save_debug_image(self, screenshot, top_left, bottom_right, center):
        """保存调试图像"""
        start_time = time.time()
        debug_img = screenshot.copy()

        # 绘制匹配区域和中心点
        cv2.rectangle(debug_img, top_left, bottom_right, (0, 0, 255), 2)
        cv2.drawMarker(debug_img, center, (0, 255, 0), cv2.MARKER_CROSS, 30, 2)

        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = os.path.join(self.debug_img, f"debug_match_{timestamp}.png")
        cv2.imwrite(debug_path, debug_img)
        self.last_debug_image = debug_path

        save_time = time.time() - start_time
        logger.debug(f"{self.task_id}--调试图像已保存: {debug_path}, 耗时: {save_time:.3f}s")

    def detect_color_in_region(self, target_color: Tuple[int, int, int],
                               region: Tuple[int, int, int, int] = None,
                               color_tolerance: int = 10,
                               min_pixel_count: int = 1,
                               debug: bool = False) -> Dict[str, Any]:
        """
        识别一个指定区域内某一个的特定颜色,是否存在
        """
        start_time = time.time()
        try:
            # 获取屏幕截图
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            screenshot_time = time.time() - screenshot_start

            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            # 如果指定了区域，则裁剪截图
            region_start = time.time()
            if region:
                x1, y1, x2, y2 = region
                # 确保区域在有效范围内
                height, width = screenshot.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(x1 + 1, min(x2, width))
                y2 = max(y1 + 1, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    raise ValueError(f"无效的区域设置: {region}")

                region_screenshot = screenshot[y1:y2, x1:x2]
            else:
                region_screenshot = screenshot
                x1, y1 = 0, 0
            region_time = time.time() - region_start

            # 将BGR转换为RGB（OpenCV使用BGR，但输入是RGB）
            target_bgr = (target_color[2], target_color[1], target_color[0])

            # 定义颜色范围
            lower_bound = np.array([
                max(0, target_bgr[0] - color_tolerance),
                max(0, target_bgr[1] - color_tolerance),
                max(0, target_bgr[2] - color_tolerance)
            ])

            upper_bound = np.array([
                min(255, target_bgr[0] + color_tolerance),
                min(255, target_bgr[1] + color_tolerance),
                min(255, target_bgr[2] + color_tolerance)
            ])

            # 创建颜色掩码
            color_detect_start = time.time()
            color_mask = cv2.inRange(region_screenshot, lower_bound, upper_bound)

            # 统计匹配的像素数量
            pixel_count = cv2.countNonZero(color_mask)

            # 获取匹配像素的坐标
            matches = cv2.findNonZero(color_mask)
            matched_coordinates = []

            if matches is not None:
                for match in matches:
                    x, y = match[0]
                    # 转换为全屏坐标
                    global_x = x + x1
                    global_y = y + y1
                    matched_coordinates.append((global_x, global_y))

            # 计算匹配比例
            total_pixels = region_screenshot.shape[0] * region_screenshot.shape[1]
            match_ratio = pixel_count / total_pixels if total_pixels > 0 else 0

            # 是否满足最小像素数量要求
            meets_threshold = pixel_count >= min_pixel_count
            color_detect_time = time.time() - color_detect_start

            result = {
                "pixel_count": pixel_count,
                "match_ratio": match_ratio,
                "meets_threshold": meets_threshold,
                "total_pixels_in_region": total_pixels,
                "matched_coordinates": matched_coordinates,
                "color_tolerance": color_tolerance,
                "target_color_rgb": target_color,
                "target_color_bgr": target_bgr,
                "region": region if region else (0, 0, screenshot.shape[1], screenshot.shape[0]),
                "processing_time": time.time() - start_time,
                "screenshot_time": screenshot_time,
                "region_time": region_time,
                "color_detect_time": color_detect_time
            }

            total_time = time.time() - start_time
            logger.debug(
                f"{self.task_id}--颜色识别结果: "
                f"目标颜色RGB{target_color}, 匹配像素数: {pixel_count}, "
                f"匹配比例: {match_ratio:.4f}, 满足阈值: {meets_threshold}, "
                f"总耗时: {total_time:.3f}s (截图: {screenshot_time:.3f}s, "
                f"区域处理: {region_time:.3f}s, 颜色检测: {color_detect_time:.3f}s)"
            )

            if debug:
                debug_start = time.time()
                self._save_color_debug_image(
                    region_screenshot, color_mask, target_color,
                    pixel_count, region, x1, y1
                )
                debug_time = time.time() - debug_start
                logger.debug(f"{self.task_id}--颜色调试图像保存耗时: {debug_time:.3f}s")

            return result

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--颜色识别失败: {e}, 耗时: {total_time:.3f}s")
            return {
                "pixel_count": 0,
                "match_ratio": 0,
                "meets_threshold": False,
                "total_pixels_in_region": 0,
                "matched_coordinates": [],
                "color_tolerance": color_tolerance,
                "target_color_rgb": target_color,
                "error": str(e),
                "processing_time": total_time
            }

    def detect_multiple_colors_in_region(self, color_list: List[Tuple[int, int, int]],
                                         region: Tuple[int, int, int, int] = None,
                                         color_tolerance: int = 10,
                                         min_pixel_count: int = 1,
                                         debug: bool = False) -> Dict[str, Any]:
        """
        检测一个区域内的多个颜色，判断是否存在,避免重复截图
        """
        start_time = time.time()
        try:
            # 一次性获取截图
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            screenshot_time = time.time() - screenshot_start
            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            # 处理区域
            region_start = time.time()
            if region:
                x1, y1, x2, y2 = region
                height, width = screenshot.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(x1 + 1, min(x2, width))
                y2 = max(y1 + 1, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    return {"total_pixel_count": 0, "colors": {}}

                region_screenshot = screenshot[y1:y2, x1:x2]
            else:
                region_screenshot = screenshot
                x1, y1 = 0, 0
            region_time = time.time() - region_start

            total_pixel_count = 0
            color_results = {}
            color_count = len(color_list)

            # 为每个颜色创建掩码并统计
            color_detect_start = time.time()
            for i, target_color in enumerate(color_list):
                target_bgr = (target_color[2], target_color[1], target_color[0])

                # 定义颜色范围
                lower_bound = np.array([
                    max(0, target_bgr[0] - color_tolerance),
                    max(0, target_bgr[1] - color_tolerance),
                    max(0, target_bgr[2] - color_tolerance)
                ])
                upper_bound = np.array([
                    min(255, target_bgr[0] + color_tolerance),
                    min(255, target_bgr[1] + color_tolerance),
                    min(255, target_bgr[2] + color_tolerance)
                ])

                # 创建颜色掩码
                color_mask = cv2.inRange(region_screenshot, lower_bound, upper_bound)
                pixel_count = cv2.countNonZero(color_mask)

                color_results[str(target_color)] = {
                    "pixel_count": pixel_count,
                    "meets_threshold": pixel_count >= min_pixel_count,
                    "target_color": target_color
                }

                total_pixel_count += pixel_count
            color_detect_time = time.time() - color_detect_start

            # 性能日志
            total_time = time.time() - start_time
            if total_time > 0.2:
                logger.debug(
                    f"{self.task_id}--批量颜色检测: 检测{color_count}种颜色, "
                    f"总像素数: {total_pixel_count}, 总耗时: {total_time:.3f}s "
                    f"(截图: {screenshot_time:.3f}s, 区域处理: {region_time:.3f}s, "
                    f"颜色检测: {color_detect_time:.3f}s)"
                )

            return {
                "total_pixel_count": total_pixel_count,
                "colors": color_results,
                "processing_time": total_time,
                "screenshot_time": screenshot_time,
                "region_time": region_time,
                "color_detect_time": color_detect_time
            }

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--批量颜色检测失败: {e}, 耗时: {total_time:.3f}s")
            return {"total_pixel_count": 0, "colors": {}, "error": str(e), "processing_time": total_time}

    def _save_color_debug_image(self, screenshot, color_mask, target_color,
                                pixel_count, region, offset_x, offset_y):
        """保存颜色识别的调试图像"""
        start_time = time.time()
        try:
            # 创建调试图像
            debug_img = screenshot.copy()

            # 将掩码应用到原图（高亮显示匹配区域）
            highlighted = debug_img.copy()
            highlighted[color_mask > 0] = [0, 255, 0]  # 用绿色高亮匹配区域

            # 混合原图和高亮图
            alpha = 0.7
            debug_img = cv2.addWeighted(debug_img, 1 - alpha, highlighted, alpha, 0)

            # 添加文本信息
            text_lines = [
                f"Target RGB: {target_color}",
                f"Matched Pixels: {pixel_count}",
                f"Region: {region}" if region else "Full Screen"
            ]

            for i, text in enumerate(text_lines):
                cv2.putText(debug_img, text, (10, 30 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"color_detection_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            save_time = time.time() - start_time
            logger.debug(f"{self.task_id}--颜色识别调试图像已保存: {debug_path}, 耗时: {save_time:.3f}s")

        except Exception as e:
            save_time = time.time() - start_time
            logger.warning(f"{self.task_id}--保存颜色识别调试图像失败: {e}, 耗时: {save_time:.3f}s")



    def safe_color_diff(actual, target):
        """安全计算颜色差异，避免整数溢出"""
        return abs(int(actual) - int(target))

    def check_point_color(self, point: Tuple[int, int],
                          target_color: Tuple[int, int, int],
                          color_tolerance: int = 5,
                          debug: bool = False) -> Union[Tuple[int, int], bool]:
        """
        检查指定点的颜色是否与目标颜色一致
        """
        start_time = time.time()
        try:
            # 获取屏幕截图
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            screenshot_time = time.time() - screenshot_start

            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            height, width = screenshot.shape[:2]
            x, y = point

            # 检查坐标是否在有效范围内
            if x < 0 or x >= width or y < 0 or y >= height:
                logger.warning(f"{self.task_id}--坐标点({x}, {y})超出屏幕范围({width}x{height})")
                return False

            # 获取该点的颜色值 (BGR格式)
            pixel_color_bgr = screenshot[y, x]
            b, g, r = pixel_color_bgr

            # 将目标颜色转换为BGR
            target_bgr = (target_color[2], target_color[1], target_color[0])

            # 修复：使用安全的整数比较，避免溢出
            def safe_color_diff(actual, target):
                """安全计算颜色差异，避免整数溢出"""
                return abs(int(actual) - int(target))

            # 检查颜色是否在容差范围内（修复溢出问题）
            color_matches = (
                    safe_color_diff(r, target_color[0]) <= color_tolerance and
                    safe_color_diff(g, target_color[1]) <= color_tolerance and
                    safe_color_diff(b, target_color[2]) <= color_tolerance
            )

            # 计算总颜色差异（用于调试）
            color_diff = (
                    safe_color_diff(r, target_color[0]) +
                    safe_color_diff(g, target_color[1]) +
                    safe_color_diff(b, target_color[2])
            )

            if debug:
                debug_start = time.time()
                self._save_point_color_debug_image(
                    screenshot, point, pixel_color_bgr, target_color,
                    color_matches, color_diff, color_tolerance
                )
                debug_time = time.time() - debug_start
                logger.debug(f"{self.task_id}--点颜色检查调试图像保存耗时: {debug_time:.3f}s")

            total_time = time.time() - start_time
            logger.debug(
                f"{self.task_id}--点颜色检查: 坐标({x}, {y}), "
                f"实际颜色RGB({r}, {g}, {b}), 目标颜色RGB{target_color}, "
                f"颜色差异: {color_diff}, 容差: {color_tolerance}, 匹配: {color_matches}, "
                f"耗时: {total_time:.3f}s (截图: {screenshot_time:.3f}s)"
            )

            if color_matches:
                return point  # 返回原始坐标点
            else:
                return False

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--检查点颜色失败: {e}, 耗时: {total_time:.3f}s")
            return False



    def check_multiple_points_color_batch(self, point_color_pairs: List[Tuple[Tuple[int, int], Tuple[int, int, int]]],
                                          color_tolerance: int = 5) -> bool:
        """
        批量检查多个坐标点的不同颜色，只截图一次

        Args:
            point_color_pairs: [(point, target_color), ...]
            color_tolerance: 颜色容差

        Returns:
            bool: 所有点颜色都匹配返回True，否则False
        """
        start_time = time.time()

        try:
            # 只截图一次
            screenshot_start = time.time()
            screenshot = self.d.screenshot(format='opencv')
            screenshot_time = time.time() - screenshot_start

            if screenshot is None:
                return False

            height, width = screenshot.shape[:2]

            # 检查所有点
            for i, (point, target_color) in enumerate(point_color_pairs):
                x, y = point

                # 检查坐标范围
                if x < 0 or x >= width or y < 0 or y >= height:
                    logger.debug(f"{self.task_id}--坐标点{point}超出范围")
                    return False

                # 获取颜色并比较
                b, g, r = screenshot[y, x]
                target_b, target_g, target_r = target_color[2], target_color[1], target_color[0]  # RGB转BGR

                # 颜色比较
                if (abs(int(r) - target_r) > color_tolerance or
                        abs(int(g) - target_g) > color_tolerance or
                        abs(int(b) - target_b) > color_tolerance):
                    logger.debug(f"{self.task_id}--点{point}颜色不匹配: ({r},{g},{b}) vs {target_color}")
                    return False

            total_time = time.time() - start_time
            logger.debug(f"{self.task_id}--批量颜色检查通过, 检查{len(point_color_pairs)}个点, 耗时: {total_time:.3f}s")
            return True

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"{self.task_id}--批量颜色检查失败: {e}, 耗时: {total_time:.3f}s")
            return False

    def _save_point_color_debug_image(self, screenshot, point, actual_color_bgr,
                                      target_color, color_matches, color_diff, tolerance):
        """保存点颜色检查的调试图像"""
        start_time = time.time()
        try:
            debug_img = screenshot.copy()
            x, y = point

            # 在点上绘制标记
            marker_color = (0, 255, 0) if color_matches else (0, 0, 255)  # 绿色匹配，红色不匹配
            cv2.drawMarker(debug_img, (x, y), marker_color, cv2.MARKER_CROSS, 20, 2)

            # 绘制一个圆圈突出显示点
            cv2.circle(debug_img, (x, y), 15, marker_color, 2)

            # 添加文本信息
            actual_rgb = (actual_color_bgr[2], actual_color_bgr[1], actual_color_bgr[0])
            target_rgb = target_color

            text_lines = [
                f"Point: ({x}, {y})",
                f"Actual: RGB{actual_rgb}",
                f"Target: RGB{target_rgb}",
                f"Diff: {color_diff}",
                f"Tolerance: {tolerance}",
                f"Match: {'Yes' if color_matches else 'No'}"  # 改为英文
            ]

            # 计算文本位置（确保在图像内）
            text_x = max(10, min(x - 100, screenshot.shape[1] - 300))
            text_y = max(100, min(y - 80, screenshot.shape[0] - len(text_lines) * 30))

            for i, text in enumerate(text_lines):
                cv2.putText(debug_img, text, (text_x, text_y + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(debug_img, text, (text_x, text_y + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"point_color_check_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            save_time = time.time() - start_time
            logger.debug(f"{self.task_id}--点颜色检查调试图像已保存: {debug_path}, 耗时: {save_time:.3f}s")

        except Exception as e:
            save_time = time.time() - start_time
            logger.warning(f"{self.task_id}--保存点颜色检查调试图像失败: {e}, 耗时: {save_time:.3f}s")




    def click_coordinate(self, x: int, y: int, duration: float = None, time_sleep: float = 2) -> None:
        """点击坐标"""
        start_time = time.time()
        if duration is None:
            self.d.click(x, y)
        else:
            self.d.long_click(x, y, duration=duration)

        click_time = time.time() - start_time
        logger.debug(f'{self.task_id}--点击坐标: ({x}, {y}), 耗时: {click_time:.3f}s')
        sleep(time_sleep)

    def app_screenshot(self, name: str, path: str = None, region: Tuple[int, int, int, int] = None) -> str:
        """优化版截图方法 - 使用原子操作保存，提升性能和稳定性"""
        start_time = time.time()
        temp_path = None

        try:
            # 1. 截图操作
            screenshot_start = time.time()
            screenshot = self.d.screenshot()
            screenshot_time = time.time() - screenshot_start

            # 2. 区域裁剪（如果有）
            crop_time = 0
            if region:
                crop_start = time.time()
                screenshot = screenshot.crop(region)
                crop_time = time.time() - crop_start

            # 3. 确定保存路径
            save_dir = path if path else self.img_path
            save_path = os.path.join(save_dir, f"{name}.png")
            os.makedirs(save_dir, exist_ok=True)

            # 4. 创建临时文件
            buffer_start = time.time()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
            buffer_time = time.time() - buffer_start

            # 5. 保存到临时文件
            save_start = time.time()
            screenshot.save(temp_path, format='PNG')  # 移除压缩参数
            save_time = time.time() - save_start

            # 6. 原子操作：移动文件
            move_start = time.time()
            try:
                # 如果目标文件已存在，先删除
                if os.path.exists(save_path):
                    os.unlink(save_path)  # 使用unlink更高效
                shutil.move(temp_path, save_path)
                temp_path = None  # 移动成功后标记为None，避免重复删除
            except OSError as e:
                # 文件操作失败时使用备用方案：直接保存
                logger.warning(f"{self.task_id}--文件移动失败，使用直接保存: {e}")
                screenshot.save(save_path, format='PNG')  # 移除压缩参数
            move_time = time.time() - move_start

            # 7. 性能统计和日志
            total_time = time.time() - start_time

            # 根据耗时决定日志级别
            log_level = logger.warning if total_time > 2.0 else logger.debug

            log_level(
                f'{self.task_id}--截图保存成功: {save_path}\n'
                f'  总耗时: {total_time:.3f}s\n'
                f'  步骤耗时 - 截图: {screenshot_time:.3f}s, 裁剪: {crop_time:.3f}s, '
                f'临时文件: {buffer_time:.3f}s, 保存: {save_time:.3f}s, 移动: {move_time:.3f}s\n'
                f'  图片尺寸: {screenshot.size}'
            )

            return save_path

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f'{self.task_id}--截图保存失败: {e}\n'
                f'  参数: name={name}, path={path}, region={region}\n'
                f'  耗时: {total_time:.3f}s'
            )
            # 返回预期的保存路径，即使失败
            save_dir = path if path else self.img_path
            return os.path.join(save_dir, f"{name}.png")

        finally:
            # 8. 清理临时文件（如果存在）
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.debug(f'{self.task_id}--临时文件清理失败: {cleanup_error}')

    def app_operations(self, operation: str, package_name: str, **kwargs) -> None:
        """应用操作通用方法"""
        start_time = time.time()
        operations = {
            'install': self.d.app_install,
            'uninstall': self.d.app_uninstall,
            'stop': self.d.app_stop,
            'start': self.d.app_start
        }

        if operation not in operations:
            raise ValueError(f"{self.task_id}--不支持的操作用: {operation}")

        operations[operation](package_name, **kwargs)
        operation_time = time.time() - start_time
        logger.debug(f'{self.task_id}--{operation}应用: {package_name}, 耗时: {operation_time:.3f}s')

    def app_stop_all(self):
        """停止所有应用"""
        start_time = time.time()
        self.d.app_stop_all()
        stop_time = time.time() - start_time
        logger.debug(f'{self.task_id}--停止所有应用, 耗时: {stop_time:.3f}s')
