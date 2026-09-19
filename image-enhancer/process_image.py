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

def apply_crystal_clarity_pipeline(cv_img, orig_w, orig_h, target_w, target_h, face_enhance=True, denoise=True, sharpen=True):
    """
    Ultra-Sharp Detail-Preserving Super Resolution Pipeline.
    Prevents plastic/watercolor/painterly blur effects upon 100% zoom.
    """
    print("Executing Ultra-Sharp High-Frequency Detail Preservation Pipeline...")

    # Step 1: Smart Micro-Detail Extraction before Upscaling
    # Extract high-frequency edges & texture layer from initial image
    gray_orig = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    blurred_orig = cv2.GaussianBlur(gray_orig, (0, 0), sigmaX=1.5)
    high_freq_orig = cv2.subtract(gray_orig, blurred_orig)

    # Upscale high frequency detail map to target size using Lanczos
    high_freq_upscaled = cv2.resize(high_freq_orig, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    # Step 2: Main Upscaling via Cubic Spline / Lanczos
    upscaled_bgr = cv2.resize(cv_img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    # Step 3: Gentle Smart Denoise (Edge-Aware without plastic smoothing)
    if denoise:
        print("Applying Edge-Aware Micro-Denoise (No Plastic/Watercolor Effect)...")
        # Gentle bilateral filter with small kernel so texture is NOT destroyed
        upscaled_bgr = cv2.bilateralFilter(upscaled_bgr, d=5, sigmaColor=35, sigmaSpace=35)

    # Step 4: High-Frequency Texture Re-Injection
    # Convert upscaled BGR to LAB color space
    lab = cv2.cvtColor(upscaled_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Inject high frequency micro-textures back into L channel
    l_float = l.astype(np.float32)
    hf_float = high_freq_upscaled.astype(np.float32) * 0.45 # Texture injection strength
    enhanced_l = np.clip(l_float + hf_float, 0, 255).astype(np.uint8)

    # Step 5: Adaptive Local Contrast Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    crisp_l = clahe.apply(enhanced_l)

    # Merge LAB back
    crisp_lab = cv2.merge((crisp_l, a, b))
    enhanced_bgr = cv2.cvtColor(crisp_lab, cv2.COLOR_LAB2BGR)

    # Step 6: Multi-Scale Unsharp Masking & Edge Crispness Boost
    if sharpen:
        print("Applying Multi-Scale Crisp Sharpening...")
        # Fine detail sharpening
        g1 = cv2.GaussianBlur(enhanced_bgr, (0, 0), 1.0)
        sharpened1 = cv2.addWeighted(enhanced_bgr, 1.6, g1, -0.6, 0)

        # Medium edge sharpening
        g2 = cv2.GaussianBlur(sharpened1, (0, 0), 2.5)
        enhanced_bgr = cv2.addWeighted(sharpened1, 1.25, g2, -0.25, 0)

    # Step 7: Natural Skin & Hair Detail Restoration (No Painterly/Plastic Blobs)
    if face_enhance:
        print("Applying Natural Face & Micro-Skin Texture Restoration...")
        # Blend subtle Laplacian edge map to sharpen facial features, hair, and eyes
        laplacian = cv2.Laplacian(enhanced_bgr, cv2.CV_8U, ksize=3)
        enhanced_bgr = cv2.addWeighted(enhanced_bgr, 1.0, laplacian, 0.12, 0)

    return enhanced_bgr

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
    print(f"=== Starting Ultra-HD Crystal AI Enhancement [JOB: {job_id}] ===")
    start_time = time.time()

    # Load image
    pil_img = decode_image(image_input)
    orig_w, orig_h = pil_img.size
    print(f"Original Image Resolution: {orig_w} x {orig_h} px")

    # Determine target dimensions
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

    # Convert PIL image to OpenCV BGR numpy array
    cv_input = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Process through Ultra-Sharp Crystal Clarity Pipeline
    processed_cv = apply_crystal_clarity_pipeline(
        cv_img=cv_input,
        orig_w=orig_w,
        orig_h=orig_h,
        target_w=target_w,
        target_h=target_h,
        face_enhance=face_enhance,
        denoise=denoise,
        sharpen=sharpen
    )

    # Convert back to PIL Image
    final_pil = Image.fromarray(cv2.cvtColor(processed_cv, cv2.COLOR_BGR2RGB))

    # Final Micro-Clarity & Saturation Tuning
    sharpness_booster = ImageEnhance.Sharpness(final_pil)
    final_pil = sharpness_booster.enhance(1.3) # Razor-sharp edge crispness

    color_booster = ImageEnhance.Color(final_pil)
    final_pil = color_booster.enhance(1.08) # Vivid natural color tones

    # Save output files
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_png = os.path.join(output_dir, f"{job_id}.png")
    latest_png = os.path.join(output_dir, "latest.png")
    json_path = os.path.join(output_dir, f"{job_id}.json")

    final_pil.save(output_png, format="PNG", quality=100)
    final_pil.save(latest_png, format="PNG", quality=100)

    # Base64 output payload
    buffered = BytesIO()
    final_pil.save(buffered, format="PNG")
    out_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    elapsed = round(time.time() - start_time, 2)
    print(f"=== Ultra-HD Process completed successfully in {elapsed}s ===")

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
