
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask, render_template, request,
    send_from_directory, abort
)
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

from crypto import generate_shares, reconstruct_secret

app = Flask(__name__)

RESULTS = Path("results").resolve()
RESULTS.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_upload(file):
    if not file or not file.filename:
        raise ValueError("Please select an image.")

    if not allowed_file(secure_filename(file.filename)):
        raise ValueError("Only PNG, JPG, and JPEG are allowed.")

    path = RESULTS / f"{uuid4().hex}.png"

    try:
        image = Image.open(file.stream)
        image.verify()

        file.stream.seek(0)
        image = Image.open(file.stream).convert("RGB")
        image.save(path, format="PNG")
    except (UnidentifiedImageError, OSError, ValueError):
        path.unlink(missing_ok=True)
        raise ValueError("The uploaded file is not a valid image.")

    return path


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/generate")
def generate():
    try:
        source = save_upload(request.files.get("image"))
        share1 = RESULTS / f"{uuid4().hex}.png"
        share2 = RESULTS / f"{uuid4().hex}.png"

        generate_shares(source, share1, share2)

        # Remove the uploaded secret after processing
        source.unlink(missing_ok=True)

        return render_template(
            "index.html",
            share1=share1.name,
            share2=share2.name,
            message="Shares generated successfully."
        )
    except ValueError as error:
        return render_template(
            "index.html", error=str(error)
        ), 400


@app.post("/reconstruct")
def reconstruct():
    try:
        first = save_upload(request.files.get("share1"))
        second = save_upload(request.files.get("share2"))

        output = RESULTS / f"{uuid4().hex}.png"

        try:
            reconstruct_secret(first, second, output)
        finally:
            first.unlink(missing_ok=True)
            second.unlink(missing_ok=True)

        return render_template(
            "index.html",
            reconstructed=output.name,
            message="Reconstruction completed."
        )
    except ValueError as error:
        return render_template(
            "index.html", error=str(error)
        ), 400


@app.get("/results/<filename>")
def download_result(filename):
    # Never allow arbitrary paths or filenames
    if not filename.endswith(".png") or Path(filename).name != filename:
        abort(404)

    return send_from_directory(
        RESULTS, filename, as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
