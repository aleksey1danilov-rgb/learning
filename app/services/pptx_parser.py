"""Parser .pptx -> elements for course editor."""
import io
import base64
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE, MSO_SHAPE

EMU_PER_PX = 9525


def _emu_to_px(value):
    if value is None:
        return 0
    return int(round(value / EMU_PER_PX))


def _extract_color(font_or_fill):
    try:
        rgb = font_or_fill.rgb
        if rgb is not None:
            return '#' + str(rgb)
    except Exception:
        pass
    return None


def _extract_text_element(shape, x, y, w, h):
    tf = shape.text_frame
    text = tf.text or ''
    if not text.strip():
        return None
    font_name = 'Inter'
    font_size = 16
    color = '#0b0c10'
    bold = False
    italic = False
    align = 'left'
    try:
        for para in tf.paragraphs:
            for run in para.runs:
                if run.text and run.text.strip():
                    if run.font.name:
                        font_name = run.font.name
                    if run.font.size:
                        font_size = int(run.font.size.pt)
                    c = _extract_color(run.font.color)
                    if c:
                        color = c
                    bold = bool(run.font.bold)
                    italic = bool(run.font.italic)
                    break
            if font_size != 16:
                break
        try:
            from pptx.enum.text import PP_ALIGN
            align_map = {PP_ALIGN.LEFT: 'left', PP_ALIGN.CENTER: 'center', PP_ALIGN.RIGHT: 'right'}
            if tf.paragraphs and tf.paragraphs[0].alignment in align_map:
                align = align_map[tf.paragraphs[0].alignment]
        except Exception:
            pass
    except Exception:
        pass
    if font_size == 16:
        if h > 200:
            font_size = 32
        elif h > 100:
            font_size = 24
        elif h > 50:
            font_size = 18
    safe_text = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(chr(10), '<br>'))
    if bold:
        safe_text = '<b>' + safe_text + '</b>'
    if italic:
        safe_text = '<i>' + safe_text + '</i>'
    return {
        'type': 'text', 'content': safe_text,
        'x': x, 'y': y,
        'width': max(60, w), 'height': max(30, h),
        'font_size': font_size, 'font': font_name, 'color': color,
        'text_align': align, 'bg_color': 'transparent',
    }


def _extract_image_element(shape, x, y, w, h):
    try:
        img = shape.image
        blob = img.blob
        ext = img.ext or 'png'
        mime = 'image/jpeg' if ext.lower() in ('jpg', 'jpeg') else 'image/' + ext
        b64 = base64.b64encode(blob).decode('ascii')
        return {
            'type': 'image', 'content': 'data:' + mime + ';base64,' + b64,
            'x': x, 'y': y, 'width': max(20, w), 'height': max(20, h),
        }
    except Exception:
        return None


_SHAPE_MAP = {
    MSO_SHAPE.OVAL: 'circle',
    MSO_SHAPE.ROUNDED_RECTANGLE: 'square',
    MSO_SHAPE.RECTANGLE: 'square',
    MSO_SHAPE.ISOSCELES_TRIANGLE: 'triangle',
    MSO_SHAPE.RIGHT_TRIANGLE: 'triangle',
    MSO_SHAPE.DIAMOND: 'diamond',
    MSO_SHAPE.STAR_5_POINT: 'star',
    MSO_SHAPE.HEXAGON: 'hexagon',
    MSO_SHAPE.RIGHT_ARROW: 'arrow',
    MSO_SHAPE.LEFT_RIGHT_ARROW: 'arrow',
}


def _extract_shape_element(shape, x, y, w, h):
    # Линия — особый случай
    if shape.shape_type == MSO_SHAPE_TYPE.LINE:
        our_shape = 'line'
    else:
        shape_type = None
        try:
            shape_type = shape.auto_shape_type
        except Exception:
            pass
        our_shape = _SHAPE_MAP.get(shape_type, 'square')

    fill_color = '#6C3EB8'
    # Для LINE цвет берём из stroke (у линии нет заливки)
    if shape.shape_type == MSO_SHAPE_TYPE.LINE:
        try:
            if shape.line.color and shape.line.color.rgb:
                fill_color = '#' + str(shape.line.color.rgb)
        except Exception:
            pass
    else:
        try:
            if shape.fill.type is not None and shape.fill.type != 5:
                fc = _extract_color(shape.fill.fore_color)
                if fc:
                    fill_color = fc
        except Exception:
            pass

    stroke_color = 'transparent'
    stroke_width = 0
    try:
        if shape.line.color and shape.line.color.rgb:
            stroke_color = '#' + str(shape.line.color.rgb)
        if shape.line.width:
            stroke_width = max(0, int(shape.line.width.pt))
    except Exception:
        pass

    return {
        'type': 'shape', 'shape': our_shape, 'content': '',
        'x': x, 'y': y, 'width': max(20, w), 'height': max(20, h),
        'fill': fill_color, 'stroke': stroke_color, 'stroke_width': stroke_width,
    }

def _extract_group_elements(group_shape, base_x, base_y):
    """Точный парсинг групп через XML координаты (chOff/chExt)."""
    result = []
    
    grp_x = grp_y = 0
    grp_w, grp_h = 960, 540
    ch_x = ch_y = 0
    ch_w, ch_h = grp_w, grp_h
    
    try:
        grp_xfrm = group_shape._element.grpSpPr.xfrm
        if grp_xfrm is not None:
            grp_x = _emu_to_px(grp_xfrm.off.x)
            grp_y = _emu_to_px(grp_xfrm.off.y)
            grp_w = _emu_to_px(grp_xfrm.ext.cx)
            grp_h = _emu_to_px(grp_xfrm.ext.cy)
            if grp_xfrm.chOff is not None:
                ch_x = _emu_to_px(grp_xfrm.chOff.x)
                ch_y = _emu_to_px(grp_xfrm.chOff.y)
            if grp_xfrm.chExt is not None:
                ch_w = _emu_to_px(grp_xfrm.chExt.cx)
                ch_h = _emu_to_px(grp_xfrm.chExt.cy)
    except Exception:
        pass
    
    for sub in group_shape.shapes:
        if ch_w > 0 and ch_h > 0:
            rel_x = (sub.left - ch_x) / ch_w
            rel_y = (sub.top - ch_y) / ch_h
        else:
            rel_x = rel_y = 0
        
        abs_x = grp_x + rel_x * grp_w
        abs_y = grp_y + rel_y * grp_h
        
        sx = _nx(abs_x)
        sy = _ny(abs_y)
        sw = _nw(sub.width)
        sh = _nh(sub.height)
        
        if sub.shape_type == MSO_SHAPE_TYPE.GROUP:
            result.extend(_extract_group_elements(sub, sx, sy))
        else:
            el = _shape_to_element(sub, sx, sy, sw, sh)
            if el:
                result.append(el)
    
    return result

def _shape_to_element(shape, x, y, w, h):
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        return None
    # Текст — приоритет
    if shape.has_text_frame and shape.text_frame.text.strip():
        return _extract_text_element(shape, x, y, w, h)
    # Картинки
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return _extract_image_element(shape, x, y, w, h)
    # Линии
    if shape.shape_type == MSO_SHAPE_TYPE.LINE:
        return _extract_shape_element(shape, x, y, w, h)
    # Всё остальное с заливкой или контуром
    try:
        has_fill = shape.fill is not None and shape.fill.type is not None and shape.fill.type != 5
    except Exception:
        has_fill = False
    try:
        has_line = False
        if shape.line is not None:
            if shape.line.color and shape.line.color.rgb:
                has_line = True
            elif shape.line.width:
                has_line = True
    except Exception:
        has_line = False
    if has_fill or has_line:
        return _extract_shape_element(shape, x, y, w, h)
    return None


# ===== Глобальные параметры нормализации (обновляются в parse_pptx) =====
_CURRENT_SCALE = 1.0
_CURRENT_OFFSET_X = 0
_CURRENT_OFFSET_Y = 0


def _nx(emu):
    return int(round(_emu_to_px(emu) * _CURRENT_SCALE + _CURRENT_OFFSET_X))


def _ny(emu):
    return int(round(_emu_to_px(emu) * _CURRENT_SCALE + _CURRENT_OFFSET_Y))


def _nw(emu):
    return int(round(_emu_to_px(emu) * _CURRENT_SCALE))


def _nh(emu):
    return int(round(_emu_to_px(emu) * _CURRENT_SCALE))


def parse_pptx(file_bytes):
    """Парсит .pptx, нормализует координаты к 960x540, возвращает слайды с элементами и фоном."""
    TARGET_W = 960
    TARGET_H = 540

    prs = Presentation(io.BytesIO(file_bytes))
    src_w = _emu_to_px(prs.slide_width)
    src_h = _emu_to_px(prs.slide_height)

    global _CURRENT_SCALE, _CURRENT_OFFSET_X, _CURRENT_OFFSET_Y
    scale = min(TARGET_W / src_w, TARGET_H / src_h)
    offset_x = (TARGET_W - src_w * scale) / 2
    offset_y = (TARGET_H - src_h * scale) / 2
    _CURRENT_SCALE = scale
    _CURRENT_OFFSET_X = offset_x
    _CURRENT_OFFSET_Y = offset_y

    slides = []
    for slide in prs.slides:
        elements = []
        bg_color = "#ffffff"
        bg_image = ""
        try:
            bg = slide.background
            if bg.fill.type is not None:
                c = _extract_color(bg.fill.fore_color)
                if c:
                    bg_color = c
        except Exception:
            pass
        # Сначала фигуры из layout (фон/декор)
        try:
            layout = slide.slide_layout
            for shape in layout.shapes:
                x = _nx(shape.left)
                y = _ny(shape.top)
                w = _nw(shape.width)
                h = _nh(shape.height)
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    elements.extend(_extract_group_elements(shape, x, y))
                else:
                    el = _shape_to_element(shape, x, y, w, h)
                    if el:
                        elements.append(el)
        except Exception:
            pass

        # Потом фигуры самого слайда
        for shape in slide.shapes:
            x = _nx(shape.left)
            y = _ny(shape.top)
            w = _nw(shape.width)
            h = _nh(shape.height)
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                elements.extend(_extract_group_elements(shape, x, y))
            else:
                el = _shape_to_element(shape, x, y, w, h)
                if el:
                    elements.append(el)


        slides.append({
            "elements": elements,
            "bg_color": bg_color,
            "bg_image": bg_image,
        })

    return {
        "slide_width": TARGET_W,
        "slide_height": TARGET_H,
        "source_width": src_w,
        "source_height": src_h,
        "slides": slides,
    }
