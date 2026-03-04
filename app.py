import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard PENA", layout="wide")
st.title("📊 Dashboard Analisis Performance PENA")
st.markdown("Aplikasi pemantauan performa pengiriman dan penerimaan file posting.")

# --- SIDEBAR: UPLOAD FILE & FILTER ---
st.sidebar.header("1. Upload Dataset")
file_sent = st.sidebar.file_uploader("Upload app_ftp_file_sent.csv", type=['csv'])
file_receive = st.sidebar.file_uploader("Upload app_ftp_file_receive.csv", type=['csv'])

if file_sent and file_receive:
    # --- TOMBOL PROSES & LOAD DATA ---
    proses_btn = st.sidebar.button("Proses & Validasi Data")
    
    if proses_btn:
        with st.spinner("Memuat data & melakukan validasi..."):
            try:
                # Baca data sementara
                df_sent_temp = pd.read_csv(file_sent, low_memory=False)
                df_receive_temp = pd.read_csv(file_receive, low_memory=False)
                
                # Validasi Karakter Pertama (Sent = I, Receive = O)
                cek_sent = str(df_sent_temp['file_name'].iloc[0])[0].upper()
                cek_recv = str(df_receive_temp['file_name'].iloc[0])[0].upper()
                
                if cek_sent != 'I' or cek_recv != 'O':
                    st.sidebar.error("❌ Validasi Gagal: Pastikan file Sent (I) dan Receive (O) tidak tertukar.")
                    st.stop()
                else:
                    # Konversi waktu dan penyesuaian zona waktu WIB (+7 Jam)
                    df_sent_temp['created_at'] = pd.to_datetime(df_sent_temp['created_at']) 
                    df_receive_temp['created_at'] = pd.to_datetime(df_receive_temp['created_at'])
                    
                    # Simpan ke Session State agar data menetap di memori
                    st.session_state['df_sent'] = df_sent_temp
                    st.session_state['df_receive'] = df_receive_temp
                    st.session_state['data_valid'] = True
                    st.sidebar.success("✅ Data berhasil dimuat!")
            except Exception as e:
                st.sidebar.error(f"❌ Terjadi kesalahan: {e}")
                st.stop()

    # --- PROTEKSI DATA (Hanya tampilkan dashboard jika data sudah valid) ---
    if st.session_state.get('data_valid', False):
        # Ambil data dari memory session_state
        df_sent = st.session_state['df_sent']
        df_receive = st.session_state['df_receive']

        # --- FILTER TANGGAL ---
        st.sidebar.header("2. Filter Data")
        available_days = list(range(1, 32))
        selected_day = st.sidebar.selectbox("Pilih Tanggal (Hari):", available_days, index=26)

        # Filter dataset berdasarkan tanggal
        df_sent_filter = df_sent[df_sent['created_at'].dt.day == selected_day].copy()
        df_receive_filter = df_receive[df_receive['created_at'].dt.day == selected_day].copy()

        # --- BAGIAN 1: RINGKASAN DATA ---
        st.header(f"Ringkasan Data (Tanggal {selected_day})")
        col1, col2 = st.columns(2)
        col1.metric("Total Data Sent", f"{len(df_sent_filter):,} Baris")
        col2.metric("Total Data Receive", f"{len(df_receive_filter):,} Baris")
        st.markdown("---")

        # --- BAGIAN 2: GRAFIK BOTTLENECK ---
        st.header("📈 Analisis Kecepatan & Distribusi File Sent")
        
        if not df_sent_filter.empty:
            df_sent_filter = df_sent_filter.sort_values('created_at')
            df_sent_filter['hour'] = df_sent_filter['created_at'].dt.hour
            df_sent_filter['cumulative_count'] = range(1, len(df_sent_filter) + 1)

            fig, ax = plt.subplots(2, 1, figsize=(12, 10))

            # Grafik 1: Distribusi per Jam
            hourly_counts = df_sent_filter.groupby('hour').size()
            ax[0].bar(hourly_counts.index, hourly_counts.values, color='skyblue', edgecolor='navy')
            ax[0].set_title(f'Distribusi Jumlah Data Masuk per Jam', fontsize=14, fontweight='bold')
            ax[0].set_xlabel('Jam Ke-')
            ax[0].set_ylabel('Jumlah Records')
            
            if not hourly_counts.empty:
                ax[0].set_xticks(range(int(min(hourly_counts.index)), int(max(hourly_counts.index)) + 1)) 
            
            for i, v in enumerate(hourly_counts):
                ax[0].text(hourly_counts.index[i], v + 100, str(v), ha='center', fontweight='bold')

            # Grafik 2: Progress Kumulatif
            ax[1].plot(df_sent_filter['created_at'], df_sent_filter['cumulative_count'], color='red', linewidth=2)
            ax[1].set_title('Progress Kumulatif (Garis Mendatar = Sistem Idle)', fontsize=14, fontweight='bold')
            ax[1].set_xlabel('Waktu')
            ax[1].set_ylabel('Total Data Terproses')
            ax[1].grid(True, linestyle=':', alpha=0.6)
            
            zona_wib = pytz.timezone('Asia/Jakarta')
            ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=zona_wib))

            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning(f"⚠️ Tidak ada data untuk tanggal {selected_day}.")

        st.markdown("---")


         # --- BAGIAN 2: GRAFIK BOTTLENECK ---
        st.header("📈 Analisis Kecepatan & Distribusi File Receive")
        
        if not df_receive_filter.empty:
            df_receive_filter = df_receive_filter.sort_values('created_at')
            df_receive_filter['hour'] = df_receive_filter['created_at'].dt.hour
            df_receive_filter['cumulative_count'] = range(1, len(df_receive_filter) + 1)

            fig, ax = plt.subplots(2, 1, figsize=(12, 10))

            # Grafik 1: Distribusi per Jam
            hourly_counts = df_receive_filter.groupby('hour').size()
            ax[0].bar(hourly_counts.index, hourly_counts.values, color='skyblue', edgecolor='navy')
            ax[0].set_title(f'Distribusi Jumlah Data Masuk per Jam', fontsize=14, fontweight='bold')
            ax[0].set_xlabel('Jam Ke-')
            ax[0].set_ylabel('Jumlah Records')
            
            if not hourly_counts.empty:
                ax[0].set_xticks(range(int(min(hourly_counts.index)), int(max(hourly_counts.index)) + 1)) 
            
            for i, v in enumerate(hourly_counts):
                ax[0].text(hourly_counts.index[i], v + 100, str(v), ha='center', fontweight='bold')

            # Grafik 2: Progress Kumulatif
            ax[1].plot(df_receive_filter['created_at'], df_receive_filter['cumulative_count'], color='red', linewidth=2)
            ax[1].set_title('Progress Kumulatif (Garis Mendatar = Sistem Idle)', fontsize=14, fontweight='bold')
            ax[1].set_xlabel('Waktu')
            ax[1].set_ylabel('Total Data Terproses')
            ax[1].grid(True, linestyle=':', alpha=0.6)
            
            zona_wib = pytz.timezone('Asia/Jakarta')
            ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=zona_wib))

            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning(f"⚠️ Tidak ada data untuk tanggal {selected_day}.")

        st.markdown("---")



        # --- BAGIAN 3: ANALISIS LATENSI (BJB VS INTERNAL) ---
        st.header("⏱️ Analisis Waktu Tunggu (Latency)")
        
        try:
            # Kalkulasi Latensi BJB
            sent_summary = df_sent_filter.groupby('file_name')['created_at'].max().reset_index()
            sent_summary.rename(columns={'created_at': 'waktu_sent_terakhir'}, inplace=True)
            sent_summary['base_file_name'] = sent_summary['file_name'].str.replace(r'^I_?', '', regex=True)
            
            recv_summary = df_receive_filter.groupby('file_name')['created_at'].min().reset_index()
            recv_summary.rename(columns={'created_at': 'waktu_receive_pertama'}, inplace=True)
            recv_summary['base_file_name'] = recv_summary['file_name'].str.replace(r'^O_?', '', regex=True)
            
            df_compare = pd.merge(sent_summary, recv_summary, on='base_file_name', how='inner')
            df_compare['bjb_latency_seconds'] = (df_compare['waktu_receive_pertama'] - df_compare['waktu_sent_terakhir']).dt.total_seconds()
            df_compare['bjb_latency_minutes'] = df_compare['bjb_latency_seconds'] / 60
            
            # Durasi Internal
            recv_proc = df_receive_filter.groupby('file_name')['created_at'].agg(['min', 'max', 'count']).reset_index()
            recv_proc['durasi_menit'] = (recv_proc['max'] - recv_proc['min']).dt.total_seconds() / 60
            recv_proc['durasi_detik'] = (recv_proc['max'] - recv_proc['min']).dt.total_seconds()

            sent_proc = df_sent_filter.groupby('file_name')['created_at'].agg(['min', 'max', 'count']).reset_index()
            sent_proc['durasi_menit'] = (sent_proc['max'] - sent_proc['min']).dt.total_seconds() / 60
            sent_proc['durasi_detik'] = (sent_proc['max'] - sent_proc['min']).dt.total_seconds()
            
            # --- TAMPILAN KPI ---
            st.subheader("Performance Monitor")
            k1, k2, k3 = st.columns(3)
            
            if not df_compare.empty:
                k1.metric("Rata-rata Latensi FTP ", f"{df_compare['bjb_latency_minutes'].mean():.2f} Menit", 
                          delta=f"{df_compare['bjb_latency_seconds'].mean():.2f} Detik", delta_color="off")
            if not sent_proc.empty:
                k2.metric("Rata-rata Proses Insert untuk Generate Request (File Sent)", f"{sent_proc['durasi_menit'].mean():.2f} Menit", 
                          delta=f"{sent_proc['durasi_detik'].mean():.2f} Detik", delta_color="off")
            if not recv_proc.empty:
                k3.metric("Rata-rata Proses Membaca dan Insert File Response  (File Receive)", f"{recv_proc['durasi_menit'].mean():.2f} Menit", 
                          delta=f"{recv_proc['durasi_detik'].mean():.2f} Detik", delta_color="off")

            st.write("---")
            k4, k5 = st.columns(2)
            if not sent_proc.empty:
                k4.metric("Durasi  Terlama untuk Insert File Request (File Sent)", f"{sent_proc['durasi_menit'].max():.2f} Menit", 
                          delta=f"{sent_proc['durasi_detik'].max():.2f} Detik", delta_color="off")
            if not recv_proc.empty:
                k5.metric("Durasi Terlama untuk insert file Response (File Receive)", f"{recv_proc['durasi_menit'].max():.2f} Menit", 
                          delta=f"{recv_proc['durasi_detik'].max():.2f} Detik", delta_color="off")

            # --- TABEL RINCIAN ---
            st.subheader("Rincian per File")
            tab1, tab2, tab3 = st.tabs(["Latensi Middleware", "Performa File Sent", "Performa File Receive"])
            
            with tab1:
                st.dataframe(
                    df_compare[['base_file_name', 'waktu_sent_terakhir', 'waktu_receive_pertama', 'bjb_latency_minutes', 'bjb_latency_seconds']]
                    .sort_values('bjb_latency_minutes', ascending=False)
                    .rename(columns={
                        'waktu_sent_terakhir': 'insert_data_file_sent_terakhir', 
                        'waktu_receive_pertama': 'insert_data_file_receive_terakhir', 
                        'bjb_latency_minutes': 'latency_minutes', 
                        'bjb_latency_seconds': 'latency_seconds'
                    }), 
                    width='stretch'
                )
            
            with tab2:
                # Perbaikan: sort_values() dulu, baru .rename()
                st.dataframe(
                    sent_proc[['file_name', 'min', 'max', 'count', 'durasi_menit', 'durasi_detik']]
                    .sort_values('durasi_detik', ascending=False)
                    .rename(columns={'count': 'Jumlah Data'}), 
                    width='stretch'
                )
                
            with tab3:
                # Perbaikan: sort_values() dulu, baru .rename()
                st.dataframe(
                    recv_proc[['file_name', 'min', 'max', 'count', 'durasi_menit', 'durasi_detik']]
                    .sort_values('durasi_detik', ascending=False)
                    .rename(columns={'count': 'Jumlah Data'}), 
                    width='stretch'
                )

        except Exception as e:
            st.error(f"Terjadi kesalahan saat mengkalkulasi latensi: {e}")
    else:
        st.info("👈 Silakan klik tombol ' Proses & Validasi Data' di sidebar untuk memulai analisis.")

else:
    # Reset status jika file di-remove
    st.session_state['data_valid'] = False
    st.info("👈 Silakan upload file `app_ftp_file_sent.csv` dan `app_ftp_file_receive.csv` di sidebar untuk memulai.")