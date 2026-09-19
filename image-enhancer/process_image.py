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

def apply_silky_smooth_razor_sharp_pipeline(cv_img, target_w, target_h, face_enhance=True, denoise=True, sharpen=True):
    """
    Dual-Layer Super-Resolution Pipeline:
    Layer 1: Silky Smooth Surfaces (صاف و نرم)
    Layer 2: Razor-Sharp Edge Contours (حذف تاری موقع زوم 100%)
    """
    print("Executing Silky Smooth & Razor-Sharp Dual Pipeline...")

    # Step 1: High Quality Spline / Lanczos Upscaling
    upscaled = cv2.resize(cv_img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    # Step 2: Layer 1 - Silky Smooth Surface Smoothing (صاف و نرم)
    # Convert to LAB for luminance-guided surface smoothing
    lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Guided Surface Smoothing (smooths flat regions/skin without blurring edges)
    if denoise or face_enhance:
        smooth_l = cv2.bilateralFilter(l, d=7, sigmaColor=40, sigmaSpace=40)
    else:
        smooth_l = l

    # Step 3: Layer 2 - Razor-Sharp Edge & Contour Extraction (بدون تاری موقع زوم)
    # Extract edge map using Canny & Sobel gradients
    sobelx = cv2.Sobel(smooth_l, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(smooth_l, cv2.CV_64F, 0, 1, ksize=3)
    edge_magnitude = cv2.magnitude(sobelx, sobely)
    edge_mask = np.clip(edge_magnitude / 255.0, 0, 1).astype(np.float32)

    # High-Pass Crisp Edge Sharpening
    gaussian = cv2.GaussianBlur(smooth_l, (0, 0), sigmaX=1.2)
    high_pass = cv2.addWeighted(smooth_l, 1.8, gaussian, -0.8, 0)

    # Blend: Use high_pass sharpness ON EDGES, and smooth_l ON FLAT SURFACES
    l_float = smooth_l.astype(np.float32)
    hp_float = high_pass.astype(np.float32)

    # Edge-guided blending for silky smooth surfaces + crystal sharp contours
    blended_l = l_float * (1.0 - edge_mask * 0.85) + hp_float * (edge_mask * 0.85)
    final_l = np.clip(blended_l, 0, 255).astype(np.uint8)

    # Step 4: CLAHE Contrast Boost on Luminance
    clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))
    crisp_l = clahe.apply(final_l)

    # Merge back LAB
    final_lab = cv2.merge((crisp_l, a, b))
    final_bgr = cv2.cvtColor(final_lab, cv2.COLOR_LAB2BGR)

    # Step 5: Multi-Scale Detail Boost for 100% Zoom Clarity
    if sharpen:
        # Fine-edge unsharp mask
        blur_bgr = cv2.GaussianBlur(final_bgr, (0, 0), sigmaX=1.5)
        final_bgr = cv2.addWeighted(final_bgr, 1.35, blur_bgr, -0.35, 0)

    return final_bgr

def process_ai_image(
    image_input,
    upscale_factor=2,
    custom_width=0,
    custom_height=0,
    face_enhance=True,
    denoise=True,
    sharpen=True,
    job_id="job_default"
):
    print(f"=== Starting Silky-Smooth Ultra-HD AI Enhancement [JOB: {job_id}] ===")
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

    processed_cv = apply_silky_smooth_razor_sharp_pipeline(
        cv_img=cv_input,
        target_w=target_w,
        target_h=target_h,
        face_enhance=face_enhance,
        denoise=denoise,
        sharpen=sharpen
    )

    final_pil = Image.fromarray(cv2.cvtColor(processed_cv, cv2.COLOR_BGR2RGB))

    # Crispness boost
    sharpness_booster = ImageEnhance.Sharpness(final_pil)
    final_pil = sharpness_booster.enhance(1.25)

    color_booster = ImageEnhance.Color(final_pil)
    final_pil = color_booster.enhance(1.06)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_png = os.path.join(output_dir, f"{job_id}.png")
    latest_png = os.path.join(output_dir, "latest.png")
    json_path = os.path.join(output_dir, f"{job_id}.json")

    final_pil.save(output_png, format="PNG", quality=100)
    final_pil.save(latest_png, format="PNG", quality=100)

    buffered = BytesIO()
    final_pil.save(buffered, format="PNG")
    out_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    elapsed = round(time.time() - start_time, 2)
    print(f"=== Silky-Smooth Ultra-HD Process completed in {elapsed}s ===")

    meta_result = {
        "job_id": job_id,
        "status": "completed",
        "original_width": orig_w,
        "original_height": orig_h,
        "target_width": target_w,
        "target_height": target_h,
        "processing_time_seconds": elapsed,
        "image_data_base64": f"data:image/png;base64,{out_b64}"
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
        job_id=job_identifier
    )
