# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Submission kelas "Belajar Fundamental Analisis Data" (Dicoding).

- **Nama:** Awalin Nisa'Ul Mufidah
- **Email:** DS466B6X0293@student.devacademy.id
- **ID Dicoding:** DS466B6X0293

## Pertanyaan bisnis

1. Bagaimana perbandingan order dan pendapatan per bulan pada Jan-Agu 2017 vs Jan-Agu 2018, dan kategori produk apa yang menyumbang pendapatan terbesar pada Jan-Agu 2018?
2. State mana yang punya rata-rata review score terendah pada Jan-Agu 2018, dan seberapa besar pengaruh keterlambatan pengiriman terhadap review?
3. Segmen pelanggan (RFM) mana yang menyumbang pendapatan terbesar, dan di wilayah mana pelanggan bernilai tinggi terkonsentrasi?

## Struktur folder

```
submission
├── dashboard
│   ├── dashboard.py
│   └── main_data.csv
├── data
│   └── (sembilan berkas CSV dataset)
├── .streamlit
│   └── config.toml
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

`data/geolocation_ringkas.csv` adalah tabel geolocation asli yang diringkas menjadi satu titik rata-rata per kode pos (ukuran asli sekitar 59 MB). Cara meringkasnya ada di bagian Gathering Data pada notebook.

## Menjalankan notebook

1. Install dependensi: `pip install -r requirements.txt` dan `pip install jupyter seaborn`
2. Buka `notebook.ipynb` dari folder `submission` (path data bersifat relatif), lalu jalankan semua cell. Cell terakhir menghasilkan `dashboard/main_data.csv`.

## Menjalankan dashboard secara lokal

Dari folder `submission`:

```
pip install -r requirements.txt
streamlit run dashboard/dashboard.py
```

Dashboard terbuka di http://localhost:8501 dan memiliki filter rentang tanggal dan state, serta tiga tab: order dan kategori, review dan pengiriman, serta segmen pelanggan RFM.

## Deploy ke Streamlit Community Cloud

1. Unggah folder submission ke repository GitHub.
2. Di share.streamlit.io pilih repository tersebut, isi **Main file path** dengan `dashboard/dashboard.py`.
3. Salin tautan aplikasi ke `url.txt`.
