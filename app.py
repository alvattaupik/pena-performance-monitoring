import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard PENA", layout="wide")
st.title("📊 Dashboard Analisis Performance PENA")
st.markdown("Aplikasi pemantauan performa pengiriman, penerimaan, dan verifikasi file posting.")

# --- PILIHAN MODE ANALISIS ---
mode_analisis = st.sidebar.radio(
    "Pilih Mode Analisis:",
    ["Analisis Performa Posting", "Analisis Performa Verifikasi"]
)
st.sidebar.markdown("---")

# =====================================================================
# MODE 1: ANALISIS PERFORMA POSTING 
# =====================================================================
if mode_analisis == "Analisis Performa Posting":
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
                            'waktu_receive_pertama': 'insert_data_file_receive_pertama', 
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




# =====================================================================
# MODE 2: ANALISIS PERFORMA VERIFIKASI 
# =====================================================================
elif mode_analisis == "Analisis Performa Verifikasi":
    st.sidebar.header("1. Upload Dataset Verifikasi")
    file_request = st.sidebar.file_uploader("Upload verif_request.csv", type=['csv'], key="verif_req")
    file_response = st.sidebar.file_uploader("Upload verif_response.csv", type=['csv'], key="verif_res")

    if file_request and file_response:
        btn_verif = st.sidebar.button("Proses Data Verifikasi")
        
        if btn_verif:
            with st.spinner("Memuat data verifikasi..."):
                try:
                    df_req = pd.read_csv(file_request, low_memory=False)
                    df_res = pd.read_csv(file_response, low_memory=False)

                    # Tambahkan dayfirst=True agar 2/4 dibaca 2 April, bukan 4 Februari
                    df_req['created_at'] = pd.to_datetime(df_req['created_at'], format='mixed', dayfirst=True, errors='coerce')
                    df_res['created_at'] = pd.to_datetime(df_res['created_at'], format='mixed', dayfirst=True, errors='coerce')
                    
                    # Hapus baris yang format waktunya hancur/kosong (NaT)
                    df_req = df_req.dropna(subset=['created_at'])
                    df_res = df_res.dropna(subset=['created_at'])
                    
                    st.session_state['df_req'] = df_req
                    st.session_state['df_res'] = df_res
                    st.session_state['data_valid_verif'] = True
                    st.sidebar.success("✅ Data Verifikasi dimuat!")
                except Exception as e:
                    st.sidebar.error(f"❌ Terjadi kesalahan: Pastikan kedua file memiliki kolom 'file_name_request' dan 'created_at'. Error: {e}")
                    st.stop()

        if st.session_state.get('data_valid_verif', False):
            df_req = st.session_state['df_req']
            df_res = st.session_state['df_res']

            # --- FILTER TANGGAL ---
            st.sidebar.header("2. Filter Data")
            
            # Ambil tanggal yang tersedia di dataset agar dropdown dinamis dan tidak error
            tanggal_tersedia = sorted(df_req['created_at'].dt.day.dropna().unique().astype(int).tolist())
            
            if not tanggal_tersedia:
                st.sidebar.error("⚠️ Tidak ada data tanggal yang valid untuk difilter.")
                st.stop()

            selected_day_v = st.sidebar.selectbox("Pilih Tanggal (Hari):", tanggal_tersedia, key="filter_v")

            # Filter dataset berdasarkan tanggal
            df_req_filter = df_req[df_req['created_at'].dt.day == selected_day_v].copy()
            df_res_filter = df_res[df_res['created_at'].dt.day == selected_day_v].copy()

            # --- BAGIAN 1: RINGKASAN DATA ---
            st.header(f"Ringkasan Data Verifikasi (Tanggal {selected_day_v})")
            col1, col2 = st.columns(2)
            col1.metric("Total Data Request", f"{len(df_req_filter):,} Baris")
            col2.metric("Total Data Response", f"{len(df_res_filter):,} Baris")
            st.markdown("---")

            # --- BAGIAN 2: GRAFIK BOTTLENECK (REQUEST) ---
            st.header("📈 Analisis Kecepatan & Distribusi File Request")
            
            if not df_req_filter.empty:
                df_req_filter = df_req_filter.sort_values('created_at')
                df_req_filter['hour'] = df_req_filter['created_at'].dt.hour
                df_req_filter['cumulative_count'] = range(1, len(df_req_filter) + 1)

                fig, ax = plt.subplots(2, 1, figsize=(12, 10))

                # Grafik 1: Distribusi per Jam
                hourly_counts = df_req_filter.groupby('hour').size()
                ax[0].bar(hourly_counts.index, hourly_counts.values, color='skyblue', edgecolor='navy')
                ax[0].set_title(f'Distribusi Jumlah Data Request Masuk per Jam', fontsize=14, fontweight='bold')
                ax[0].set_xlabel('Jam Ke-')
                ax[0].set_ylabel('Jumlah Records')
                
                if not hourly_counts.empty:
                    ax[0].set_xticks(range(int(min(hourly_counts.index)), int(max(hourly_counts.index)) + 1)) 
                
                for i, v in enumerate(hourly_counts):
                    ax[0].text(hourly_counts.index[i], v + 100, str(v), ha='center', fontweight='bold')

                # Grafik 2: Progress Kumulatif
                ax[1].plot(df_req_filter['created_at'], df_req_filter['cumulative_count'], color='red', linewidth=2)
                ax[1].set_title('Progress Kumulatif Request (Garis Mendatar = Sistem Idle)', fontsize=14, fontweight='bold')
                ax[1].set_xlabel('Waktu')
                ax[1].set_ylabel('Total Data Terproses')
                ax[1].grid(True, linestyle=':', alpha=0.6)
                
                zona_wib = pytz.timezone('Asia/Jakarta')

                ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                

                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning(f"⚠️ Tidak ada data Request untuk tanggal {selected_day_v}.")

            st.markdown("---")


            # --- BAGIAN 2: GRAFIK BOTTLENECK (RESPONSE) ---
            st.header("📈 Analisis Kecepatan & Distribusi File Response")
            
            if not df_res_filter.empty:
                df_res_filter = df_res_filter.sort_values('created_at')
                df_res_filter['hour'] = df_res_filter['created_at'].dt.hour
                df_res_filter['cumulative_count'] = range(1, len(df_res_filter) + 1)

                fig, ax = plt.subplots(2, 1, figsize=(12, 10))

                # Grafik 1: Distribusi per Jam
                hourly_counts = df_res_filter.groupby('hour').size()
                ax[0].bar(hourly_counts.index, hourly_counts.values, color='skyblue', edgecolor='navy')
                ax[0].set_title(f'Distribusi Jumlah Data Response Masuk per Jam', fontsize=14, fontweight='bold')
                ax[0].set_xlabel('Jam Ke-')
                ax[0].set_ylabel('Jumlah Records')
                
                if not hourly_counts.empty:
                    ax[0].set_xticks(range(int(min(hourly_counts.index)), int(max(hourly_counts.index)) + 1)) 
                
                for i, v in enumerate(hourly_counts):
                    ax[0].text(hourly_counts.index[i], v + 100, str(v), ha='center', fontweight='bold')

                # Grafik 2: Progress Kumulatif
                ax[1].plot(df_res_filter['created_at'], df_res_filter['cumulative_count'], color='red', linewidth=2)
                ax[1].set_title('Progress Kumulatif Response (Garis Mendatar = Sistem Idle)', fontsize=14, fontweight='bold')
                ax[1].set_xlabel('Waktu')
                ax[1].set_ylabel('Total Data Terproses')
                ax[1].grid(True, linestyle=':', alpha=0.6)
                
                zona_wib = pytz.timezone('Asia/Jakarta')
                # ---ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=zona_wib))
                ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning(f"⚠️ Tidak ada data Response untuk tanggal {selected_day_v}.")

            st.markdown("---")



            # --- BAGIAN 3: ANALISIS LATENSI VERIFIKASI ---
            st.header("⏱️ Analisis Waktu Tunggu Verifikasi (Latency)")
            
            try:
                # Kalkulasi Latensi (Request vs Response)
                req_summary = df_req_filter.groupby('file_name_request')['created_at'].max().reset_index()
                req_summary.rename(columns={'created_at': 'waktu_request_terakhir'}, inplace=True)
                
                res_summary = df_res_filter.groupby('file_name_request')['created_at'].min().reset_index()
                res_summary.rename(columns={'created_at': 'waktu_response_pertama'}, inplace=True)
                
                df_compare = pd.merge(req_summary, res_summary, on='file_name_request', how='inner')
                df_compare['verif_latency_seconds'] = (df_compare['waktu_response_pertama'] - df_compare['waktu_request_terakhir']).dt.total_seconds()
                df_compare['verif_latency_minutes'] = df_compare['verif_latency_seconds'] / 60
                
                # Durasi Internal
                res_proc = df_res_filter.groupby('file_name_response')['created_at'].agg(['min', 'max', 'count']).reset_index()
                res_proc['durasi_menit'] = (res_proc['max'] - res_proc['min']).dt.total_seconds() / 60
                res_proc['durasi_detik'] = (res_proc['max'] - res_proc['min']).dt.total_seconds()

                req_proc = df_req_filter.groupby('file_name_request')['created_at'].agg(['min', 'max', 'count']).reset_index()
                req_proc['durasi_menit'] = (req_proc['max'] - req_proc['min']).dt.total_seconds() / 60
                req_proc['durasi_detik'] = (req_proc['max'] - req_proc['min']).dt.total_seconds()
                
                # --- TAMPILAN KPI ---
                st.subheader("Performance Monitor")
                # --- TAMBAHAN BARU: METRIK JUMLAH DATA ---
                j1, j2, j3 = st.columns(3)
                if not df_compare.empty:
                    j1.metric("Total File Request & Response", f"{len(df_compare):,} File")
                if not df_req_filter.empty:
                    j2.metric("Total Baris Data Request", f"{len(df_req_filter):,} Baris")
                if not df_res_filter.empty:
                    j3.metric("Total Baris Data Response", f"{len(df_res_filter):,} Baris")
                
                st.write("---") #


                k1, k2, k3 = st.columns(3)
                
                if not df_compare.empty:
                    k1.metric("Rata-rata Latensi Verifikasi", f"{df_compare['verif_latency_minutes'].mean():.2f} Menit", 
                              delta=f"{df_compare['verif_latency_seconds'].mean():.2f} Detik", delta_color="off")
                if not req_proc.empty:
                    k2.metric("Rata-rata Proses Insert (File Request)", f"{req_proc['durasi_menit'].mean():.2f} Menit", 
                              delta=f"{req_proc['durasi_detik'].mean():.2f} Detik", delta_color="off")
                if not res_proc.empty:
                    k3.metric("Rata-rata Proses Membaca & Insert (File Response)", f"{res_proc['durasi_menit'].mean():.2f} Menit", 
                              delta=f"{res_proc['durasi_detik'].mean():.2f} Detik", delta_color="off")

                st.write("---")
                k4, k5 = st.columns(2)
                if not req_proc.empty:
                    k4.metric("Durasi Terlama Insert Request", f"{req_proc['durasi_menit'].max():.2f} Menit", 
                              delta=f"{req_proc['durasi_detik'].max():.2f} Detik", delta_color="off")
                if not res_proc.empty:
                    k5.metric("Durasi Terlama Insert Response", f"{res_proc['durasi_menit'].max():.2f} Menit", 
                              delta=f"{res_proc['durasi_detik'].max():.2f} Detik", delta_color="off")

                # --- TAMBAHAN BARU: TOTAL DURASI PROSES ---
                st.write("---")
                k6, k7, k8 = st.columns(3)
                if not df_req_filter.empty:
                    total_req_dur = df_req_filter['created_at'].max() - df_req_filter['created_at'].min()
                    total_req_min = total_req_dur.total_seconds() / 60
                    req_start = df_req_filter['created_at'].min().strftime('%H:%M:%S')
                    req_end = df_req_filter['created_at'].max().strftime('%H:%M:%S')
                    k6.metric("Total Durasi Insert Request", f"{total_req_min:.2f} Menit", 
                              delta=f"Start: {req_start} | End: {req_end}", delta_color="off")
                if not df_res_filter.empty:
                    total_res_dur = df_res_filter['created_at'].max() - df_res_filter['created_at'].min()
                    total_res_min = total_res_dur.total_seconds() / 60
                    res_start = df_res_filter['created_at'].min().strftime('%H:%M:%S')
                    res_end = df_res_filter['created_at'].max().strftime('%H:%M:%S')
                    k7.metric("Total Durasi Insert Response", f"{total_res_min:.2f} Menit", 
                              delta=f"Start: {res_start} | End: {res_end}", delta_color="off")
                if not df_req_filter.empty and not df_res_filter.empty:
                    total_all_dur = df_res_filter['created_at'].max() - df_req_filter['created_at'].min()
                    total_all_min = total_all_dur.total_seconds() / 60
                    all_start = df_req_filter['created_at'].min().strftime('%H:%M:%S')
                    all_end = df_res_filter['created_at'].max().strftime('%H:%M:%S')
                    k8.metric("Total Durasi Seluruh Proses", f"{total_all_min:.2f} Menit", 
                              delta=f"Start: {all_start} | End: {all_end}", delta_color="off")

                # --- TABEL RINCIAN ---
                st.subheader("Rincian per File")
                tab1, tab2, tab3 = st.tabs(["Latensi Verifikasi", "Performa File Request", "Performa File Response"])
                
                with tab1:
                    st.dataframe(
                        df_compare[['file_name_request', 'waktu_request_terakhir', 'waktu_response_pertama', 'verif_latency_minutes', 'verif_latency_seconds']]
                        .sort_values('verif_latency_minutes', ascending=False)
                        .rename(columns={
                            'waktu_request_terakhir': 'insert_data_request_terakhir', 
                            'waktu_response_pertama': 'insert_data_response_pertama', 
                            'verif_latency_minutes': 'latency_minutes', 
                            'verif_latency_seconds': 'latency_seconds'
                        }), 
                        width='stretch'
                    )
                
                with tab2:
                    st.dataframe(
                        req_proc[['file_name_request', 'min', 'max', 'count', 'durasi_menit', 'durasi_detik']]
                        .sort_values('durasi_detik', ascending=False)
                        .rename(columns={'count': 'Jumlah Data'}), 
                        width='stretch'
                    )
                    
                with tab3:
                    st.dataframe(
                        res_proc[['file_name_response', 'min', 'max', 'count', 'durasi_menit', 'durasi_detik']]
                        .sort_values('durasi_detik', ascending=False)
                        .rename(columns={'count': 'Jumlah Data'}), 
                        width='stretch'
                    )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat mengkalkulasi latensi: {e}")
    else:
        st.session_state['data_valid_verif'] = False
        st.info("👈 Silakan upload file verif_request.csv dan verif_response.csv di sidebar untuk memulai Mode Verifikasi.")