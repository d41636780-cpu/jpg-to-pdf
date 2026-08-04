import os
import uuid
import json
import time

from flask import (
    Flask,
    render_template,
    request,
    send_file
)

from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4, LETTER


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

UPLOAD_FOLDER = "uploads"

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
# CREATE UPLOAD FOLDER
# =========================================================

os.makedirs(
    UPLOAD_FOLDER,
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

    try:

        filenames = os.listdir(
            UPLOAD_FOLDER
        )

    except OSError:
        return


    for filename in filenames:

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        try:

            if not os.path.isfile(
                file_path
            ):
                continue


            file_age = (
                current_time
                - os.path.getmtime(
                    file_path
                )
            )


            if file_age > FILE_LIFETIME:

                os.remove(
                    file_path
                )

        except (
            PermissionError,
            OSError
        ):

            # File may still be in use.
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
# CONVERT JPG TO PDF
# =========================================================

@app.route(
    "/convert",
    methods=["POST"]
)
def convert():

    cleanup_old_files()


    # =====================================================
    # GET SETTINGS
    # =====================================================

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


    # =====================================================
    # GET ROTATIONS
    # =====================================================

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


    # =====================================================
    # GET UPLOADED FILES
    # =====================================================

    files = request.files.getlist(
        "images"
    )


    # =====================================================
    # FILE COUNT
    # =====================================================

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


    # =====================================================
    # VALIDATE FILES
    # =====================================================

    valid_files = []

    total_size = 0


    for file in files:

        if not file:
            continue


        if not file.filename:
            continue


        # -------------------------------------------------
        # EXTENSION
        # -------------------------------------------------

        if not allowed_file(
            file.filename
        ):

            return (
                "Invalid file type. "
                "Only JPG, JPEG, PNG and WebP are allowed.",
                400
            )


        # -------------------------------------------------
        # FILE SIZE
        # -------------------------------------------------

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


    # =====================================================
    # TOTAL SIZE
    # =====================================================

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


    # =====================================================
    # QUALITY
    # =====================================================

    if quality == "high":

        jpeg_quality = 95

    elif quality == "medium":

        jpeg_quality = 75

    else:

        jpeg_quality = 50


    # =====================================================
    # PAGE SIZE
    # =====================================================

    if page_size == "letter":

        base_width, base_height = LETTER

    else:

        base_width, base_height = A4


    # =====================================================
    # CREATE PDF NAME
    # =====================================================

    pdf_name = (
        f"{uuid.uuid4().hex}.pdf"
    )


    pdf_path = os.path.join(
        UPLOAD_FOLDER,
        pdf_name
    )


    pdf = None


    # =====================================================
    # PROCESS ALL IMAGES
    # =====================================================

    try:

        for file_index, file in enumerate(
            valid_files
        ):

            # =============================================
            # OPEN IMAGE
            # =============================================

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


            # =============================================
            # CONVERT TO RGB
            # =============================================

            image = image.convert(
                "RGB"
            )


            # =============================================
            # ROTATION
            # =============================================

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


            # =============================================
            # PAGE SIZE
            # =============================================

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


            # =============================================
            # CREATE PDF
            # =============================================

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


            # =============================================
            # TEMP JPG
            # =============================================

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


            # =============================================
            # OPEN TEMP IMAGE
            # =============================================

            img = Image.open(
                temp_path
            )


            img_width, img_height = (
                img.size
            )


            # =============================================
            # MARGIN
            # =============================================

            margin = 30


            available_width = (
                page_width
                - (margin * 2)
            )


            available_height = (
                page_height
                - (margin * 2)
            )


            # =============================================
            # SCALE IMAGE
            # =============================================

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


            # =============================================
            # CENTER IMAGE
            # =============================================

            x = (
                page_width
                - new_width
            ) / 2


            y = (
                page_height
                - new_height
            ) / 2


            # =============================================
            # DRAW IMAGE
            # =============================================

            pdf.drawImage(
                ImageReader(img),
                x,
                y,
                width=new_width,
                height=new_height,
                preserveAspectRatio=True
            )


            img.close()


            # =============================================
            # PAGE NUMBER
            # =============================================

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


            # =============================================
            # NEW PAGE
            # =============================================

            pdf.showPage()


            # =============================================
            # DELETE TEMP FILE
            # =============================================

            try:

                os.remove(
                    temp_path
                )

            except (
                PermissionError,
                OSError
            ):

                pass


        # =================================================
        # SAVE PDF
        # =================================================

        if pdf is not None:

            pdf.save()

        else:

            return (
                "Could not create PDF.",
                500
            )


    # =====================================================
    # PDF CREATION ERROR
    # =====================================================

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


    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return {
        "success": True,
        "download_url":
            f"/download/{pdf_name}"
    }


# =========================================================
# DOWNLOAD PDF
# =========================================================

@app.route(
    "/download/<filename>"
)
def download_pdf(filename):

    # -----------------------------------------------------
    # BASIC SECURITY CHECK
    # -----------------------------------------------------

    if not filename.endswith(
        ".pdf"
    ):

        return (
            "Invalid file.",
            400
        )


    # Prevent path traversal
    safe_filename = os.path.basename(
        filename
    )


    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )


    # -----------------------------------------------------
    # CHECK FILE
    # -----------------------------------------------------

    if not os.path.isfile(
        file_path
    ):

        return (
            "File not found or expired.",
            404
        )


    # -----------------------------------------------------
    # SEND PDF
    # -----------------------------------------------------

    return send_file(
        file_path,
        as_attachment=True,
        download_name="jpg-to-pdf.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )

