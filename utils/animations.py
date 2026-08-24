# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 11:52:02 2026

@author: taric
"""

# -*- coding: utf-8 -*-
"""
Animasyon ve Stil Merkezi - SARCON Portal
Tüm animasyonlar, CSS ve JavaScript burada toplanır.
Kolayca açıp kapatmak için flag'ler mevcuttur.
"""

import streamlit as st
import time
from contextlib import contextmanager

# ===========================
# ANİMASYON FLAG'LERİ (Kolay aç/kapat)
# ===========================
ENABLE_FADE_IN = True          # Sayfa geçişleri
ENABLE_HOVER = True            # Buton/kart hover
ENABLE_SPINNER = True          # Yükleme spinner
ENABLE_SKELETON = True         # Skeleton loading
ENABLE_PLOTLY_ANIMATION = True # Grafik animasyonları
ENABLE_SMOOTH_EXPAND = True    # Panel açılma
ENABLE_TOAST = True            # Bildirimler

# ===========================
# CSS ANİMASYONLARI
# ===========================
def get_animation_css():
    """Tüm animasyon CSS'lerini döndürür"""
    css = """
    <style>
        /* ===== SAYFA GEÇİŞLERİ ===== */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Sayfa içeriği */
        .page-content {
            animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        .page-content-fast {
            animation: fadeInUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        .page-content-slow {
            animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        /* ===== HOVER EFEKTLERİ ===== */
        /* Butonlar */
        .animate-btn {
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .animate-btn:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3) !important;
        }
        
        .animate-btn:active {
            transform: scale(0.96) !important;
        }
        
        /* Kartlar */
        .animate-card {
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: default;
            position: relative;
            overflow: hidden;
        }
        
        .animate-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.4s ease;
            pointer-events: none;
        }
        
        .animate-card:hover {
            transform: translateY(-6px) !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4) !important;
            border-color: #3b82f6 !important;
        }
        
        .animate-card:hover::before {
            opacity: 1;
        }
        
        /* Özel kart - glitch efekti */
        .animate-card-glitch:hover {
            animation: glitch 0.3s ease;
        }
        
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-3px, 2px); }
            40% { transform: translate(3px, -2px); }
            60% { transform: translate(-2px, 3px); }
            80% { transform: translate(2px, -3px); }
        }
        
        /* ===== SPINNER / LOADING ===== */
        .spinner-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem 0;
        }
        
        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid #262626;
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .spinner-text {
            color: #737373;
            margin-top: 1rem;
            font-size: 0.9rem;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        /* ===== SKELETON LOADING ===== */
        .skeleton {
            background: linear-gradient(90deg, #1a1a1a 25%, #262626 50%, #1a1a1a 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 6px;
            min-height: 20px;
            margin-bottom: 0.5rem;
        }
        
        .skeleton-text {
            height: 16px;
            margin: 8px 0;
        }
        
        .skeleton-title {
            height: 28px;
            width: 60%;
            margin: 12px 0;
        }
        
        .skeleton-card {
            height: 120px;
            border-radius: 12px;
        }
        
        .skeleton-chart {
            height: 300px;
            border-radius: 12px;
        }
        
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* ===== SMOOTH EXPAND ===== */
        .smooth-expand {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
        }
        
        .smooth-expand .stExpander > div:last-child {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            max-height: 0 !important;
            opacity: 0 !important;
            overflow: hidden !important;
        }
        
        .smooth-expand .stExpander[aria-expanded="true"] > div:last-child {
            max-height: 2000px !important;
            opacity: 1 !important;
        }
        
        /* ===== TOAST / BİLDİRİMLER ===== */
        .toast-container {
            position: fixed;
            top: 90px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 380px;
            width: 100%;
            pointer-events: none;
        }
        
        .toast {
            padding: 16px 20px;
            border-radius: 12px;
            background: #1a1a1a;
            border: 1px solid #262626;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
            pointer-events: auto;
            display: flex;
            align-items: center;
            gap: 12px;
            backdrop-filter: blur(10px);
        }
        
        .toast-success {
            border-left: 4px solid #22c55e;
        }
        
        .toast-error {
            border-left: 4px solid #ef4444;
        }
        
        .toast-warning {
            border-left: 4px solid #f59e0b;
        }
        
        .toast-info {
            border-left: 4px solid #3b82f6;
        }
        
        .toast-icon {
            font-size: 1.4rem;
            flex-shrink: 0;
        }
        
        .toast-content {
            flex: 1;
        }
        
        .toast-title {
            color: #ffffff;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .toast-message {
            color: #a3a3a3;
            font-size: 0.8rem;
            margin-top: 2px;
        }
        
        .toast-close {
            cursor: pointer;
            color: #737373;
            font-size: 1.2rem;
            transition: color 0.2s;
            background: none;
            border: none;
        }
        
        .toast-close:hover {
            color: #ffffff;
        }
        
        /* Toast kaybolma */
        .toast-hide {
            animation: slideOutRight 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }
        
        /* ===== PLOTLY ÖZEL ===== */
        /* Plotly hover efektleri */
        .js-plotly-plot .plotly .hoverlayer {
            transition: all 0.3s ease;
        }
        
        .js-plotly-plot .plotly .hoverlayer .hovertext {
            background: #1a1a1a !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
            border: 1px solid #262626 !important;
        }
        
        /* ===== ÖZEL EFEKTLER ===== */
        /* Parıltı efekti */
        .shimmer-effect {
            position: relative;
            overflow: hidden;
        }
        
        .shimmer-effect::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent 40%,
                rgba(255, 255, 255, 0.03) 50%,
                transparent 60%
            );
            animation: shimmerMove 3s infinite;
        }
        
        @keyframes shimmerMove {
            0% { transform: translateX(-100%) rotate(45deg); }
            100% { transform: translateX(100%) rotate(45deg); }
        }
        
        /* Nabız efekti */
        .pulse-ring {
            animation: pulseRing 2s ease-in-out infinite;
        }
        
        @keyframes pulseRing {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            50% { box-shadow: 0 0 0 15px rgba(59, 130, 246, 0); }
        }
        
        /* Sayfa geçişi için placeholder */
        .page-transition {
            animation: fadeInUp 0.5s ease-out forwards;
        }
    </style>
    """
    return css

# ===========================
# JAVASCRIPT ANİMASYONLARI
# ===========================
def get_animation_js():
    """Tüm animasyon JavaScript'lerini döndürür"""
    js = """
    <script>
        // ===== TOAST YÖNETİMİ =====
        function showToast(type, title, message, duration = 4000) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            
            const toast = document.createElement('div');
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
                <div class="toast-content">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
            `;
            
            container.appendChild(toast);
            
            // Otomatik kaybol
            setTimeout(() => {
                toast.classList.add('toast-hide');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        // ===== SKELETON YÜKLEME =====
        function showSkeleton(elementId, type = 'card') {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            const skeletons = {
                card: '<div class="skeleton skeleton-card"></div>',
                text: '<div class="skeleton skeleton-text"></div>',
                title: '<div class="skeleton skeleton-title"></div>',
                chart: '<div class="skeleton skeleton-chart"></div>'
            };
            
            element.innerHTML = skeletons[type] || skeletons.card;
        }
        
        // ===== SAYFA GEÇİŞİ =====
        document.addEventListener('DOMContentLoaded', function() {
            const main = document.querySelector('section.main');
            if (main) {
                main.classList.add('page-content');
            }
        });
    </script>
    """
    return js

# ===========================
# STREAMLIT ENTEGRASYONU
# ===========================
def apply_animations():
    """Tüm animasyonları sayfaya uygular"""
    css = ""
    js = ""
    
    if ENABLE_FADE_IN or ENABLE_HOVER or ENABLE_SMOOTH_EXPAND:
        css += get_animation_css()
    
    if ENABLE_TOAST:
        js += get_animation_js()
    
    # CSS ve JS'yi sayfaya ekle
    if css:
        st.markdown(css, unsafe_allow_html=True)
    
    if js:
        # Toast container
        if ENABLE_TOAST:
            st.markdown('<div id="toast-container" class="toast-container"></div>', unsafe_allow_html=True)
        st.markdown(js, unsafe_allow_html=True)

# ===========================
# ANİMASYON FONKSİYONLARI
# ===========================

@contextmanager
def loading_spinner(text="Yükleniyor..."):
    """Yükleme spinner'ı gösterir"""
    if not ENABLE_SPINNER:
        yield
        return
    
    with st.spinner(text):
        yield

def show_skeleton(placeholder, skeleton_type='card', count=1):
    """Skeleton loading gösterir"""
    if not ENABLE_SKELETON:
        return
    
    skeleton_html = ""
    for _ in range(count):
        skeleton_html += f'<div class="skeleton skeleton-{skeleton_type}"></div>'
    
    placeholder.markdown(skeleton_html, unsafe_allow_html=True)

def animate_plotly(fig, duration=500):
    """Plotly grafiğine animasyon ekler"""
    if not ENABLE_PLOTLY_ANIMATION:
        return fig
    
    # Plotly animasyon ayarları
    fig.update_layout(
        transition={
            'duration': duration,
            'easing': 'cubic-in-out'
        },
        hovermode='x unified'
    )
    
    # Trace'lere animasyon ekle
    for trace in fig.data:
        if hasattr(trace, 'animation'):
            continue
    
    return fig

def toast_success(title, message, duration=4000):
    """Başarı bildirimi gösterir"""
    if not ENABLE_TOAST:
        st.success(f"{title}: {message}")
        return
    
    toast_js = f"""
    <script>
        if (typeof showToast === 'function') {{
            showToast('success', '{title}', '{message}', {duration});
        }}
    </script>
    """
    st.markdown(toast_js, unsafe_allow_html=True)

def toast_error(title, message, duration=4000):
    """Hata bildirimi gösterir"""
    if not ENABLE_TOAST:
        st.error(f"{title}: {message}")
        return
    
    toast_js = f"""
    <script>
        if (typeof showToast === 'function') {{
            showToast('error', '{title}', '{message}', {duration});
        }}
    </script>
    """
    st.markdown(toast_js, unsafe_allow_html=True)

def toast_warning(title, message, duration=4000):
    """Uyarı bildirimi gösterir"""
    if not ENABLE_TOAST:
        st.warning(f"{title}: {message}")
        return
    
    toast_js = f"""
    <script>
        if (typeof showToast === 'function') {{
            showToast('warning', '{title}', '{message}', {duration});
        }}
    </script>
    """
    st.markdown(toast_js, unsafe_allow_html=True)

def toast_info(title, message, duration=4000):
    """Bilgi bildirimi gösterir"""
    if not ENABLE_TOAST:
        st.info(f"{title}: {message}")
        return
    
    toast_js = f"""
    <script>
        if (typeof showToast === 'function') {{
            showToast('info', '{title}', '{message}', {duration});
        }}
    </script>
    """
    st.markdown(toast_js, unsafe_allow_html=True)

# ===========================
# ANİMASYON KONTROL PANELİ
# ===========================
def animation_control_panel():
    """Animasyon ayarları paneli (debug için)"""
    with st.expander("⚙️ Animasyon Kontrol Paneli (Debug)"):
        st.caption("Tüm animasyonları açıp kapatabilirsiniz. Değişiklikler sayfa yenilendiğinde aktif olur.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Sayfa Geçişleri (Fade-in)", value=ENABLE_FADE_IN, key="debug_fade", disabled=True)
            st.checkbox("Hover Efektleri", value=ENABLE_HOVER, key="debug_hover", disabled=True)
            st.checkbox("Yükleme Spinner", value=ENABLE_SPINNER, key="debug_spinner", disabled=True)
        with col2:
            st.checkbox("Skeleton Loading", value=ENABLE_SKELETON, key="debug_skeleton", disabled=True)
            st.checkbox("Plotly Animasyon", value=ENABLE_PLOTLY_ANIMATION, key="debug_plotly", disabled=True)
            st.checkbox("Toast Bildirimler", value=ENABLE_TOAST, key="debug_toast", disabled=True)
        
        st.info("💡 İpuçları: Değişiklikler için utils/animations.py dosyasındaki ENABLE_ flag'lerini düzenleyin.")