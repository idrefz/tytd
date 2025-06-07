import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io
import tempfile
import numpy as np

st.set_page_config(page_title="Tanda Tangan Digital - Drag & Drop", layout="wide")
st.title("✍️ Aplikasi Tanda Tangan Digital - Versi Drag & Drop")

st.write("1. Upload PDF")
pdf_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

st.write("2. Upload atau Gambar Tanda Tangan")
signature_tab1, signature_tab2 = st.tabs(["✏️ Gambar Tanda Tangan", "📤 Upload Gambar Tanda Tangan"])
signature_image = None

with signature_tab1:
canvas_result = st_canvas(
    fill_color="rgba(0, 0, 0, 0)",
    stroke_width=0,
    stroke_color="#000000",
    background_image=np.array(img),
    update_streamlit=True,
    height=img.height,
    width=img.width,
    drawing_mode="transform",
    key="position_canvas",
)
    if canvas_result.image_data is not None:
        signature_image = Image.fromarray((canvas_result.image_data).astype("uint8"))

with signature_tab2:
    uploaded_signature = st.file_uploader("Upload tanda tangan (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_signature is not None:
        signature_image = Image.open(uploaded_signature)
        st.image(signature_image, caption="Preview Tanda Tangan", width=200)

if pdf_file and signature_image:
    pdf_bytes = pdf_file.read()
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_num = st.number_input("3. Pilih halaman tempat menaruh tanda tangan", 1, len(pdf_doc), 1)
    page = pdf_doc.load_page(page_num - 1)
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.write("4. Klik di posisi tanda tangan akan ditempel")

    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        stroke_width=0,
        stroke_color="#000000",
        background_image=img,
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="transform",
        key="position_canvas",
    )

    if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
        obj = canvas_result.json_data["objects"][-1]
        x, y = int(obj["left"]), int(obj["top"])
        st.success(f"Tanda tangan akan ditempel di posisi: x={x}, y={y}")

        if st.button("✅ Tempel & Unduh PDF Bertanda Tangan"):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                signature_image.save(tmpfile.name)
                sig_img = fitz.Pixmap(tmpfile.name)
                page.insert_image(
                    fitz.Rect(x, y, x + sig_img.width, y + sig_img.height),
                    pixmap=sig_img,
                    overlay=True,
                )
                os.unlink(tmpfile.name)

            # Simpan hasil
            output_buffer = io.BytesIO()
            pdf_doc.save(output_buffer)
            st.download_button(
                label="⬇️ Download PDF Bertanda Tangan",
                data=output_buffer.getvalue(),
                file_name="hasil_ttd.pdf",
                mime="application/pdf"
            )
