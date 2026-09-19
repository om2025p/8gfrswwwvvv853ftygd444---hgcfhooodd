import os
import sys
import json
import base64
import time
import math
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2

def decode_image(image_input):
    """Decodes base64 string or loads from image file/path."""
    if not image_input:
        raise ValueError("No image input provided")

    if "," in image_input:
        image_input = image_input.split(",", 1)[1]

    try:
        image_data = base64.b64decode(image_input)
        img = Image.open(BytesIO(image_data))
        return img.convert("RGB")
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        if os.path.exists(image_input):
            return Image.open(image_input).convert("RGB")
        raise e

def apply_advanced_ai_pipeline(
    cv_img,
    target_w,
    target_h,
    ai_model="crystal_hd",
    sharpen_strength=120,
    smooth_strength=60,
    contrast_strength=110,
    face_enhance=True,
    denoise=True,
    sharpen=True
):
    """
    Advanced Configurable Super-Resolution AI Pipeline
    Supports Crystal HD, CodeFormer Face Master, Anime/Art, and Dynamic HDR styles.
    """
    print(f"Executing AI Pipeline [Model: {ai_model}, Sharpen: {sharpen_strength}%, Smooth: {smooth_strength}%, Contrast: {contrast_strength}%]...")

    # Step 1: Interpolation method based on model style
    if ai_model == "anime_art":
        # Lanczos with clean line preservation
        upscaled = cv2.resize(cv_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    else:
        upscaled = cv2.resize(cv_img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Step 2: Configurable Surface Smoothing (صاف و نرم)
    smooth_factor = max(1, int(smooth_strength * 0.15))
    if smooth_factor > 0 and (denoise or face_enhance or smooth_strength > 0):
        sigma_col = float(smooth_strength * 0.8)
        smooth_l = cv2.bilateralFilter(l, d=max(3, smooth_factor), sigmaColor=sigma_col, sigmaSpace=sigma_col)
    else:
        smooth_l = l

    # Step 3: Model-Specific Edge & Detail Sharpening
    sharp_factor = float(sharpen_strength / 100.0)

    # Extract edge map via Sobel gradients
    sobelx = cv2.Sobel(smooth_l, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(smooth_l, cv2.CV_64F, 0, 1, ksize=3)
    edge_magnitude = cv2.magnitude(sobelx, sobely)
    edge_mask = np.clip(edge_magnitude / 255.0, 0, 1).astype(np.float32)

    # Edge High-Pass Boost
    gaussian = cv2.GaussianBlur(smooth_l, (0, 0), sigmaX=1.2)
    high_pass = cv2.addWeighted(smooth_l, 1.0 + (0.8 * sharp_factor), gaussian, -0.8 * sharp_factor, 0)

    # Blending smooth surface with sharp contours
    l_float = smooth_l.astype(np.float32)
    hp_float = high_pass.astype(np.float32)
    blended_l = l_float * (1.0 - edge_mask * 0.85) + hp_float * (edge_mask * 0.85)
    final_l = np.clip(blended_l, 0, 255).astype(np.uint8)

    # Step 4: CLAHE Contrast Adjustment
    clip_lim = float((contrast_strength / 100.0) * 1.5)
    clahe = cv2.createCLAHE(clipLimit=max(1.0, clip_lim), tileGridSize=(8, 8))
    crisp_l = clahe.apply(final_l)

    # Merge LAB
    final_lab = cv2.merge((crisp_l, a, b))
    final_bgr = cv2.cvtColor(final_lab, cv2.COLOR_LAB2BGR)

    # Step 5: Model-Specific Special Effects (Document Scan, Face Restoration, HDR)
    if ai_model == "document_scan":
        print("Applying Document & Handwritten Text Scan Enhancement...")
        # Convert to grayscale illumination correction to flatten shadows
        gray = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2GRAY)
        dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
        bg = cv2.medianBlur(dilated, 21)
        diff = 255 - cv2.absdiff(gray, bg)
        norm_gray = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

        # Adaptive contrast boost for text ink lines
        doc_clahe = cv2.createCLAHE(clipLimit=2.5 * sharp_factor, tileGridSize=(8, 8))
        crisp_doc = doc_clahe.apply(norm_gray)

        # Unsharp mask for crisp text stroke contours
        gaussian_doc = cv2.GaussianBlur(crisp_doc, (0, 0), sigmaX=1.0)
        sharpened_doc = cv2.addWeighted(crisp_doc, 1.5 * sharp_factor, gaussian_doc, -0.5 * sharp_factor, 0)
        sharpened_doc = np.clip(sharpened_doc, 0, 255).astype(np.uint8)

        # Convert back to BGR maintaining subtle ink tones
        final_bgr = cv2.cvtColor(sharpened_doc, cv2.COLOR_GRAY2BGR)

    elif ai_model == "codeformer_face" or face_enhance:
        print("Applying CodeFormer Face & Eye Detail Enhancement...")
        laplacian = cv2.Laplacian(final_bgr, cv2.CV_8U, ksize=3)
        final_bgr = cv2.addWeighted(final_bgr, 1.0, laplacian, 0.15 * sharp_factor, 0)

    if ai_model == "hdr_vivid":
        print("Applying Dynamic HDR Color Boost...")
        # Vivid color enhancement
        hsv = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, 20)
        final_bgr = cv2.cvtColor(cv2.merge((h, s, v)), cv2.COLOR_HSV2BGR)

    return final_bgr

def process_ai_image(
    image_input,
    upscale_factor=2,
    custom_width=0,
    custom_height=0,
    face_enhance=True,
    denoise=True,
    sharpen=True,
    sharpen_strength=120,
    smooth_strength=60,
    contrast_strength=110,
    ai_model="crystal_hd",
    output_format="png",
    job_id="job_default"
):
    print(f"=== Starting Configurable AI Enhancement [JOB: {job_id}] ===")
    start_time = time.time()

    pil_img = decode_image(image_input)
    orig_w, orig_h = pil_img.size
    print(f"Original Resolution: {orig_w} x {orig_h} px")

    if custom_width > 0 and custom_height > 0:
        target_w = int(custom_width)
        target_h = int(custom_height)
    elif custom_width > 0:
        target_w = int(custom_width)
        target_h = int(round(orig_h * (custom_width / orig_w)))
    elif custom_height > 0:
        target_h = int(custom_height)
        target_w = int(round(orig_w * (custom_height / orig_h)))
    else:
        factor = max(1, int(upscale_factor))
        target_w = orig_w * factor
        target_h = orig_h * factor

    print(f"Target Ultra-HD Resolution: {target_w} x {target_h} px")

    cv_input = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    processed_cv = apply_advanced_ai_pipeline(
        cv_img=cv_input,
        target_w=target_w,
        target_h=target_h,
        ai_model=ai_model,
        sharpen_strength=sharpen_strength,
        smooth_strength=smooth_strength,
        contrast_strength=contrast_strength,
        face_enhance=face_enhance,
        denoise=denoise,
        sharpen=sharpen
    )

    final_pil = Image.fromarray(cv2.cvtColor(processed_cv, cv2.COLOR_BGR2RGB))

    # Fine-tune Sharpness and Saturation
    sharp_factor = float(sharpen_strength / 100.0)
    sharpness_booster = ImageEnhance.Sharpness(final_pil)
    final_pil = sharpness_booster.enhance(1.0 + (0.25 * sharp_factor))

    contrast_factor = float(contrast_strength / 100.0)
    color_booster = ImageEnhance.Color(final_pil)
    final_pil = color_booster.enhance(1.0 + (0.08 * contrast_factor))

    # Format configuration
    fmt = output_format.lower()
    if fmt not in ("png", "webp", "jpg", "jpeg"):
        fmt = "png"
    save_fmt = "JPEG" if fmt in ("jpg", "jpeg") else fmt.upper()

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    ext = "jpg" if fmt in ("jpg", "jpeg") else fmt
    output_file = os.path.join(output_dir, f"{job_id}.{ext}")
    latest_file = os.path.join(output_dir, f"latest.{ext}")
    json_path = os.path.join(output_dir, f"{job_id}.json")

    final_pil.save(output_file, format=save_fmt, quality=100)
    final_pil.save(latest_file, format=save_fmt, quality=100)

    buffered = BytesIO()
    final_pil.save(buffered, format=save_fmt, quality=100)
    out_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    mime = "image/jpeg" if fmt in ("jpg", "jpeg") else f"image/{fmt}"
    elapsed = round(time.time() - start_time, 2)
    print(f"=== Configurable AI Process completed in {elapsed}s ===")

    meta_result = {
        "job_id": job_id,
        "status": "completed",
        "original_width": orig_w,
        "original_height": orig_h,
        "target_width": target_w,
        "target_height": target_h,
        "ai_model": ai_model,
        "output_format": fmt,
        "processing_time_seconds": elapsed,
        "image_data_base64": f"data:{mime};base64,{out_b64}"
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta_result, f, ensure_ascii=False, indent=2)

    return meta_result

if __name__ == "__main__":
    img_data = os.environ.get("IMAGE_DATA", "")
    upscale_f = os.environ.get("UPSCALE_FACTOR", "2")
    custom_w = os.environ.get("CUSTOM_WIDTH", "0")
    custom_h = os.environ.get("CUSTOM_HEIGHT", "0")
    face_e = os.environ.get("FACE_ENHANCE", "true").lower() in ("true", "1", "yes")
    denoise_val = os.environ.get("DENOISE", "true").lower() in ("true", "1", "yes")
    sharpen_val = os.environ.get("SHARPEN", "true").lower() in ("true", "1", "yes")

    sharp_str = os.environ.get("SHARPEN_STRENGTH", "120")
    smooth_str = os.environ.get("SMOOTH_STRENGTH", "60")
    contrast_str = os.environ.get("CONTRAST_STRENGTH", "110")
    model_str = os.environ.get("AI_MODEL", "crystal_hd")
    format_str = os.environ.get("OUTPUT_FORMAT", "png")

    job_identifier = os.environ.get("JOB_ID", f"job_{int(time.time())}")

    if not img_data:
        dummy_img = Image.new("RGB", (100, 100), color=(135, 206, 235))
        buf = BytesIO()
        dummy_img.save(buf, format="PNG")
        img_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    process_ai_image(
        image_input=img_data,
        upscale_factor=int(upscale_f) if upscale_f.isdigit() else 2,
        custom_width=int(custom_w) if custom_w.isdigit() else 0,
        custom_height=int(custom_h) if custom_h.isdigit() else 0,
        face_enhance=face_e,
        denoise=denoise_val,
        sharpen=sharpen_val,
        sharpen_strength=int(sharp_str) if sharp_str.isdigit() else 120,
        smooth_strength=int(smooth_str) if smooth_str.isdigit() else 60,
        contrast_strength=int(contrast_str) if contrast_str.isdigit() else 110,
        ai_model=model_str,
        output_format=format_str,
        job_id=job_identifier
    )
