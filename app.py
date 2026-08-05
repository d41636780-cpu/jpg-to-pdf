import fitz
from pypdf import PdfWriter
from reportlab.lib.pagesizes import portrait
from reportlab.lib.pagesizes import A4, LETTER
import pikepdf
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    send_from_directory,
    Response
)

from pdf2image import convert_from_path
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4, LETTER

import os
import uuid
import json
import time
import shutil


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 50 * 1024 * 1024
MAX_FILES = 20

FILE_LIFETIME = 30 * 60


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


# =========================================================
# FLASK CONFIG
# =========================================================

app.config["MAX_CONTENT_LENGTH"] = MAX_TOTAL_SIZE


# =========================================================
# CREATE FOLDERS
# =========================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# =========================================================
# ALLOWED FILE CHECK
# =========================================================

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_EXTENSIONS


# =========================================================
# CLEAN OLD FILES
# =========================================================

def cleanup_old_files():

    current_time = time.time()

    folders = [
        UPLOAD_FOLDER,
        OUTPUT_FOLDER
    ]

    for folder in folders:

        try:
            items = os.listdir(folder)

        except OSError:
            continue

        for item in items:

            item_path = os.path.join(
                folder,
                item
            )

            try:

                modified_time = os.path.getmtime(
                    item_path
                )

                age = (
                    current_time
                    - modified_time
                )

                if age <= FILE_LIFETIME:
                    continue

                if os.path.isfile(item_path):

                    os.remove(
                        item_path
                    )

                elif os.path.isdir(item_path):

                    # Remove old PDF-to-JPG folders
                    shutil.rmtree(
                        item_path,
                        ignore_errors=True
                    )

            except (
                PermissionError,
                OSError
            ):

                pass


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    cleanup_old_files()

    return render_template(
        "index.html"
    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =========================================================
# PRIVACY
# =========================================================

@app.route("/privacy")
def privacy():

    return render_template(
        "privacy.html"
    )


# =========================================================
# TERMS
# =========================================================

@app.route("/terms")
def terms():

    return render_template(
        "terms.html"
    )


# =========================================================
# JPG TO PDF PAGE
# =========================================================

@app.route("/jpg-to-pdf")
def jpg_to_pdf():

    return render_template(
        "jpg-to-pdf.html"
    )


# =========================================================
# PNG TO PDF PAGE
# =========================================================

@app.route("/png-to-pdf")
def png_to_pdf():

    return render_template(
        "png-to-pdf.html"
    )


# =========================================================
# IMAGE TO PDF PAGE
# =========================================================

@app.route("/image-to-pdf")
def image_to_pdf():

    return render_template(
        "image-to-pdf.html"
    )


# =========================================================
# PDF COMPRESSOR
# =========================================================

@app.route("/pdf-compressor")
def pdf_compressor():
    return render_template("pdf-compressor.html")


@app.route("/compress-pdf", methods=["POST"])
def compress_pdf():
    
    pdf_file = request.files.get("pdf")
    target_value = request.form.get("target_value", "")
    target_unit = request.form.get("target_unit", "KB")

    # -----------------------------------------------------
    # CHECK PDF
    # -----------------------------------------------------

    if not pdf_file or not pdf_file.filename:
        return {
            "error": "Please select a PDF file."
        }, 400

    if not pdf_file.filename.lower().endswith(".pdf"):
        return {
            "error": "Only PDF files are supported."
        }, 400

    # -----------------------------------------------------
    # CHECK TARGET SIZE
    # -----------------------------------------------------

    try:
        target_value = float(target_value)

        if target_value <= 0:
            raise ValueError

    except Exception:

        return {
            "error": "Please enter a valid target size."
        }, 400

    if target_unit == "MB":

        target_bytes = int(
            target_value * 1024 * 1024
        )

    else:

        target_bytes = int(
            target_value * 1024
        )

    # -----------------------------------------------------
    # TARGET LIMITS
    # -----------------------------------------------------

    if target_bytes < 50 * 1024:

        return {
            "error": "Minimum target size is 50 KB."
        }, 400

    if target_bytes > MAX_TOTAL_SIZE:

        return {
            "error": "Target size cannot exceed 50 MB."
        }, 400

    # -----------------------------------------------------
    # CREATE TEMP FILES
    # -----------------------------------------------------

    input_name = (
        f"{uuid.uuid4().hex}_compress_input.pdf"
    )

    output_name = (
        f"{uuid.uuid4().hex}_compressed.pdf"
    )

    input_path = os.path.join(
        UPLOAD_FOLDER,
        input_name
    )

    output_path = os.path.join(
        UPLOAD_FOLDER,
        output_name
    )

    try:

        # -------------------------------------------------
        # SAVE ORIGINAL PDF
        # -------------------------------------------------

        pdf_file.save(input_path)

        original_size = os.path.getsize(
            input_path
        )

        # -------------------------------------------------
        # ALREADY SMALL ENOUGH
        # -------------------------------------------------

        if original_size <= target_bytes:

            shutil.copy2(
                input_path,
                output_path
            )

            final_size = original_size

            reduction = 0

            return {
                "success": True,
                "target_size": target_bytes,
                "original_size": original_size,
                "compressed_size": final_size,
                "reduction": reduction,
                "target_achieved": True,
                "message": (
                    "Your PDF is already smaller "
                    "than the selected target."
                ),
                "download_url":
                    f"/download-compressed-pdf/"
                    f"{output_name}"
            }

        # -------------------------------------------------
        # MULTI-LEVEL COMPRESSION TO REACH TARGET
        # -------------------------------------------------

        # Try multiple compression strategies
        compression_strategies = []

        # Strategy 1: pikepdf compression only
        compression_strategies.append({
            "name": "Standard Compression",
            "dpi": None,
            "quality": None,
            "use_pikepdf": True
        })

        # Strategy 2-15: PDF to images and back with different DPI/Quality
        dpi_levels = [200, 150, 120, 100, 80, 72]
        quality_levels = [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30]

        for dpi in dpi_levels:
            for quality in quality_levels:
                compression_strategies.append({
                    "name": f"DPI {dpi} Quality {quality}",
                    "dpi": dpi,
                    "quality": quality,
                    "use_pikepdf": False
                })

        best_path = None
        best_size = None
        temp_files = []

        for strategy_index, strategy in enumerate(compression_strategies):
            
            temp_pdf = os.path.join(
                UPLOAD_FOLDER,
                f"{uuid.uuid4().hex}_temp_{strategy_index}.pdf"
            )
            
            temp_files.append(temp_pdf)

            try:
                
                if strategy["use_pikepdf"]:
                    # Use pikepdf compression
                    with pikepdf.open(input_path) as pdf:
                        pdf.save(
                            temp_pdf,
                            compress_streams=True,
                            recompress_flate=True,
                            object_stream_mode=pikepdf.ObjectStreamMode.generate
                        )
                else:
                    # Convert PDF to images and back
                    dpi = strategy["dpi"]
                    quality = strategy["quality"]
                    
                    # Create temp folder for images
                    image_folder = os.path.join(
                        OUTPUT_FOLDER,
                        f"{uuid.uuid4().hex}_images"
                    )
                    
                    os.makedirs(image_folder, exist_ok=True)
                    
                    try:
                        # Convert PDF to images
                        pages = convert_from_path(
                            input_path,
                            dpi=dpi,
                            fmt='jpeg'
                        )
                        
                        if not pages:
                            continue
                        
                        # Create new PDF from images
                        pdf_canvas = None
                        
                        for page_index, page in enumerate(pages):
                            
                            # Ensure RGB
                            if page.mode != "RGB":
                                page = page.convert("RGB")
                            
                            # Save image
                            image_path = os.path.join(
                                image_folder,
                                f"page_{page_index}.jpg"
                            )
                            
                            page.save(
                                image_path,
                                "JPEG",
                                quality=quality,
                                optimize=True,
                                progressive=False
                            )
                            
                            # Get image dimensions
                            img_width, img_height = page.size
                            
                            # Create PDF page
                            if pdf_canvas is None:
                                pdf_canvas = canvas.Canvas(
                                    temp_pdf,
                                    pagesize=(img_width, img_height)
                                )
                            else:
                                pdf_canvas.setPageSize((img_width, img_height))
                            
                            # Draw image on page
                            pdf_canvas.drawImage(
                                ImageReader(image_path),
                                0, 0,
                                width=img_width,
                                height=img_height
                            )
                            
                            pdf_canvas.showPage()
                            
                            # Clean up image
                            page.close()
                            
                            # Remove image file
                            try:
                                os.remove(image_path)
                            except:
                                pass
                        
                        if pdf_canvas is not None:
                            pdf_canvas.save()
                        
                        # Clean up image folder
                        try:
                            shutil.rmtree(image_folder, ignore_errors=True)
                        except:
                            pass
                        
                    except Exception as e:
                        print(f"Strategy {strategy_index} failed:", e)
                        # Clean up
                        try:
                            shutil.rmtree(image_folder, ignore_errors=True)
                        except:
                            pass
                        continue
                
                # Check if file was created
                if not os.path.exists(temp_pdf):
                    continue
                
                current_size = os.path.getsize(temp_pdf)
                
                # Keep track of best result
                if best_size is None or current_size < best_size:
                    best_size = current_size
                    best_path = temp_pdf
                
                # If we achieved target, stop
                if current_size <= target_bytes:
                    shutil.copy2(temp_pdf, output_path)
                    best_path = output_path
                    best_size = current_size
                    break
                    
            except Exception as level_error:
                print(f"Compression strategy {strategy_index} error:", level_error)
                continue

        # -------------------------------------------------
        # IF WE HAVE A BEST RESULT, USE IT
        # -------------------------------------------------

        if best_path is None:
            # Fallback: Just copy original
            shutil.copy2(input_path, output_path)
            compressed_size = original_size
            reduction = 0
            target_achieved = False
            message = "Could not compress the PDF further. The original file is provided."
            
        else:
            # Copy best result to output
            if best_path != output_path:
                shutil.copy2(best_path, output_path)
            
            compressed_size = os.path.getsize(output_path)
            
            # If compressed size is still larger than target, try one more aggressive pass
            if compressed_size > target_bytes:
                # Try one final aggressive compression
                try:
                    # Use pikePDF with maximum compression
                    with pikepdf.open(output_path) as pdf:
                        # Remove metadata to save space
                        with pdf.open_metadata() as meta:
                            for key in list(meta):
                                del meta[key]
                        
                        pdf.save(
                            output_path,
                            compress_streams=True,
                            recompress_flate=True,
                            object_stream_mode=pikepdf.ObjectStreamMode.generate,
                            stream_decode_level=pikepdf.StreamDecodeLevel.specialized
                        )
                    
                    compressed_size = os.path.getsize(output_path)
                except:
                    pass
            
            # Calculate reduction
            reduction = ((original_size - compressed_size) / original_size) * 100
            reduction = round(max(reduction, 0), 1)
            
            target_achieved = compressed_size <= target_bytes
            
            if target_achieved:
                message = f"Target size achieved successfully! Compressed to {format_size(compressed_size)}."
            else:
                message = f"Best possible compression: {format_size(compressed_size)}. Target: {format_size(target_bytes)}."

        # -------------------------------------------------
        # RETURN RESPONSE
        # -------------------------------------------------

        return {
            "success": True,
            "target_size": target_bytes,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction": reduction,
            "target_achieved": target_achieved,
            "message": message,
            "download_url": f"/download-compressed-pdf/{output_name}"
        }

    except Exception as error:

        print("PDF COMPRESSOR ERROR:", error)

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

        return {
            "error": "Could not compress the PDF.",
            "details": str(error)
        }, 500

    finally:
        # Clean up temp files
        for temp_file in locals().get("temp_files", []):
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass


# =========================================================
# DOWNLOAD COMPRESSED PDF
# =========================================================

@app.route(
    "/download-compressed-pdf/<filename>"
)
def download_compressed_pdf(filename):

    safe_filename = os.path.basename(
        filename
    )

    if not safe_filename.endswith(
        "_compressed.pdf"
    ):

        return (
            "Invalid file.",
            400
        )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    if not os.path.isfile(file_path):

        return (
            "File not found or expired.",
            404
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="compressed.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# PDF TO JPG PAGE + CONVERSION
# =========================================================

@app.route(
    "/pdf-to-jpg",
    methods=["GET", "POST"]
)
def pdf_to_jpg():

    # -----------------------------------------------------
    # SHOW PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "pdf-to-jpg.html"
        )

    # -----------------------------------------------------
    # GET PDF
    # -----------------------------------------------------

    pdf_file = request.files.get(
        "pdf"
    )

    if not pdf_file or not pdf_file.filename:

        return {
            "error": "Please select a PDF file."
        }, 400

    # -----------------------------------------------------
    # CHECK EXTENSION
    # -----------------------------------------------------

    if not pdf_file.filename.lower().endswith(
        ".pdf"
    ):

        return {
            "error": "Only PDF files are supported."
        }, 400

    # -----------------------------------------------------
    # CHECK SIZE
    # -----------------------------------------------------

    try:

        pdf_file.stream.seek(
            0,
            os.SEEK_END
        )

        pdf_size = (
            pdf_file.stream.tell()
        )

        pdf_file.stream.seek(0)

    except Exception:

        return {
            "error": "Could not read the PDF file."
        }, 400

    if pdf_size > MAX_FILE_SIZE:

        return {
            "error": "PDF file is too large. Maximum size is 10 MB."
        }, 400

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    try:

        dpi = int(
            request.form.get(
                "dpi",
                150
            )
        )

    except ValueError:

        dpi = 150

    try:

        quality = int(
            request.form.get(
                "quality",
                90
            )
        )

    except ValueError:

        quality = 90

    # Safe limits

    if dpi not in (
        100,
        150,
        200,
        300
    ):

        dpi = 150

    if quality not in (
        70,
        85,
        95
    ):

        quality = 90

    # -----------------------------------------------------
    # FILE PATHS
    # -----------------------------------------------------

    file_id = uuid.uuid4().hex

    pdf_path = os.path.join(
        UPLOAD_FOLDER,
        f"{file_id}.pdf"
    )

    output_folder = os.path.join(
        OUTPUT_FOLDER,
        file_id
    )

    try:

        os.makedirs(
            output_folder,
            exist_ok=True
        )

        # -------------------------------------------------
        # SAVE PDF
        # -------------------------------------------------

        pdf_file.save(
            pdf_path
        )

        # -------------------------------------------------
        # CONVERT PDF TO IMAGES
        # -------------------------------------------------

        pages = convert_from_path(
            pdf_path,
            dpi=dpi
        )

        if not pages:

            return {
                "error": "The PDF does not contain any pages."
            }, 400

        image_urls = []

        # -------------------------------------------------
        # SAVE JPG PAGES
        # -------------------------------------------------

        for index, page in enumerate(
            pages,
            start=1
        ):

            image_filename = (
                f"page-{index}.jpg"
            )

            image_path = os.path.join(
                output_folder,
                image_filename
            )

            # Ensure RGB

            if page.mode != "RGB":

                page = page.convert(
                    "RGB"
                )

            page.save(
                image_path,
                "JPEG",
                quality=quality,
                optimize=True
            )

            image_urls.append(
                f"/download-pdf-jpg/"
                f"{file_id}/"
                f"{image_filename}"
            )

        # -------------------------------------------------
        # DELETE ORIGINAL PDF
        # -------------------------------------------------

        try:

            os.remove(
                pdf_path
            )

        except (
            PermissionError,
            OSError
        ):

            pass

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return {
            "success": True,
            "pages": len(image_urls),
            "images": image_urls
        }

    except Exception as error:

        print(
            "PDF TO JPG ERROR:",
            error
        )

        # Remove PDF if conversion failed

        if os.path.exists(
            pdf_path
        ):

            try:

                os.remove(
                    pdf_path
                )

            except (
                PermissionError,
                OSError
            ):

                pass

        # Remove output folder if exists

        if os.path.isdir(
            output_folder
        ):

            shutil.rmtree(
                output_folder,
                ignore_errors=True
            )

        return {
            "error": (
                "Could not convert the PDF. "
                "Please make sure the PDF is valid."
            ),
            "details": str(error)
        }, 500


# =========================================================
# DOWNLOAD PDF TO JPG
# =========================================================

@app.route(
    "/download-pdf-jpg/<file_id>/<filename>"
)
def download_pdf_jpg(
    file_id,
    filename
):

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    safe_file_id = os.path.basename(
        file_id
    )

    safe_filename = os.path.basename(
        filename
    )

    # Only JPG files

    if not safe_filename.lower().endswith(
        ".jpg"
    ):

        return (
            "Invalid file.",
            400
        )

    folder = os.path.join(
        OUTPUT_FOLDER,
        safe_file_id
    )

    # -----------------------------------------------------
    # CHECK FOLDER
    # -----------------------------------------------------

    if not os.path.isdir(
        folder
    ):

        return (
            "File not found or expired.",
            404
        )

    # -----------------------------------------------------
    # CHECK FILE
    # -----------------------------------------------------

    file_path = os.path.join(
        folder,
        safe_filename
    )

    if not os.path.isfile(
        file_path
    ):

        return (
            "File not found or expired.",
            404
        )

    # -----------------------------------------------------
    # SEND JPG
    # -----------------------------------------------------

    return send_from_directory(
        folder,
        safe_filename,
        as_attachment=True,
        download_name=safe_filename,
        mimetype="image/jpeg"
    )


# =========================================================
# CONVERT JPG TO PDF
# =========================================================

@app.route(
    "/convert",
    methods=["POST"]
)
def convert():

    cleanup_old_files()

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    page_size = request.form.get(
        "page_size",
        "a4"
    )

    orientation = request.form.get(
        "orientation",
        "portrait"
    )

    quality = request.form.get(
        "quality",
        "high"
    )

    page_numbers = request.form.get(
        "page_numbers",
        "yes"
    )

    # -----------------------------------------------------
    # ROTATIONS
    # -----------------------------------------------------

    rotation_text = request.form.get(
        "rotations",
        "[]"
    )

    try:

        rotations = json.loads(
            rotation_text
        )

        if not isinstance(
            rotations,
            list
        ):

            rotations = []

    except Exception:

        rotations = []

    # -----------------------------------------------------
    # GET FILES
    # -----------------------------------------------------

    files = request.files.getlist(
        "images"
    )

    # -----------------------------------------------------
    # FILE COUNT
    # -----------------------------------------------------

    if len(files) == 0:

        return (
            "Please select at least one image.",
            400
        )

    if len(files) > MAX_FILES:

        return (
            f"Maximum {MAX_FILES} images are allowed.",
            400
        )

    # -----------------------------------------------------
    # VALIDATE FILES
    # -----------------------------------------------------

    valid_files = []

    total_size = 0

    for file in files:

        if not file:
            continue

        if not file.filename:
            continue

        # Extension

        if not allowed_file(
            file.filename
        ):

            return (
                "Invalid file type. "
                "Only JPG, JPEG, PNG and WebP are allowed.",
                400
            )

        # File size

        try:

            file.stream.seek(
                0,
                os.SEEK_END
            )

            file_size = (
                file.stream.tell()
            )

            file.stream.seek(0)

        except Exception:

            return (
                f"Could not read {file.filename}.",
                400
            )

        if file_size > MAX_FILE_SIZE:

            return (
                f"{file.filename} is too large. "
                "Maximum size is 10 MB per image.",
                400
            )

        total_size += file_size

        valid_files.append(
            file
        )

    # -----------------------------------------------------
    # TOTAL SIZE
    # -----------------------------------------------------

    if total_size > MAX_TOTAL_SIZE:

        return (
            "Total upload size cannot exceed 50 MB.",
            400
        )

    if not valid_files:

        return (
            "No valid images were uploaded.",
            400
        )

    # -----------------------------------------------------
    # JPEG QUALITY
    # -----------------------------------------------------

    if quality == "high":

        jpeg_quality = 95

    elif quality == "medium":

        jpeg_quality = 75

    else:

        jpeg_quality = 50

    # -----------------------------------------------------
    # PAGE SIZE
    # -----------------------------------------------------

    if page_size == "letter":

        base_width, base_height = LETTER

    else:

        base_width, base_height = A4

    # -----------------------------------------------------
    # PDF NAME
    # -----------------------------------------------------

    pdf_name = (
        f"{uuid.uuid4().hex}.pdf"
    )

    pdf_path = os.path.join(
        UPLOAD_FOLDER,
        pdf_name
    )

    pdf = None

    # -----------------------------------------------------
    # PROCESS IMAGES
    # -----------------------------------------------------

    try:

        for file_index, file in enumerate(
            valid_files
        ):

            # ---------------------------------------------
            # OPEN IMAGE
            # ---------------------------------------------

            try:

                image = Image.open(
                    file.stream
                )

                image.verify()

                file.stream.seek(0)

                image = Image.open(
                    file.stream
                )

            except Exception:

                return (
                    f"{file.filename} is not a valid image.",
                    400
                )

            # ---------------------------------------------
            # RGB
            # ---------------------------------------------

            image = image.convert(
                "RGB"
            )

            # ---------------------------------------------
            # ROTATION
            # ---------------------------------------------

            rotation = 0

            if file_index < len(
                rotations
            ):

                try:

                    rotation = int(
                        rotations[
                            file_index
                        ]
                    )

                except Exception:

                    rotation = 0

            if rotation not in (
                0,
                90,
                180,
                270
            ):

                rotation = 0

            if rotation != 0:

                image = image.rotate(
                    rotation,
                    expand=True
                )

            # ---------------------------------------------
            # PAGE SIZE
            # ---------------------------------------------

            if page_size == "original":

                width_px, height_px = (
                    image.size
                )

                page_width = width_px
                page_height = height_px

            else:

                page_width = base_width
                page_height = base_height

                if orientation == "landscape":

                    page_width, page_height = (
                        max(
                            page_width,
                            page_height
                        ),
                        min(
                            page_width,
                            page_height
                        )
                    )

                else:

                    page_width, page_height = (
                        min(
                            page_width,
                            page_height
                        ),
                        max(
                            page_width,
                            page_height
                        )
                    )

            # ---------------------------------------------
            # CREATE PDF
            # ---------------------------------------------

            if pdf is None:

                pdf = canvas.Canvas(
                    pdf_path,
                    pagesize=(
                        page_width,
                        page_height
                    )
                )

            else:

                pdf.setPageSize(
                    (
                        page_width,
                        page_height
                    )
                )

            # ---------------------------------------------
            # TEMP JPG
            # ---------------------------------------------

            temp_name = (
                f"{uuid.uuid4().hex}.jpg"
            )

            temp_path = os.path.join(
                UPLOAD_FOLDER,
                temp_name
            )

            image.save(
                temp_path,
                "JPEG",
                quality=jpeg_quality,
                optimize=True
            )

            image.close()

            # ---------------------------------------------
            # OPEN TEMP IMAGE
            # ---------------------------------------------

            img = Image.open(
                temp_path
            )

            img_width, img_height = (
                img.size
            )

            # ---------------------------------------------
            # MARGIN
            # ---------------------------------------------

            margin = 30

            available_width = (
                page_width
                - (margin * 2)
            )

            available_height = (
                page_height
                - (margin * 2)
            )

            # ---------------------------------------------
            # SCALE
            # ---------------------------------------------

            scale = min(
                available_width / img_width,
                available_height / img_height
            )

            new_width = (
                img_width * scale
            )

            new_height = (
                img_height * scale
            )

            # ---------------------------------------------
            # CENTER
            # ---------------------------------------------

            x = (
                page_width
                - new_width
            ) / 2

            y = (
                page_height
                - new_height
            ) / 2

            # ---------------------------------------------
            # DRAW IMAGE
            # ---------------------------------------------

            pdf.drawImage(
                ImageReader(img),
                x,
                y,
                width=new_width,
                height=new_height,
                preserveAspectRatio=True
            )

            img.close()

            # ---------------------------------------------
            # PAGE NUMBER
            # ---------------------------------------------

            if page_numbers == "yes":

                pdf.setFont(
                    "Helvetica",
                    9
                )

                pdf.drawCentredString(
                    page_width / 2,
                    15,
                    str(
                        file_index + 1
                    )
                )

            # ---------------------------------------------
            # NEW PAGE
            # ---------------------------------------------

            pdf.showPage()

            # ---------------------------------------------
            # DELETE TEMP
            # ---------------------------------------------

            try:

                os.remove(
                    temp_path
                )

            except (
                PermissionError,
                OSError
            ):

                pass

        # -------------------------------------------------
        # SAVE PDF
        # -------------------------------------------------

        if pdf is not None:

            pdf.save()

        else:

            return (
                "Could not create PDF.",
                500
            )

    except Exception as error:

        print(
            "PDF ERROR:",
            error
        )

        if pdf is not None:

            try:

                pdf.save()

            except Exception:

                pass

        if os.path.exists(
            pdf_path
        ):

            try:

                os.remove(
                    pdf_path
                )

            except (
                PermissionError,
                OSError
            ):

                pass

        return (
            "Something went wrong while creating the PDF.",
            500
        )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    return {
        "success": True,
        "download_url":
            f"/download/{pdf_name}"
    }


# =========================================================
# DOWNLOAD JPG TO PDF
# =========================================================

@app.route(
    "/download/<filename>"
)
def download_pdf(filename):

    # Security

    if not filename.lower().endswith(
        ".pdf"
    ):

        return (
            "Invalid file.",
            400
        )

    safe_filename = os.path.basename(
        filename
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    # Check file

    if not os.path.isfile(
        file_path
    ):

        return (
            "File not found or expired.",
            404
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="jpg-to-pdf.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# PDF MERGER PAGE
# =========================================================

@app.route("/pdf-merger")
def pdf_merger():
    return render_template("pdf-merger.html")


# =========================================================
# MERGE PDF
# =========================================================

@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():

    files = request.files.getlist("pdfs")

    if not files:
        return {
            "error": "Please select at least one PDF."
        }, 400

    valid_files = []

    for file in files:

        if not file or not file.filename:
            continue

        if not file.filename.lower().endswith(".pdf"):
            return {
                "error": f"{file.filename} is not a PDF file."
            }, 400

        valid_files.append(file)

    if len(valid_files) < 2:
        return {
            "error": "Please select at least 2 PDF files."
        }, 400

    if len(valid_files) > 20:
        return {
            "error": "Maximum 20 PDF files are allowed."
        }, 400

    file_id = uuid.uuid4().hex

    output_name = f"{file_id}_merged.pdf"

    output_path = os.path.join(
        UPLOAD_FOLDER,
        output_name
    )

    temp_files = []

    try:

        writer = PdfWriter()

        # -------------------------------------------------
        # ADD PDF FILES IN UPLOAD ORDER
        # -------------------------------------------------

        for index, file in enumerate(valid_files):

            temp_name = (
                f"{file_id}_{index}.pdf"
            )

            temp_path = os.path.join(
                UPLOAD_FOLDER,
                temp_name
            )

            file.save(temp_path)

            temp_files.append(temp_path)

            writer.append(temp_path)

        # -------------------------------------------------
        # WRITE MERGED PDF
        # -------------------------------------------------

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        writer.close()

        return {
            "success": True,
            "files": len(valid_files),
            "download_url":
                f"/download-merged-pdf/{output_name}"
        }

    except Exception as error:

        print(
            "PDF MERGER ERROR:",
            error
        )

        if os.path.exists(output_path):

            try:
                os.remove(output_path)
            except OSError:
                pass

        return {
            "error": "Could not merge the PDF files.",
            "details": str(error)
        }, 500

    finally:

        # -------------------------------------------------
        # DELETE TEMP PDF FILES
        # -------------------------------------------------

        for temp_path in temp_files:

            if os.path.exists(temp_path):

                try:
                    os.remove(temp_path)
                except OSError:
                    pass


# =========================================================
# DOWNLOAD MERGED PDF
# =========================================================

@app.route("/download-merged-pdf/<filename>")
def download_merged_pdf(filename):

    safe_filename = os.path.basename(filename)

    if not safe_filename.endswith("_merged.pdf"):
        return "Invalid file.", 400

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    if not os.path.isfile(file_path):
        return "File not found or expired.", 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name="merged.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# ROBOTS.TXT
# =========================================================

@app.route("/robots.txt")
def robots():

    content = """User-agent: *
Allow: /

Sitemap: https://jpg-to-pdf-qefb.onrender.com/sitemap.xml
"""

    return Response(
        content,
        mimetype="text/plain"
    )


# =========================================================
# SITEMAP.XML
# =========================================================

@app.route("/sitemap.xml")
def sitemap():

    base_url = (
        "https://jpg-to-pdf-qefb.onrender.com"
    )

    pages = [

        "/",

        "/jpg-to-pdf",

        "/png-to-pdf",

        "/image-to-pdf",

        "/pdf-to-jpg",

        "/pdf-compressor",

        "/pdf-merger",

        "/about",

        "/contact",

        "/privacy",

        "/terms"

    ]

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
    )

    xml += (
        '<urlset '
        'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )

    for page in pages:

        xml += "  <url>\n"

        xml += (
            f"    <loc>{base_url}{page}</loc>\n"
        )

        xml += "  </url>\n"

    xml += "</urlset>"

    return Response(
        xml,
        mimetype="application/xml"
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return (
        "Upload is too large. "
        "Maximum total upload size is 50 MB.",
        413
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_size(bytes):
    """Helper function to format file size"""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes / (1024 * 1024):.2f} MB"


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )