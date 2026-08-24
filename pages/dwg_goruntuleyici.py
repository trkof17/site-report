# -*- coding: utf-8 -*-
"""
SARCON Portal | DWG/DXF + IFC Goruntuleyici
Created: 21 Agustos 2026
@author: taric
"""

import streamlit as st
import pandas as pd
import tempfile
import os
import time

from utils.db import supabase, get_user_projects
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    ENABLE_FADE_IN,
    ENABLE_HOVER
)

# Sayfa yapilandirmasi
st.set_page_config(
    page_title="SARCON Portal | DWG/DXF + IFC Goruntuleyici",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Stilleri uygula
apply_global_styles(is_login=False)

# Top navbar
render_top_navbar()
st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ============================================
# IFC VIEWER HTML (Three.js + IFC.js)
# ============================================
IFC_VIEWER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IFC Viewer</title>
    <style>
        * { margin: 0; padding: 0; }
        body { 
            background: #0e1117; 
            overflow: hidden;
            font-family: Arial, sans-serif;
        }
        #viewer-container {
            width: 100vw;
            height: 100vh;
            position: relative;
        }
        #loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-size: 18px;
            text-align: center;
            z-index: 10;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            border-top: 4px solid #3b82f6;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #info {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: #888;
            font-size: 12px;
            background: rgba(0,0,0,0.7);
            padding: 8px 16px;
            border-radius: 20px;
            z-index: 10;
            pointer-events: none;
        }
        canvas {
            display: block !important;
            width: 100% !important;
            height: 100% !important;
        }
    </style>
</head>
<body>
    <div id="viewer-container">
        <div id="loading">
            <div class="spinner"></div>
            <div>IFC Modeli Yukleniyor...</div>
        </div>
        <div id="info">Fare ile dondurun | Scroll ile yakınlastirin</div>
    </div>

    <!-- Three.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <!-- IFC.js -->
    <script src="https://cdn.jsdelivr.net/npm/web-ifc@0.0.43/dist/web-ifc-api.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/web-ifc-three@0.0.39/dist/web-ifc-three.js"></script>

    <script>
        // IFC modelini yukle
        const container = document.getElementById('viewer-container');
        const loading = document.getElementById('loading');
        
        // Scene olustur
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0e1117);
        
        // Camera
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(10, 5, 10);
        camera.lookAt(0, 0, 0);
        
        // Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);
        
        // Orbit Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.rotateSpeed = 1.0;
        controls.zoomSpeed = 1.2;
        controls.target.set(0, 0, 0);
        
        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 7);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
        backLight.position.set(-5, -5, -5);
        scene.add(backLight);
        
        // Grid Helper
        const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x333333);
        scene.add(gridHelper);
        
        // Axes Helper
        const axesHelper = new THREE.AxesHelper(3);
        scene.add(axesHelper);
        
        // IFC yukleme fonksiyonu
        async function loadIFC(url) {
            try {
                // IFC API
                const ifcAPI = new IfcAPI();
                await ifcAPI.Init();
                
                // Dosyayi yukle
                const response = await fetch(url);
                const data = await response.arrayBuffer();
                const model = ifcAPI.OpenModel(new Uint8Array(data));
                
                // IFC'yi Three.js'e cevir
                const ifcLoader = new IFCLoader();
                const geometry = ifcLoader.loadGeometry(model);
                
                // Materyal olustur
                const material = new THREE.MeshPhongMaterial({
                    color: 0x4fc3f7,
                    transparent: true,
                    opacity: 0.9,
                    shininess: 30,
                    side: THREE.DoubleSide,
                });
                
                // Mesh olustur
                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                scene.add(mesh);
                
                // Camera fit
                const box = new THREE.Box3().setFromObject(mesh);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const distance = maxDim * 1.5;
                camera.position.set(center.x + distance * 0.5, center.y + distance * 0.3, center.z + distance * 0.5);
                controls.target.copy(center);
                controls.update();
                
                // Loading gizle
                loading.style.display = 'none';
                
                // Render loop
                function animate() {
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }
                animate();
                
                // Window resize
                window.addEventListener('resize', () => {
                    camera.aspect = container.clientWidth / container.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(container.clientWidth, container.clientHeight);
                });
                
            } catch (error) {
                console.error('IFC yukleme hatasi:', error);
                loading.innerHTML = '<div style="color:#ef5350;">IFC yuklenemedi: ' + error.message + '</div>';
            }
        }
        
        // Dosya URL'sini al
        const fileUrl = document.currentScript.getAttribute('data-file-url');
        if (fileUrl) {
            loadIFC(fileUrl);
        } else {
            loading.innerHTML = '<div style="color:#ffb74d;">IFC dosyasi yuklenmemis</div>';
        }
    </script>
</body>
</html>
"""

# ============================================
# DXF GORUNTULEME FONKSIYONU
# ============================================
def render_dxf_file(file_path):
    """DXF dosyasini matplotlib ile gor sellestir"""
    try:
        import ezdxf
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle
        import numpy as np
        
        doc = ezdxf.readfile(file_path)
        modelspace = doc.modelspace()
        
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_facecolor('#1a1a2e')
        fig.patch.set_facecolor('#0e1117')
        
        entity_count = 0
        
        for entity in modelspace:
            try:
                # LINE
                if entity.dxftype() == 'LINE':
                    ax.plot([entity.dxf.start.x, entity.dxf.end.x],
                           [entity.dxf.start.y, entity.dxf.end.y],
                           color='#4fc3f7', linewidth=1, alpha=0.8)
                    entity_count += 1
                
                # CIRCLE
                elif entity.dxftype() == 'CIRCLE':
                    circle = Circle((entity.dxf.center.x, entity.dxf.center.y),
                                   entity.dxf.radius,
                                   fill=False, edgecolor='#4fc3f7', linewidth=1)
                    ax.add_patch(circle)
                    entity_count += 1
                
                # ARC
                elif entity.dxftype() == 'ARC':
                    import math
                    start_angle = math.radians(entity.dxf.start_angle)
                    end_angle = math.radians(entity.dxf.end_angle)
                    theta = np.linspace(start_angle, end_angle, 100)
                    x = entity.dxf.center.x + entity.dxf.radius * np.cos(theta)
                    y = entity.dxf.center.y + entity.dxf.radius * np.sin(theta)
                    ax.plot(x, y, color='#4fc3f7', linewidth=1)
                    entity_count += 1
                
                # LWPOLYLINE
                elif entity.dxftype() == 'LWPOLYLINE':
                    points = list(entity.get_points())
                    if len(points) > 1:
                        x = [p[0] for p in points]
                        y = [p[1] for p in points]
                        if entity.closed:
                            ax.plot(x + [x[0]], y + [y[0]], color='#4fc3f7', linewidth=1)
                        else:
                            ax.plot(x, y, color='#4fc3f7', linewidth=1)
                    entity_count += 1
                
                # POLYLINE
                elif entity.dxftype() == 'POLYLINE':
                    points = list(entity.get_points())
                    if len(points) > 1:
                        x = [p[0] for p in points]
                        y = [p[1] for p in points]
                        ax.plot(x, y, color='#4fc3f7', linewidth=1)
                    entity_count += 1
                
                # TEXT
                elif entity.dxftype() == 'TEXT':
                    ax.text(entity.dxf.insert.x, entity.dxf.insert.y,
                           entity.dxf.text,
                           color='#ffb74d', fontsize=8, alpha=0.7)
                    entity_count += 1
                
                # MTEXT
                elif entity.dxftype() == 'MTEXT':
                    ax.text(entity.dxf.insert.x, entity.dxf.insert.y,
                           entity.dxf.text,
                           color='#ffb74d', fontsize=8, alpha=0.7)
                    entity_count += 1
                
                # SPLINE
                elif entity.dxftype() == 'SPLINE':
                    points = list(entity.control_points())
                    if len(points) > 1:
                        x = [p[0] for p in points]
                        y = [p[1] for p in points]
                        ax.plot(x, y, color='#81c784', linewidth=1, linestyle='--')
                    entity_count += 1
                    
            except Exception:
                continue
        
        # Grafik ayarlari
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, alpha=0.3, color='#444')
        ax.set_xlabel('X Koordinati', color='#888', fontsize=10)
        ax.set_ylabel('Y Koordinati', color='#888', fontsize=10)
        ax.tick_params(colors='#888')
        
        for spine in ax.spines.values():
            spine.set_color('#444')
        
        plt.tight_layout()
        return fig, entity_count
        
    except ImportError:
        toast_error("Hata", "ezdxf kutuphanesi yuklu degil: pip install ezdxf matplotlib")
        return None, 0
    except Exception as e:
        toast_error("Hata", f"DXF goruntuleme hatasi: {str(e)}")
        return None, 0

# ============================================
# SAYFA BASLIGI
# ============================================
st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">DWG/DXF + IFC Goruntuleyici</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        DXF (2D) ve IFC (3D/BIM) dosyalarini goruntuleyin ve yönetin
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================
# PROJE SECIMI
# ============================================
with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# ============================================
# TABS
# ============================================
tab1, tab2, tab3 = st.tabs(["Dosya Yukle", "Goruntule", "Kayitli Dosyalar"])

# ============================================
# TAB 1: DOSYA YUKLE
# ============================================
with tab1:
    st.markdown("### Dosya Yukle")
    
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
        margin-bottom: 1rem;
    ">
        <p style="color: #737373; margin: 0.2rem 0;"><strong style="color: #ffffff;">Desteklenen Formatlar:</strong></p>
        <p style="color: #737373; margin: 0.2rem 0;">• DXF (2D Cizim) - AutoCAD, FreeCAD'den donusturun</p>
        <p style="color: #737373; margin: 0.2rem 0;">• IFC (3D BIM Modeli) - Revit, ArchiCAD, Tekla'dan donusturun</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "DXF veya IFC dosyasi secin",
        type=['dxf', 'ifc'],
        help="DXF: 2D cizimler | IFC: 3D BIM modelleri"
    )
    
    if uploaded_file is not None:
        file_size = uploaded_file.size / 1024
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        toast_success("Basarili", f"Dosya yuklendi: {uploaded_file.name}")
        st.info(f"Dosya Boyutu: {file_size:.1f} KB | Format: {file_ext.upper()}")
        
        # Dosyayi gecici kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Formata gore goruntule
        if file_ext == 'dxf':
            with loading_spinner("DXF dosyasi goruntuleniyor..."):
                fig, count = render_dxf_file(tmp_path)
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    st.caption(f"{count} entity goruntulendi")
        
        elif file_ext == 'ifc':
            toast_info("Bilgi", "IFC modeli 3D olarak goruntulenecek")
            
            # IFC'yi storage'a yukle
            try:
                file_bytes = uploaded_file.getvalue()
                file_name = f"project_{project_id}/{uploaded_file.name}"
                
                # Storage'a yukle
                with loading_spinner("IFC dosyasi yukleniyor..."):
                    supabase.storage.from_("dwg_files").upload(file_name, file_bytes, {"cache-control": "3600"})
                    time.sleep(0.3)
                
                # Public URL al
                public_url = supabase.storage.from_("dwg_files").get_public_url(file_name)
                
                toast_success("Basarili", "IFC dosyasi yuklendi! Goruntuleme sekmesinden acabilirsiniz.")
                
            except Exception as e:
                toast_error("Hata", f"IFC yukleme hatasi: {e}")
        
        # Temizle
        os.unlink(tmp_path)
        
        # Kaydetme butonlari
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Dosyayi Kaydet", type="primary", use_container_width=True):
                try:
                    with loading_spinner("Dosya kaydediliyor..."):
                        file_bytes = uploaded_file.getvalue()
                        file_name = f"project_{project_id}/{uploaded_file.name}"
                        supabase.storage.from_("dwg_files").upload(file_name, file_bytes)
                        time.sleep(0.3)
                    toast_success("Basarili", "Dosya basariyla kaydedildi!")
                    st.rerun()
                except Exception as e:
                    toast_error("Hata", f"Kayit hatasi: {e}")
        
        with col2:
            st.download_button(
                label="Dosyayi Indir",
                data=uploaded_file,
                file_name=uploaded_file.name,
                mime="application/octet-stream",
                use_container_width=True
            )

# ============================================
# TAB 2: GORUNTULE
# ============================================
with tab2:
    st.markdown("### Dosya Goruntuleme")
    
    with loading_spinner("Dosyalar listeleniyor..."):
        try:
            file_list = supabase.storage.from_("dwg_files").list(f"project_{project_id}")
            time.sleep(0.3)
        except:
            file_list = []
        
        if not file_list:
            toast_info("Bilgi", "Henuz yuklenmis dosya yok.")
        else:
            # Dosya secimi
            file_names = [f["name"] for f in file_list]
            file_extensions = {
                f["name"]: f["name"].split('.')[-1].lower() for f in file_list
            }
            
            # Sadece DXF ve IFC goster
            filtered_files = [f for f in file_names if f.split('.')[-1].lower() in ['dxf', 'ifc']]
            
            if not filtered_files:
                toast_info("Bilgi", "Henuz DXF veya IFC dosyasi yuklenmemis.")
            else:
                selected_file = st.selectbox("Goruntulenecek dosyayi secin", filtered_files)
                
                if selected_file:
                    file_ext = selected_file.split('.')[-1].lower()
                    
                    try:
                        file_path = f"project_{project_id}/{selected_file}"
                        
                        with loading_spinner("Dosya yukleniyor..."):
                            file_data = supabase.storage.from_("dwg_files").download(file_path)
                            time.sleep(0.3)
                        
                        if file_ext == 'dxf':
                            # DXF goruntule
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                                tmp_file.write(file_data)
                                tmp_path = tmp_file.name
                            
                            with loading_spinner("DXF goruntuleniyor..."):
                                fig, count = render_dxf_file(tmp_path)
                                if fig:
                                    st.pyplot(fig, use_container_width=True)
                                    st.caption(f"{count} entity goruntulendi")
                            
                            os.unlink(tmp_path)
                        
                        elif file_ext == 'ifc':
                            # IFC goruntule
                            toast_info("Bilgi", "IFC modeli 3D goruntuleniyor...")
                            
                            # Dosyayi public URL ile goster
                            public_url = supabase.storage.from_("dwg_files").get_public_url(file_path)
                            
                            # IFC Viewer'i goster
                            st.components.v1.html(
                                IFC_VIEWER_HTML.replace(
                                    'const fileUrl = document.currentScript.getAttribute("data-file-url");',
                                    f'const fileUrl = "{public_url}";'
                                ),
                                height=700
                            )
                        
                        # Indir butonu
                        st.download_button(
                            label="Dosyayi Indir",
                            data=file_data,
                            file_name=selected_file,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        toast_error("Hata", f"Dosya goruntuleme hatasi: {e}")

# ============================================
# TAB 3: KAYITLI DOSYALAR
# ============================================
with tab3:
    st.markdown("### Yuklenmis Dosyalar")
    
    try:
        file_list = supabase.storage.from_("dwg_files").list(f"project_{project_id}")
        
        if not file_list:
            toast_info("Bilgi", "Henuz yuklenmis dosya yok.")
        else:
            # Tablo olustur
            df_files = pd.DataFrame([{
                "Dosya Adi": f["name"],
                "Format": f["name"].split('.')[-1].upper(),
                "Boyut": f"{f['metadata']['size'] / 1024:.1f} KB" if f.get('metadata') else "Bilinmiyor",
                "Tarih": f.get('created_at', '')[:10] if f.get('created_at') else ""
            } for f in file_list])
            
            st.dataframe(df_files, use_container_width=True, hide_index=True)
            
            # Dosya silme
            selected_file = st.selectbox(
                "Silmek istediginiz dosyayi secin",
                [""] + [f["name"] for f in file_list]
            )
            
            if selected_file:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("Dosyayi Sil", type="secondary", use_container_width=True):
                        try:
                            with loading_spinner("Dosya siliniyor..."):
                                file_path = f"project_{project_id}/{selected_file}"
                                supabase.storage.from_("dwg_files").remove([file_path])
                                time.sleep(0.3)
                            toast_success("Basarili", f"{selected_file} silindi!")
                            st.rerun()
                        except Exception as e:
                            toast_error("Hata", f"Silme hatasi: {e}")
                
                with col2:
                    try:
                        file_path = f"project_{project_id}/{selected_file}"
                        file_data = supabase.storage.from_("dwg_files").download(file_path)
                        st.download_button(
                            label="Indir",
                            data=file_data,
                            file_name=selected_file,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    except:
                        pass

    except Exception as e:
        toast_info("Bilgi", "Storage bucket'i henuz olusturulmamis.")

# ============================================
# BILGILER
# ============================================
with st.expander("Desteklenen Formatlar Hakkinda"):
    st.markdown("""
    ### DXF (2D Cizim)
    - **Kaynak:** AutoCAD, FreeCAD, DraftSight
    - **Goruntuleme:** Matplotlib (2D)
    - **Destek:** Line, Circle, Arc, Polyline, Text, Spline
    
    ### IFC (3D BIM Modeli)
    - **Kaynak:** Revit, ArchiCAD, Tekla, SketchUp
    - **Goruntuleme:** Three.js + IFC.js (3D)
    - **Destek:** 3D model, Dondurme, Yakınlastirma, Renklendirme
    
    ### Donusum Onerileri
    - **DWG -> DXF:** AutoCAD'de "Farkli Kaydet" -> DXF
    - **RVT -> IFC:** Revit'te "Dis Aktar" -> IFC
    - **SKP -> IFC:** SketchUp'da "Dis Aktar" -> IFC
    """)

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    .stFileUploader {
        border: 2px dashed #444;
        border-radius: 10px;
        padding: 20px;
        background: #0e1117;
    }
    .stDataFrame {
        background: #0e1117;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #0e1117;
        padding: 8px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 8px 16px;
        color: #888;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #1a1a2e;
        color: #fff;
        border: 1px solid #333;
    }
    .streamlit-expanderHeader {
        background: #0e1117;
        border-radius: 8px;
        border: 1px solid #262626;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.caption("Not: Dosyalar Supabase Storage'da 'dwg_files' bucket'inda saklanir.")

st.markdown('</div>', unsafe_allow_html=True)