import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io
import tempfile

st.set_page_config(page_title="Tanda Tangan Digital", layout="wide")

st.title("✍️ Aplikasi Tanda Tangan Digital")
st.write("Upload PDF dan tambahkan tanda tangan dengan menggambar atau mengunggah gambar.")

pdf_file = st.file_uploader("📄 Upload file PDF", type=["pdf"])
tab1, tab2 = st.tabs(["✏️ Gambar Tanda Tangan", "📤 Upload Gambar Tanda Tangan"])

signature_image = None

with tab1:
    st.write("Gambar tanda tangan di bawah ini:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#fff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )
    if canvas_result.image_data is not None:
        signature_image = Image.fromarray((canvas_result.image_data).astype("uint8"))

with tab2:
    uploaded_signature = st.file_uploader("Upload gambar tanda tangan (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_signature is not None:
        signature_image = Image.open(uploaded_signature)
        st.image(signature_image, caption="Preview Tanda Tangan", width=200)

if pdf_file is not None and signature_image is not None:
    st.success("PDF dan Tanda Tangan siap digunakan.")

    # Load PDF dan render halaman
    pdf_bytes = pdf_file.read()
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_num = st.number_input("Pilih halaman untuk menaruh tanda tangan", 1, len(pdf_doc), 1)
    page = pdf_doc.load_page(page_num - 1)
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.image(img, caption=f"Halaman {page_num}")

    st.write("🔽 Tentukan posisi tanda tangan (koordinat relatif)")
    col1, col2 = st.columns(2)
    with col1:
        x = st.slider("Posisi X", 0, pix.width, int(pix.width * 0.5))
    with col2:
        y = st.slider("Posisi Y", 0, pix.height, int(pix.height * 0.5))

    # Simpan PDF baru jika tombol ditekan
    if st.button("✅ Tempel & Unduh PDF Bertanda Tangan"):
        # Convert tanda tangan ke format PNG dengan latar belakang transparan
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
            file_name="pdf_bertanda_tangan.pdf",
            mime="application/pdf"
        )