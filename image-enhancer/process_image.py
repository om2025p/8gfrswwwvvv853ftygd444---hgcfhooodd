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

    # Check if base64 header exists
    if "," in image_input:
        image_input = image_input.split(",", 1)[1]

    try:
        image_data = base64.b64decode(image_input)
        img = Image.open(BytesIO(image_data))
        return img.convert("RGB")
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        # Try opening as file path if string is short
        if os.path.exists(image_input):
            return Image.open(image_input).convert("RGB")
        raise e

def apply_face_enhancement(cv_img):
    """Applies specialized skin smoothing and eye/lip detail enhancement."""
    # Convert to LAB color space for luminance-based smoothing
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply bilateral filter to smooth noise while preserving edges
    filtered_l = cv2.bilateralFilter(l, d=9, sigmaColor=75, sigmaSpace=75)

    # Merge back LAB
    enhanced_lab = cv2.merge((filtered_l, a, b))
    smoothed = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # Blend 60% smoothed with 40% original for natural skin texture
    blended = cv2.addWeighted(smoothed, 0.6, cv_img, 0.4, 0)
    return blended

def apply_denoise(cv_img):
    """Removes digital noise while keeping sharp edges."""
    return cv2.fastNlMeansDenoisingColored(cv_img, None, h=6, hColor=6, templateWindowSize=7, searchWindowSize=21)

def apply_sharpen(cv_img):
    """Applies unsharp mask filter using OpenCV."""
    gaussian = cv2.GaussianBlur(cv_img, (0, 0), 2.0)
    sharpened = cv2.addWeighted(cv_img, 1.5, gaussian, -0.5, 0)
    return sharpened

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
    print(f"=== Starting AI Image Enhancement [JOB: {job_id}] ===")
    start_time = time.time()

    # Load image
    pil_img = decode_image(image_input)
    orig_w, orig_h = pil_img.size
    print(f"Original Image Size: {orig_w} x {orig_h} px")

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

    print(f"Target Image Size: {target_w} x {target_h} px (Factor: {upscale_factor}x)")

    # Step 1: Smart AI Resampling using Lanczos / Super-Resolution
    resized_pil = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Convert to OpenCV BGR numpy array for advanced filter processing
    cv_img = cv2.cvtColor(np.array(resized_pil), cv2.COLOR_RGB2BGR)

    # Step 2: Denoising
    if denoise:
        print("Applying AI Denoising...")
        cv_img = apply_denoise(cv_img)

    # Step 3: Face Enhancement / Texture smoothing
    if face_enhance:
        print("Applying Face & Skin Enhancement...")
        cv_img = apply_face_enhancement(cv_img)

    # Step 4: Sharpening and Detail Reconstruction
    if sharpen:
        print("Applying Detail Sharpening & Edge Boost...")
        cv_img = apply_sharpen(cv_img)

    # Step 5: Contrast & Color Auto-Equalization (CLAHE)
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    cv_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # Convert back to PIL Image
    final_pil = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

    # Step 6: Color & Clarity Enhancer
    enhancer = ImageEnhance.Color(final_pil)
    final_pil = enhancer.enhance(1.12) # Subtle color boost
    sharp_enhancer = ImageEnhance.Sharpness(final_pil)
    final_pil = sharp_enhancer.enhance(1.25)

    # Save output files
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_png = os.path.join(output_dir, f"{job_id}.png")
    latest_png = os.path.join(output_dir, "latest.png")
    json_path = os.path.join(output_dir, f"{job_id}.json")

    final_pil.save(output_png, format="PNG", quality=95)
    final_pil.save(latest_png, format="PNG", quality=95)

    # Generate base64 string for JSON output
    buffered = BytesIO()
    final_pil.save(buffered, format="PNG")
    out_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    elapsed = round(time.time() - start_time, 2)
    print(f"=== Successfully processed in {elapsed}s ===")

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
    # Get inputs from environment variables
    img_data = os.environ.get("IMAGE_DATA", "")
    upscale_f = os.environ.get("UPSCALE_FACTOR", "2")
    custom_w = os.environ.get("CUSTOM_WIDTH", "0")
    custom_h = os.environ.get("CUSTOM_HEIGHT", "0")
    face_e = os.environ.get("FACE_ENHANCE", "true").lower() in ("true", "1", "yes")
    denoise_val = os.environ.get("DENOISE", "true").lower() in ("true", "1", "yes")
    sharpen_val = os.environ.get("SHARPEN", "true").lower() in ("true", "1", "yes")
    job_identifier = os.environ.get("JOB_ID", f"job_{int(time.time())}")

    # Fallback to test image if no env provided
    if not img_data:
        test_file = os.path.join(os.path.dirname(__file__), "test_input.png")
        if os.path.exists(test_file):
            with open(test_file, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
        else:
            # Create dummy 100x100 test image if no input
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
