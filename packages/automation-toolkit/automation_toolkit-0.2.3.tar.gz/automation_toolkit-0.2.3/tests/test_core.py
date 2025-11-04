from automation_toolkit import AutomationToolkit

# from automation_toolkit.core import AutomationToolkit
tool = AutomationToolkit(
    device="R38N100G4EJ",
    img_path="./images",
    debug_img="./debug",
    # ocr_model_path=r"C:\Users\A\PycharmProjects\websoket_ui\ch_PP-OCRv4_det_infer.onnx"
)
# print(tool.compare_region_similarity('image.png', (162, 823, 332, 870),debug=True))
# tool.s
# 使用OCR查找文字
# result = tool.ocr_find_text(
#     target_text="武林",
#     # region=(557, 330, 2070, 906),  # 在指定区域查找
#     # region=(766, 413, 914, 452),  # 在指定区域查找
#     # min_confidence=0.6,
#     # debug=True
# )
print(tool.detect_multiple_colors_in_region([(220, 117, 153), (139, 196, 226)], region=None, color_tolerance=20,
                                            debug=True))
# data = tool.img_match(r'C:\Users\A\PycharmProjects\websoket_ui\image\NSHSY\occupation\su_wen.png', min_similarity=0.85,
#                      max_matches=3,region=(25, 102,543, 924))
# if data:
#     point = None
#     if isinstance(data, list):
#         # logger.info(f"[task_id {self.task_id} ---Client {self.devices}] 找到多个相同的职业")
#         for i in data:
#             if not point:
#                 # logger.info(f"[task_id {self.task_id} ---Client {self.devices}] 将第一个坐标写在变量中")
#                 point = i['point']
#             else:
#                 if i['point'][1] > point[1]:
#                     pass
#                     # logger.info(
#                     #     f"[task_id {self.task_id} ---Client {self.devices}] 当前坐标比变量中的坐标低,不使用这个坐标")
#                 else:
#                     point = i['point']
#                     # logger.info(
#                     #     f"[task_id {self.task_id} ---Client {self.devices}] 当前坐标比变量中的坐标高,覆盖变量中的坐标")
#     else:
#         # logger.info(f"[task_id {self.task_id} ---Client {self.devices}] 只找到一个选择的职业")
#         point = data['point']
#
#     print(point)

# tool.img_click(r'C:\Users\A\PycharmProjects\websoket_ui\image\NSHSY\occupation\long_yin.png',min_similarity=0.85)