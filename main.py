import os
import streamlit as st
from PIL import Image
import io
import zlib
import time
import ffmpeg

def get_file_size(file_path):
    try:
        size_bytes = os.path.getsize(file_path)
        return get_file_size_from_bytes(size_bytes)
    except FileNotFoundError:
        return "File not found"

def get_file_size_from_bytes(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.2f} KB"
    else:
        return f"{size_bytes/(1024*1024):.2f} MB"

def compress_video(input_path, output_path, target_size):
    probe = ffmpeg.probe(input_path)
    duration = float(probe['format']['duration'])
    target_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)
    
    ffmpeg.input(input_path)\
        .output(output_path, 
               vcodec='libx264', 
               video_bitrate=f"{int(target_bitrate*0.9)}k",
               audio_bitrate="128k")\
        .run()

def main():
    st.title("FILE SIZE REDUCER")
    uploaded_file = st.file_uploader("Choose a file", type=['jpg', 'jpeg', 'png', 'mp4', 'mov'])
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        if file_type in ['jpg', 'jpeg', 'png']:
           
            img = Image.open(uploaded_file)
            original_size = len(uploaded_file.getvalue()) 
            
            # Create sliders for compression options
            # Revert slider label
            quality = st.slider("Compression Level (JPEG Quality)", 1, 100, 85) 
            resize_percent = st.slider("Resize Percentage", 50, 100, 100)
            
            # --- Single Pass: Resize (if needed) and Compression ---
            if resize_percent < 100:
                width = int(img.width * resize_percent / 100)
                height = int(img.height * resize_percent / 100)
                img = img.resize((width, height), Image.LANCZOS)
            
            img_bytes = io.BytesIO() # Use single BytesIO object
            start_time = time.time() # Use single timer
            if file_type == 'png':
                # Single save for PNG
                img.save(img_bytes, format='PNG', optimize=True, compress_level=3) 
            else:
                # Single save for JPEG
                img.save(img_bytes, format='JPEG', quality=quality, optimize=True, progressive=True) 
            end_time = time.time()
            total_time = end_time - start_time # Calculate total time
            compressed_size = img_bytes.tell() # Get final compressed size
            print(f"Compression took {total_time:.2f} seconds")

            # --- Remove second pass logic ---

            # --- Show size comparison (reverted) ---
            st.success(f"Original size: {get_file_size_from_bytes(original_size)}")
            # Show only the final compressed size
            st.success(f"Compressed size: {get_file_size_from_bytes(compressed_size)}") 
            st.info(f"Compression time: {total_time:.2f} seconds") # Show total time
            
            # --- Offer download of the compressed file (reverted) ---
            st.download_button(
                label="Download compressed file", # Revert label
                data=img_bytes.getvalue(), # Use data from the single pass
                file_name=f"compressed_{uploaded_file.name}", # Revert filename
                mime=f"image/{file_type}"
            )
        else:
            # For non-image files, revert to single compression
            # Revert slider label
            compression_level = st.slider("Compression Level (zlib)", 1, 9, 9) 
            
            # Get original file data
            file_data = uploaded_file.getvalue()
            original_size = len(file_data)
            
            # --- Single Compression Pass ---
            start_time = time.time() # Use single timer
            # Single compression call
            compressed_data = zlib.compress(file_data, compression_level) 
            end_time = time.time()
            total_time = end_time - start_time # Calculate total time
            compressed_size = len(compressed_data) # Get final compressed size
            
            # --- Remove second pass logic ---

            # --- Show size comparison (reverted) ---
            st.success(f"Original size: {get_file_size_from_bytes(original_size)}")
            # Show only final compressed size
            st.success(f"Compressed size: {get_file_size_from_bytes(compressed_size)}") 
            st.info(f"Compression time: {total_time:.2f} seconds") # Show total time
            
            # --- Offer download of compressed file (reverted) ---
            st.download_button(
                label="Download compressed file", # Revert label
                data=compressed_data, # Use data from single pass
                file_name=f"compressed_{uploaded_file.name}.z", # Revert filename
                mime="application/octet-stream"
            )
            
            # Save uploaded video to temp file
            with open("temp_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Get target size from user
            target_size = st.slider("Target size (MB)", 1, 100, 10)
            
            if st.button("Compress Video"):
                with st.spinner('Compressing video...'):
                    try:
                        compress_video("temp_video.mp4", "compressed_video.mp4", target_size)
                        st.success("Video compressed successfully!")
                        
                        # Offer download
                        with open("compressed_video.mp4", "rb") as f:
                            st.download_button(
                                label="Download compressed video",
                                data=f,
                                file_name=f"compressed_{uploaded_file.name}",
                                mime="video/mp4"
                            )
                    except Exception as e:
                        st.error(f"Error compressing video: {e}")

if __name__ == "__main__":
    main()
