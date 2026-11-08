import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard E-Commerce Olist", layout="wide")

AKSEN = "#1F6F78"
ABU = "#CFCFC8"
ABU_TUA = "#B8B8B2"
TEKS = "#2B2B2B"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8A8A85",
    "axes.labelcolor": TEKS, "text.color": TEKS, "xtick.color": TEKS, "ytick.color": TEKS,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "figure.facecolor": "none", "axes.facecolor": "none",
})


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path, parse_dates=["order_purchase_timestamp"])
    df["bulan"] = df.order_purchase_timestamp.dt.to_period("M").dt.to_timestamp()
    return df


def hitung_rfm(df):
    acuan = df.order_purchase_timestamp.max().normalize() + pd.Timedelta(days=1)
    rfm = df.groupby("customer_unique_id").agg(
        last_purchase=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum"),
    ).reset_index()
    rfm["recency"] = (acuan - rfm.last_purchase).dt.days
    # rank(method="first") menghindari error qcut jika banyak nilai kembar pada rentang data yang kecil
    rfm["r_score"] = pd.qcut(rfm.recency.rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["m_score"] = pd.qcut(rfm.monetary.rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)

    def segmen(r):
        if r.frequency >= 2:
            return "Pelanggan berulang"
        if r.m_score == 4 and r.r_score >= 3:
            return "Bernilai tinggi, masih aktif"
        if r.m_score == 4:
            return "Bernilai tinggi, mulai pasif"
        if r.r_score >= 3:
            return "Baru, belanja kecil-menengah"
        return "Pasif, belanja kecil-menengah"

    rfm["segmen"] = rfm.apply(segmen, axis=1)
    return rfm


data = load_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Filter")
tgl_min = data.order_purchase_timestamp.min().date()
tgl_max = data.order_purchase_timestamp.max().date()
rentang = st.sidebar.date_input("Rentang tanggal order", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max)
semua_state = sorted(data.customer_state.unique())
state_pilih = st.sidebar.multiselect("State pelanggan", semua_state, default=[], placeholder="Semua state")
st.sidebar.caption("Kosongkan state untuk menampilkan semua state. Data: order berstatus delivered.")

if not (isinstance(rentang, (tuple, list)) and len(rentang) == 2):
    st.info("Pilih tanggal akhir pada filter di sebelah kiri untuk melanjutkan.")
    st.stop()

mulai, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]) + pd.Timedelta(days=1)
df = data[(data.order_purchase_timestamp >= mulai) & (data.order_purchase_timestamp < akhir)]
if state_pilih:
    df = df[df.customer_state.isin(state_pilih)]

st.title("Dashboard E-Commerce Olist")
st.caption("Order terkirim September 2016 sampai Agustus 2018. Pendapatan dihitung dari harga barang (BRL), tanpa ongkos kirim.")

if df.empty:
    st.warning("Tidak ada data untuk filter ini. Ubah rentang tanggal atau state.")
    st.stop()

# ---------------------------------------------------------------- ringkasan
total_order = df.order_id.nunique()
total_pendapatan = df.price.sum()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Jumlah order", f"{total_order:,}")
k2.metric("Total pendapatan", f"{total_pendapatan / 1e6:,.2f} juta BRL")
k3.metric("Nilai rata-rata per order", f"{total_pendapatan / total_order:,.1f} BRL")
k4.metric("Pelanggan unik", f"{df.customer_unique_id.nunique():,}")

tab1, tab2, tab3 = st.tabs(["Order, pendapatan, dan kategori", "Review dan pengiriman", "Segmen pelanggan (RFM)"])

# ---------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Tren order dan pendapatan per bulan")
    bulanan = df.groupby("bulan").agg(order=("order_id", "nunique"), pendapatan=("price", "sum")).reset_index()
    c1, c2 = st.columns(2)
    for kolom, judul, skala, wadah in [("order", "Jumlah order", 1, c1), ("pendapatan", "Pendapatan (ribu BRL)", 1000, c2)]:
        fig, ax = plt.subplots(figsize=(6, 3.4))
        ax.plot(bulanan.bulan, bulanan[kolom] / skala, color=AKSEN, lw=2.6, marker="o", ms=4)
        ax.set_title(judul)
        ax.set_ylim(0)
        ax.yaxis.grid(True, color="#E0DCD2", lw=0.8)
        ax.set_axisbelow(True)
        fig.autofmt_xdate()
        wadah.pyplot(fig)
        plt.close(fig)

    st.subheader("Kategori dengan pendapatan terbesar")
    n_kat = st.slider("Jumlah kategori yang ditampilkan", 5, 15, 10)
    kat = (df.groupby("product_category_name_english").price.sum().sort_values(ascending=False).head(n_kat).iloc[::-1])
    persen = kat / df.price.sum() * 100
    warna = [AKSEN if i >= len(kat) - 3 else ABU for i in range(len(kat))]
    fig, ax = plt.subplots(figsize=(9, 0.42 * n_kat + 1.2))
    ax.barh(kat.index, kat.values / 1000, color=warna, height=0.72)
    for i, (v, p) in enumerate(zip(kat.values / 1000, persen.values)):
        ax.text(v + kat.max() / 1000 * 0.01, i, f"{v:,.0f} rb ({p:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, kat.max() / 1000 * 1.25)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_title("Pendapatan per kategori (ribu BRL, tiga teratas diberi warna)")
    st.pyplot(fig)
    plt.close(fig)

# ---------------------------------------------------------------- tab 2
with tab2:
    order_df = df.drop_duplicates("order_id").dropna(subset=["review_score"]).copy()
    order_df["terlambat"] = order_df.delay_days > 0
    if order_df.empty:
        st.warning("Tidak ada review pada filter ini.")
    else:
        m1, m2 = st.columns(2)
        m1.metric("Rata-rata review score", f"{order_df.review_score.mean():.2f}")
        m2.metric("Order terlambat", f"{order_df.terlambat.mean() * 100:.1f}%")

        st.subheader("Review score per state")
        min_order = st.slider("Minimal jumlah order per state (agar rata-rata stabil)", 10, 300, 100, step=10)
        st_df = order_df.groupby("customer_state").agg(rata2=("review_score", "mean"), n=("order_id", "count"))
        st_df = st_df[st_df.n >= min_order].sort_values("rata2", ascending=False)
        if st_df.empty:
            st.info("Tidak ada state yang memenuhi jumlah minimal order. Turunkan batas minimalnya.")
        else:
            warna = [AKSEN if i >= len(st_df) - 5 else ABU for i in range(len(st_df))]
            fig, ax = plt.subplots(figsize=(10, 3.9))
            ax.bar(st_df.index, st_df.rata2, color=warna, width=0.72)
            for i, v in enumerate(st_df.rata2):
                ax.text(i, v + 0.015, f"{v:.2f}", ha="center", fontsize=8)
            ax.axhline(order_df.review_score.mean(), color=TEKS, ls="--", lw=1)
            ax.set_ylim(3.0, 4.6)
            ax.set_ylabel("Rata-rata review (sumbu mulai 3,0)")
            ax.set_title("Lima state terendah diberi warna, garis putus-putus = rata-rata keseluruhan")
            ax.yaxis.grid(True, color="#E0DCD2", lw=0.8)
            ax.set_axisbelow(True)
            st.pyplot(fig)
            plt.close(fig)

        st.subheader("Review score berdasarkan keterlambatan")
        order_df["kelompok"] = pd.cut(order_df.delay_days, [-np.inf, 0, 3, 7, np.inf],
                                      labels=["Tepat waktu", "Telat 1-3 hari", "Telat 4-7 hari", "Telat > 7 hari"])
        tel = order_df.groupby("kelompok", observed=True).agg(rata2=("review_score", "mean"), n=("order_id", "count"))
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.bar(tel.index.astype(str), tel.rata2, color=[ABU] + [AKSEN] * (len(tel) - 1), width=0.62)
        for i, (v, n) in enumerate(zip(tel.rata2, tel.n)):
            ax.text(i, v + 0.07, f"{v:.2f}", ha="center", fontweight="bold")
            ax.text(i, 0.12, f"n = {n:,}", ha="center", fontsize=8.5)
        ax.set_ylim(0, 5)
        ax.set_ylabel("Rata-rata review score")
        ax.yaxis.grid(True, color="#E0DCD2", lw=0.8)
        ax.set_axisbelow(True)
        st.pyplot(fig)
        plt.close(fig)

# ---------------------------------------------------------------- tab 3
with tab3:
    if df.customer_unique_id.nunique() < 8:
        st.warning("Data terlalu sedikit untuk membuat segmen. Perluas filter.")
    else:
        rfm = hitung_rfm(df)
        urutan = ["Bernilai tinggi, mulai pasif", "Bernilai tinggi, masih aktif", "Baru, belanja kecil-menengah",
                  "Pasif, belanja kecil-menengah", "Pelanggan berulang"]
        seg = rfm.groupby("segmen").agg(pelanggan=("customer_unique_id", "count"), pendapatan=("monetary", "sum"),
                                        rata2=("monetary", "mean"), recency=("recency", "mean")).reindex(urutan).dropna()
        seg["p_pelanggan"] = seg.pelanggan / seg.pelanggan.sum() * 100
        seg["p_pendapatan"] = seg.pendapatan / seg.pendapatan.sum() * 100

        tinggi = rfm[rfm.segmen.str.startswith("Bernilai tinggi")]
        a1, a2, a3 = st.columns(3)
        a1.metric("Pelanggan bernilai tinggi", f"{len(tinggi) / len(rfm) * 100:.1f}% pelanggan")
        a2.metric("Kontribusi pendapatan", f"{tinggi.monetary.sum() / rfm.monetary.sum() * 100:.1f}%")
        a3.metric("Pelanggan sekali beli", f"{(rfm.frequency == 1).mean() * 100:.1f}%")

        st.subheader("Porsi pelanggan dan porsi pendapatan tiap segmen")
        p = seg.iloc[::-1]
        y = np.arange(len(p))
        h = 0.38
        fig, ax = plt.subplots(figsize=(9.5, 4))
        ax.barh(y + h / 2, p.p_pelanggan, height=h, color=ABU, label="% pelanggan")
        ax.barh(y - h / 2, p.p_pendapatan, height=h, color=AKSEN, label="% pendapatan")
        for i, (a, b) in enumerate(zip(p.p_pelanggan, p.p_pendapatan)):
            ax.text(a + 0.5, i + h / 2, f"{a:.1f}%", va="center", fontsize=9)
            ax.text(b + 0.5, i - h / 2, f"{b:.1f}%", va="center", fontsize=9, fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels(p.index)
        ax.legend(frameon=False, loc="lower right")
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.set_xlim(0, max(p.p_pelanggan.max(), p.p_pendapatan.max()) * 1.15)
        st.pyplot(fig)
        plt.close(fig)

        with st.expander("Lihat tabel segmen"):
            tabel = seg.rename(columns={"pelanggan": "Jumlah pelanggan", "pendapatan": "Total pendapatan (BRL)",
                                        "rata2": "Rata-rata belanja (BRL)", "recency": "Rata-rata recency (hari)",
                                        "p_pelanggan": "% pelanggan", "p_pendapatan": "% pendapatan"})
            st.dataframe(tabel.round(1), width="stretch")

        st.subheader("Sebaran pelanggan bernilai tinggi")
        lokasi = (df.sort_values("order_purchase_timestamp").drop_duplicates("customer_unique_id", keep="last")
                  [["customer_unique_id", "customer_state", "customer_lat", "customer_lng"]])
        geo = tinggi.merge(lokasi, on="customer_unique_id", how="left")
        geo_ok = geo.dropna(subset=["customer_lat"])
        g1, g2 = st.columns([1.5, 1])
        fig, ax = plt.subplots(figsize=(6.5, 6))
        lain = rfm.merge(lokasi, on="customer_unique_id").dropna(subset=["customer_lat"])
        lain = lain[~lain.segmen.str.startswith("Bernilai tinggi")]
        ax.scatter(lain.customer_lng, lain.customer_lat, s=3, color="#D9D9D3", alpha=0.35, linewidths=0)
        ax.scatter(geo_ok.customer_lng, geo_ok.customer_lat, s=4, color=AKSEN, alpha=0.35, linewidths=0)
        ax.set_aspect("equal")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Titik hijau-biru = pelanggan bernilai tinggi")
        g1.pyplot(fig)
        plt.close(fig)

        top = geo.customer_state.value_counts().head(5).iloc[::-1]
        fig, ax = plt.subplots(figsize=(4.5, 3.6))
        ax.barh(top.index, top.values, color=[AKSEN if i == len(top) - 1 else ABU for i in range(len(top))], height=0.65)
        for i, v in enumerate(top.values):
            ax.text(v + top.max() * 0.02, i, f"{v:,} ({v / len(geo) * 100:.0f}%)", va="center", fontsize=9)
        ax.set_xlim(0, top.max() * 1.45)
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.set_title("5 state teratas")
        g2.pyplot(fig)
        plt.close(fig)
