import os
import glob
import cv2
import fitz  # PyMuPDF
import numpy as np
import logging

# Настройка логгера для пакета
logger = logging.getLogger(__name__)  # логгер по имени модуля
logger.setLevel(logging.INFO)  # уровень по умолчанию

# Хэндлер для консоли
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)


# --- НАСТРОЙКИ ---

# 1. Пути
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
# # 2. Параметры рендеринга
# render_dpi = 400 ## ВЛЯЕТ НА scales_to_try качество рендеринга pdf - делает процесс дольше
# # 3. Параметры поиска по ЦВЕТУ (HSV)
# hsv_red_ranges = [
#     # Нижний диапазон (ближе к 0)
#     (np.array([0, 120, 70]), np.array([10, 255, 255])),
#     # Верхний диапазон (ближе к 180)
#     (np.array([170, 120, 70]), np.array([180, 255, 255]))
# ]

# # 4. Параметры фильтрации контуров
# contour_min_area = 2000  # <--- (Для 200 DPI ~60x60 пикселей) от
# contour_max_area = 100000 # <--- (Для 200 DPI ~366x366 пикселей) до
# contour_aspect_ratio_range = (0.7, 1.3) # <--- От 0.7 до 1.3

# # 5. Параметры сопоставления с шаблоном
# match_threshold = 0.4 
# # (scale < 115/250, т.е. scale < 0.46)
# scales_to_try = np.linspace(0.2, 2, 200)

# # --- КОНЕЦ НАСТРОЕК ---


def load_reference_icons(icon_dir:str = ICON_DIR):
    """
    Загружает все эталонные значки из папки ./icons
    и конвертирует их в оттенки серого для надежного сопоставления.
    """
    reference_icons = {}
    icon_paths = glob.glob(os.path.join(icon_dir, "*.png"))
    icon_paths.extend(glob.glob(os.path.join(icon_dir, "*.jpg")))
    icon_paths.extend(glob.glob(os.path.join(icon_dir, "*.jpeg")))
    
    if not icon_paths:
        logger.debug(f"Ошибка: Не найдены значки в папке {icon_dir}")
        logger.debug("Убедитесь, что файлы имеют расширение .png или .jpg")
        return None

    for path in icon_paths:
        icon_name = os.path.basename(path)
        image = cv2.imread(path)
        if image is None:
            logger.debug(f"Не удалось прочитать значок: {path}")
            continue
        gray_icon = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        reference_icons[icon_name] = gray_icon
        
    logger.debug(f"Загружено {len(reference_icons)} эталонных значков.")
    return reference_icons


def find_icons_in_pdf(pdf_path, icon_dir:str = ICON_DIR, **kwargs):
    """
    Ищет значки в PDF, используя словарь для хранения ЛУЧШЕГО результата.
    """
    reference_icons = load_reference_icons(icon_dir)
    logger.debug(len(reference_icons))
    render_dpi = kwargs.get("render_dpi", 400)
    hsv_red_ranges = kwargs.get(
        "hsv_red_ranges",
        [
            (np.array([0, 120, 70]), np.array([10, 255, 255])),
            (np.array([170, 120, 70]), np.array([180, 255, 255]))
        ]
    )
    contour_min_area = kwargs.get("contour_min_area", 2000)
    contour_max_area = kwargs.get("contour_max_area", 100000)
    contour_aspect_ratio_range = kwargs.get("contour_aspect_ratio_range", (0.7, 1.3))
    match_threshold = kwargs.get("match_threshold", 0.4)
    scales_to_try = kwargs.get("scales_to_try", np.linspace(0.2, 2, 200))

    found_icons_dict = {} # лучше кандидаты
    candidate_rois_for_return = [] # Сохраним все ROI для возможного анализа
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.info(f"Ошибка: Не удалось открыть PDF {pdf_path}. {e}")
        return
    
    # logger.debug(f"\nНачинаю поиск в {pdf_path} (Всего страниц: {len(doc)})...")

    # for page_num in range(len(doc)):
    page_nums = min([len(doc),2])
    for page_num in range(page_nums):
        page = doc.load_page(page_num)
        logger.debug(f"--- Обрабатываю страницу {page_num + 1} ---")
        
        # 1. Рендеринг
        pix = page.get_pixmap(dpi=render_dpi)
        page_image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if page_image.shape[2] == 4:
            page_image_bgr = cv2.cvtColor(page_image, cv2.COLOR_RGBA2BGR)
        else:
            page_image_bgr = cv2.cvtColor(page_image, cv2.COLOR_RGB2BGR)

        # 2. Конвертация
        page_gray = cv2.cvtColor(page_image_bgr, cv2.COLOR_BGR2GRAY)
        page_hsv = cv2.cvtColor(page_image_bgr, cv2.COLOR_BGR2HSV)

        # 3. Маска красного цвета
        (lower1, upper1) = hsv_red_ranges[0]
        (lower2, upper2) = hsv_red_ranges[1]
        mask1 = cv2.inRange(page_hsv, lower1, upper1)
        mask2 = cv2.inRange(page_hsv, lower2, upper2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # 4. Поиск контуров
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        logger.debug(f"  [i] Найдено {len(contours)} красных объектов-кандидатов.")
        
        # 5. Фильтрация контуров и сбор ROI
        candidate_rois = [] 
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (contour_min_area < area < contour_max_area):
                continue
            logger.debug('Пройдена проверка на макс размер')

            x, y, w, h = cv2.boundingRect(cnt)
            
            aspect_ratio = w / float(h)
            if not (contour_aspect_ratio_range[0] < aspect_ratio < contour_aspect_ratio_range[1]):
                continue
            logger.debug('Пройдена проверка на contour_aspect_ratio_range')
            
            logger.debug(f"  [i] Найден хороший кандидат (похож на ромб) в [x:{x}, y:{y}]")
            
            # Вырезаем ROI (с вашим отступом 3)
            padding = 0
            y1 = max(0, y - padding)
            y2 = min(page_gray.shape[0], y + h + padding)
            x1 = max(0, x - padding)
            x2 = min(page_gray.shape[1], x + w + padding)
            
            roi_gray = page_gray[y1:y2, x1:x2]
            candidate_rois.append(roi_gray)
            candidate_rois_for_return.append(roi_gray)


        # 6. Сопоставление (с обновленной логикой)
        
        for icon_name, icon_gray in reference_icons.items():
            
            # Проверяем каждый вырезанный "красный квадрат"
            for roi_gray in candidate_rois:
            
                # Мы должны проверить ВСЕ ROI, чтобы найти лучший результат.
                h_icon, w_icon = icon_gray.shape
                best_match_value = -1.0 
                best_match_scale = 0.0

                for scale in scales_to_try:
                    new_w, new_h = int(w_icon * scale), int(h_icon * scale)
                    
                    if new_w == 0 or new_h == 0:
                        continue
                    if new_h > roi_gray.shape[0] or new_w > roi_gray.shape[1]:
                        continue
                    
                    resized_icon = cv2.resize(icon_gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    
                    # Используем ваши настройки с blur
                    roi_blur = cv2.GaussianBlur(roi_gray, (1, 1), 0)
                    icon_blur = cv2.GaussianBlur(resized_icon, (1, 1), 0)
                    
                    result = cv2.matchTemplate(roi_blur, icon_blur, cv2.TM_CCOEFF_NORMED)
                    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

                    if max_val > best_match_value:
                        best_match_value = max_val
                        best_match_scale = scale
                
                # Проверяем, прошли ли мы порог
                if best_match_value >= match_threshold:
                    # Теперь проверяем, лучше ли этот результат (из этого ROI),
                    # чем тот, что уже сохранен в словаре (из ДРУГОГО ROI).
                    current_best = found_icons_dict.get(icon_name, 0.0) # 0.0 - если еще не нашли
                    
                    if best_match_value > current_best:
                        # Это новый рекорд для этого значка!
                        found_icons_dict[icon_name] = best_match_value
                        # Печатаем только при обновлении
                        logger.debug(f"  [✓] ОБНОВЛЕН РЕЗУЛЬТАТ: {icon_name} (новое совпадение: {best_match_value*100:.1f}%)")
                        logger.debug(roi_blur.shape)

    doc.close()
    return (found_icons_dict, candidate_rois_for_return)
