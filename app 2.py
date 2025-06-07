
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
import tempfile
import numpy as np

st.title("TTD Digital di PDF dengan Drag & Drop Posisi")

# Upload PDF
pdf_file = st.file_uploader("Upload file PDF", type=["pdf"])

if pdf_file is not None:
    # Load PDF
    pdf_in = fitz.open(stream=pdf_file.read(), filetype="pdf")
    num_pages = pdf_in.page_count

    # Pilih halaman
    page_number = st.number_input("Pilih halaman untuk tanda tangan:", min_value=1, max_value=num_pages, value=num_pages)

    # Render halaman jadi gambar (preview)
    page = pdf_in.load_page(page_number - 1)
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.image(img, caption=f"Preview halaman {page_number}")

    # Sekarang aman untuk gunakan `img`
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="#000000",
        background_image=img,
        height=img.height,
        width=img.width,
        drawing_mode="freedraw",
        key="canvas"
    )


if canvas_result.image_data is not None:

        # Simpan tanda tangan sebagai image hitam putih (tanpa background)
        img_data = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
        # Crop tanda tangan dari layer canvas (misalnya ambil area dengan warna hitam)
        # Untuk simplifikasi, langsung pakai hasil canvas
        sign_img = img_data.convert("L").point(lambda x: 0 if x < 200 else 255, '1').convert("RGB")

        if st.button("Tambahkan Tanda Tangan ke PDF"):
            # Konversi tanda tangan ke bytes PNG
            img_byte_arr = BytesIO()
            sign_img.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            # Sisipkan tanda tangan ke halaman yang dipilih
            # Tentukan posisi berdasarkan canvas (anggap full canvas = full page)
            # Cari bounding box tanda tangan dari canvas_result.image_data

            arr = canvas_result.image_data[..., 3]  # ambil alpha channel
            coords = np.argwhere(arr > 10)  # piksel tidak transparan

            if coords.size == 0:
                st.error("Tanda tangan kosong, gambar dulu ya.")
            else:
                top_left = coords.min(axis=0)
                bottom_right = coords.max(axis=0)

                # Skala posisi canvas ke ukuran page PDF (point)
                page = pdf_in.load_page(page_number - 1)
                rect = page.rect

                # Canvas ukuran:
                canvas_w, canvas_h = canvas_result.width, canvas_result.height
                # Posisi di canvas
                x0_canvas, y0_canvas = top_left[1], top_left[0]
                x1_canvas, y1_canvas = bottom_right[1], bottom_right[0]

                # Posisi di PDF (proportional)
                x0_pdf = rect.width * (x0_canvas / canvas_w)
                y0_pdf = rect.height * (y0_canvas / canvas_h)
                x1_pdf = rect.width * (x1_canvas / canvas_w)
                y1_pdf = rect.height * (y1_canvas / canvas_h)

                # Sisipkan gambar tanda tangan ke PDF
                page.insert_image(fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf), stream=img_byte_arr)

                # Simpan PDF ke bytes buffer
                pdf_bytes = pdf_in.write()
                pdf_in.close()

                # Tombol download
                st.download_button(
                    label="Download PDF dengan Tanda Tangan",
                    data=pdf_bytes,
                    file_name="ttd_output.pdf",
                    mime="application/pdf"
                )
