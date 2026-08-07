import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
import math
import os

st.set_page_config(
    page_title="DHE SISWA SMPN 1 SOREANG",
    page_icon="",
    layout="centered"
)

# ---------------------------------------------------------
# 1. KONFIGURASI LOKASI & WAKTU (SMPN 1 Soreang)
# ---------------------------------------------------------
# Koordinat SMPN 1 Soreang (Ciloa, Soreang, Bandung)
LAT_SEKOLAH = -6.9928500 
LON_SEKOLAH = 107.5143500 
RADIUS_TOLERANSI_METER = 150 # Jarak toleransi dari titik sekolah (meter)

# Batasan Waktu Absen
JAM_BUKA_ABSEN = time(6, 0)   # 06:00 WIB
JAM_BATAS_TEPAT = time(7, 15) # 07:15 WIB
JAM_BATAS_AKHIR = time(22, 0)  # 08:00 WIB

FILE_DATABASE_SISWA = "data_presensi_siswa.xlsx"
FILE_EXCEL_REKAP = "Rekap_Presensi_Siswa.xlsx"

# ---------------------------------------------------------
# 2. FUNGSI HITUNG JARAK (Haversine Formula)
# ---------------------------------------------------------
def hitung_jarak_meter(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius bumi dalam meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# ---------------------------------------------------------
# 3. INTERFACE APLIKASI
# ---------------------------------------------------------
st.title("DAFTAR HADIR SISWA SMPN 1 SOREANG")
st.caption("Sistem Absensi Online Berbasis GPS & Jam Masuk Sekolah")
st.markdown("---")

zona_wib = pytz.timezone('Asia/Jakarta')
waktu_sekarang = datetime.now(zona_wib)
jam_sekarang = waktu_sekarang.time()

st.info(f"🕒 **Waktu:** {waktu_sekarang.strftime('%H:%M:%S WIB')} | **Tanggal:** {waktu_sekarang.strftime('%d-%m-%Y')}")

# Cek Jadwal Absen
if jam_sekarang < JAM_BUKA_ABSEN:
    st.warning("⚠️ Presensi belum dibuka! Jam buka absen pukul 06:00 WIB.")
    st.stop()
elif jam_sekarang > JAM_BATAS_AKHIR:
    st.error("❌ Presensi telah ditutup untuk hari ini (Batas jam 08:00 WIB).")
    st.stop()

# Load Data Siswa dari Excel
if not os.path.exists(FILE_DATABASE_SISWA):
    st.error(f"❌ File `{FILE_DATABASE_SISWA}` tidak ditemukan di folder aplikasi!")
    st.stop()

df_siswa = pd.read_excel(FILE_DATABASE_SISWA, dtype=str)
# Normalisasi nama kolom menjadi uppercase & strip
df_siswa.columns = df_siswa.columns.str.strip().str.upper()

# Form Input Presensi
with st.form("form_login"):
    nisn_input = st.text_input("Masukkan NISN:", placeholder="Contoh: 1001").strip()
    password_input = st.text_input("Masukkan Password:", type="password").strip()
    
    html_gps = """
        <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError, {enableHighAccuracy: true});
            } else { 
                alert("Geolocation tidak didukung oleh browser Anda.");
            }
        }
        function showPosition(position) {
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                lat: position.coords.latitude,
                lon: position.coords.longitude
            }, "*");
            document.getElementById("gps_status").innerText = "✅ Lokasi Terdeteksi: Lat " + position.coords.latitude.toFixed(5) + ", Lon " + position.coords.longitude.toFixed(5);
        }
        function showError(error) {
            document.getElementById("gps_status").innerText = "❌ Gagal mengambil lokasi. Pastikan GPS/Location HP diaktifkan!";
        }
        </script>
        <button type="button" onclick="getLocation()" style="padding: 10px 15px; background-color: #1E3A8A; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
            📍 Deteksi Lokasi Saya (GPS)
        </button>
        <p id="gps_status" style="margin-top: 8px; color: #555; font-size: 14px;">Klik tombol di atas untuk menyambungkan GPS HP.</p>
    """
    st.components.v1.html(html_gps, height=120)
    
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat_user = st.number_input("Latitude", value=0.0, format="%.7f")
    with col_lon:
        lon_user = st.number_input("Longitude", value=0.0, format="%.7f")

    btn_presensi = st.form_submit_button("🚀 Kirim Presensi", type="primary")

# ---------------------------------------------------------
# 4. PROSES VALIDASI
# ---------------------------------------------------------
if btn_presensi:
    siswa_row = df_siswa[df_siswa['NISN'] == nisn_input]
    
    if siswa_row.empty:
        st.error("❌ NISN tidak terdaftar dalam database sekolah!")
    else:
        pass_db = str(siswa_row.iloc[0]['PASSWORD']).strip()
        nama_siswa = str(siswa_row.iloc[0]['NAMA']).strip()
        kelas_siswa = str(siswa_row.iloc[0]['KELAS']).strip()
        
        if pass_db != password_input:
            st.error("❌ Password salah!")
        elif lat_user == 0.0 or lon_user == 0.0:
            st.error("⚠️ Lokasi GPS belum dideteksi. Klik tombol 'Deteksi Lokasi Saya (GPS)' di atas!")
        else:
            jarak = hitung_jarak_meter(lat_user, lon_user, LAT_SEKOLAH, LON_SEKOLAH)
            
            if jarak > RADIUS_TOLERANSI_METER:
                st.error(f"❌ Posisi Anda di luar area sekolah! (Jarak: **{int(jarak)} meter**, Toleransi Maksimal: {RADIUS_TOLERANSI_METER} meter).")
            else:
                status_kehadiran = "Hadir Tepat Waktu" if jam_sekarang <= JAM_BATAS_TEPAT else "Terlambat"
                
                # Simpan Rekap
                data_baru = pd.DataFrame([{
                    "TANGGAL": waktu_sekarang.strftime("%Y-%m-%d"),
                    "JAM": waktu_sekarang.strftime("%H:%M:%S"),
                    "NISN": nisn_input,
                    "NAMA": nama_siswa,
                    "KELAS": kelas_siswa,
                    "STATUS": status_kehadiran,
                    "JARAK_METER": round(jarak, 1),
                    "LATITUDE": lat_user,
                    "LONGITUDE": lon_user
                }])

                if os.path.exists(FILE_EXCEL_REKAP):
                    df_lama = pd.read_excel(FILE_EXCEL_REKAP, dtype=str)
                    df_gabung = pd.concat([df_lama, data_baru], ignore_index=True)
                    df_gabung.to_excel(FILE_EXCEL_REKAP, index=False)
                else:
                    data_baru.to_excel(FILE_EXCEL_REKAP, index=False)

                st.balloons()
                st.success(f"🎉 Presensi Berhasil! Status: **{status_kehadiran}**")
                st.info(f"👤 Selamat Belajar, **{nama_siswa}** ({kelas_siswa})!")
