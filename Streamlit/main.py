import streamlit as st
import requests
import time
import pandas as pd
import json
import base64
import hmac
import hashlib
import altair as alt
from urllib.parse import quote

# ==========================================
# 国际化配置 (i18n)
# ==========================================

TRANSLATIONS = {
    'zh': {
        'app_title': '物联网控制台',
        'login_title': '系统登录', 
        'default_account_hint': '默认账号: admin / 123456',
        'username': '用户名',
        'password': '密码', 
        'login_button': '登录',
        'login_error': '用户名或密码错误',
        'console_title': '控制台',
        'admin_role': '管理员',
        'logout': '退出',
        'remote_control': '远程控制',
        'acquisition_control': '采集控制',
        'start': '开始',
        'stop': '停止',
        'parameter_settings': '参数设置',
        'pga_gain': 'PGA 增益',
        'apply_pga': '应用 PGA 设置',
        'pga_sent': '已发送 PGA=',
        'sample_rate': '采样率',
        'apply_sample_rate': '应用采样率设置',
        'mode_sent': '已发送 Mode=',
        'system_settings': '系统设置',
        'auto_refresh': '自动刷新 (3s)',
        'clear_history': '清空历史数据',
        'clear_logs': '清空操作日志',
        'current_voltage': '当前电压',
        'current_pga': '当前 PGA',
        'last_updated': '最后更新',
        'device_status': '设备状态',
        'online': '在线',
        'offline_unknown': '离线/未知',
        'realtime_monitor': '实时监控',
        'data_details': '数据明细',
        'operation_logs': '操作日志',
        'no_history_data': '暂无历史数据，请等待数据刷新...',
        'download_csv': '下载 CSV 数据', 
        'no_data': '暂无数据',
        'no_logs': '暂无操作日志',
        'command_success': '指令下发成功',
        'seconds_ago': '秒前',
        'minutes_ago': '分钟前',
        'api_error': 'API 错误',
        'request_failed': '请求失败',
        'dark_mode': '黑夜模式',
        'language_select': '语言 / Language',
        'success_sent': '成功',
        'fail_sent': '失败',
        'exception_sent': '异常'
    },
    'en': {
        'app_title': 'IoT Console',
        'login_title': 'System Login',
        'default_account_hint': 'Default Account: admin / 123456',
        'username': 'Username',
        'password': 'Password',
        'login_button': 'Login',
        'login_error': 'Invalid username or password',
        'console_title': 'Console', 
        'admin_role': 'Administrator',
        'logout': 'Logout',
        'remote_control': 'Remote Control',
        'acquisition_control': 'Acquisition Control',
        'start': 'Start',
        'stop': 'Stop', 
        'parameter_settings': 'Parameter Settings',
        'pga_gain': 'PGA Gain',
        'apply_pga': 'Apply PGA',
        'pga_sent': 'Sent PGA=',
        'sample_rate': 'Sample Rate',
        'apply_sample_rate': 'Apply Sample Rate', 
        'mode_sent': 'Sent Mode=',
        'system_settings': 'System Settings',
        'auto_refresh': 'Auto Refresh (3s)',
        'clear_history': 'Clear History',
        'clear_logs': 'Clear Logs',
        'current_voltage': 'Current Voltage',
        'current_pga': 'Current PGA',
        'last_updated': 'Last Updated',
        'device_status': 'Device Status',
        'online': 'Online',
        'offline_unknown': 'Offline/Unknown',
        'realtime_monitor': 'Real-time Monitor',
        'data_details': 'Data Details',
        'operation_logs': 'Operation Logs',
        'no_history_data': 'No history data, waiting for refresh...',
        'download_csv': 'Download CSV',
        'no_data': 'No Data',
        'no_logs': 'No Logs', 
        'command_success': 'Command Sent Successfully',
        'seconds_ago': ' seconds ago',
        'minutes_ago': ' minutes ago',
        'api_error': 'API Error', 
        'request_failed': 'Request Failed',
        'dark_mode': 'Dark Mode',
        'language_select': 'Language / 语言',
        'success_sent': 'Success',
        'fail_sent': 'Failed',
        'exception_sent': 'Exception'
    }
}

def t(key):
    lang = st.session_state.get('language', 'zh')
    return TRANSLATIONS.get(lang, TRANSLATIONS['zh']).get(key, key)

# ==========================================
# 配置区域
# ==========================================

# OneNET 基础信息
PRODUCT_ID = "6R9kiumZF1"
DEVICE_NAME = "ESP32"
ACCESS_KEY = "GdFdkQGP1YsRv129daPTa+nV07XtGSmjQ0ERl91jIRk="  # 用户提供的 AccessKey

# OneNET Studio API 地址
BASE_URL = "https://iot-api.heclouds.com"

# ==========================================
# 核心逻辑函数
# ==========================================

# 使用 ESP32 代码中已验证可用的 Token
# 注意：这个 Token 有效期到 2030 年 (et=1923202207)
FIXED_TOKEN = "version=2018-10-31&res=products%2F6R9kiumZF1%2Fdevices%2FESP32&et=1923202207&method=md5&sign=S9SRMkTDgNQcH9lEVh%2Bnew%3D%3D"

def get_token(res):
    """
    直接返回已知的可用 Token，跳过本地计算，避免 Key 或算法不匹配的问题
    """
    return FIXED_TOKEN

# def get_token_dynamic(res):
#     """
#     (已禁用) 动态生成 Token
#     """
#     version = "2018-10-31"
    # 过期时间：当前时间 + 100天 (简单起见)
    et = int(time.time()) + 3600 * 24 * 100
    method = "md5" # 改为 md5 以匹配 ESP32 的配置
    
    # 构造签名字符串
    # res 需要 URL Encode
    res_encoded = quote(res, safe='')
    sign_str = f"{et}\n{method}\n{res_encoded}\n{version}"
    
    # 计算 HMAC-MD5
    key = base64.b64decode(ACCESS_KEY)
    sign = base64.b64encode(hmac.new(key, sign_str.encode('utf-8'), hashlib.md5).digest()).decode('utf-8')
    sign_encoded = quote(sign, safe='')
    
    # 拼接最终 Token
    token = f"version={version}&res={res_encoded}&et={et}&method={method}&sign={sign_encoded}"
    return token

def get_device_property(property_name):
    """
    查询设备属性最新值
    API: /thingmodel/query-device-property
    """
    url = f"{BASE_URL}/thingmodel/query-device-property"
    
    # 资源标识符
    res = f"products/{PRODUCT_ID}/devices/{DEVICE_NAME}"
    token = get_token(res)
    
    headers = {
        "Authorization": token
    }
    
    params = {
        "product_id": PRODUCT_ID,
        "device_name": DEVICE_NAME
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            # 解析属性列表
            properties = data.get("data", [])
            for prop in properties:
                if prop.get("identifier") == property_name:
                    return prop.get("value"), prop.get("time")
            return None, None
        else:
            st.error(f"{t('api_error')}: {data.get('msg')}")
            return None, None
    except Exception as e:
        st.error(f"{t('request_failed')}: {e}")
        return None, None

def set_device_property(params_dict):
    """
    下发设备属性设置指令
    API: /thingmodel/set-device-property
    """
    url = f"{BASE_URL}/thingmodel/set-device-property"
    
    res = f"products/{PRODUCT_ID}/devices/{DEVICE_NAME}"
    token = get_token(res)
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    body = {
        "product_id": PRODUCT_ID,
        "device_name": DEVICE_NAME,
        "params": params_dict
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # 记录日志
        if 'cmd_logs' not in st.session_state:
            st.session_state.cmd_logs = []
        
        timestamp = time.strftime("%H:%M:%S")
        
        if data.get("code") == 0:
            msg = t('command_success')
            st.session_state.cmd_logs.insert(0, f"[{timestamp}] ✅ {t('success_sent')}: {params_dict}")
            return True, msg
        else:
            msg = f"{t('api_error')}: {data.get('msg')}"
            st.session_state.cmd_logs.insert(0, f"[{timestamp}] ❌ {t('fail_sent')}: {params_dict} - {msg}")
            return False, msg
    except Exception as e:
        if 'cmd_logs' not in st.session_state:
            st.session_state.cmd_logs = []
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.cmd_logs.insert(0, f"[{timestamp}] ❌ {t('exception_sent')}: {params_dict} - {e}")
        return False, f"{t('request_failed')}: {e}"

# ==========================================
# Streamlit 页面逻辑
# ==========================================

st.set_page_config(
    page_title="IoT Console",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 状态初始化 ---
if 'language' not in st.session_state:
    st.session_state.language = 'zh'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# --- 黑夜模式 CSS ---
if st.session_state.dark_mode:
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        [data-testid="stSidebar"] {
            background-color: #262730;
            color: #FAFAFA;
        }
        .stMetric {
            background-color: #262730 !important;
            color: #FAFAFA !important;
            border: 1px solid #41444C;
        }
        h1, h2, h3, h4, h5, h6, p, label {
            color: #FAFAFA !important;
        }
        .stButton button {
            border-color: #41444C;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    # 浅色模式下的 Metric 样式
    st.markdown("""
        <style>
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

# --- 侧边栏设置 (全局) ---
# 无论是否登录，都在侧边栏提供语言和主题切换
with st.sidebar:
    st.subheader("⚙️ " + t('system_settings'))
    
    # 语言切换
    lang_options = {"中文": "zh", "English": "en"}
    current_lang_label = "中文" if st.session_state.language == "zh" else "English"
    selected_lang = st.selectbox(
        t('language_select'), 
        options=list(lang_options.keys()), 
        index=0 if st.session_state.language == 'zh' else 1
    )
    if lang_options[selected_lang] != st.session_state.language:
        st.session_state.language = lang_options[selected_lang]
        st.rerun()

    # 黑夜模式切换
    is_dark = st.toggle(t('dark_mode'), value=st.session_state.dark_mode)
    if is_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = is_dark
        st.rerun()
    
    st.divider()

# --- 登录认证 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .block-container {padding-top: 5rem;}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔒 " + t('login_title'))
        st.caption(t('default_account_hint'))
        
        with st.form("login_form"):
            username = st.text_input(t('username'))
            password = st.text_input(t('password'), type="password")
            submit = st.form_submit_button(t('login_button'), type="primary", use_container_width=True)
            
            if submit:
                if username == "admin" and password == "123456":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error(t('login_error'))
    
    st.stop()

st.title("☁️ " + t('app_title'))
st.caption(f"Product ID: {PRODUCT_ID} | Device: {DEVICE_NAME}")

# 初始化 Session State
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'history_data' not in st.session_state:
    st.session_state.history_data = []
if 'cmd_logs' not in st.session_state:
    st.session_state.cmd_logs = []

# --- 侧边栏：控制面板 ---
with st.sidebar:
    # 用户信息与注销
    with st.container():
        col_user, col_logout = st.columns([2, 1])
        with col_user:
            st.write(f"👤 **{t('admin_role')}**")
        with col_logout:
            if st.button(t('logout'), key="logout_btn", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    st.divider()

    st.header(f"🎮 {t('remote_control')}")
    
    # 1. 采集控制
    with st.expander(f"📡 {t('acquisition_control')}", expanded=True):
        col_sw1, col_sw2 = st.columns(2)
        with col_sw1:
            if st.button(f"▶️ {t('start')}", type="primary", use_container_width=True):
                success, msg = set_device_property({"enable": True})
                if success: st.toast(msg, icon="✅")
                else: st.toast(msg, icon="❌")
        with col_sw2:
            if st.button(f"⏹️ {t('stop')}", use_container_width=True):
                success, msg = set_device_property({"enable": False})
                if success: st.toast(msg, icon="✅")
                else: st.toast(msg, icon="❌")
    
    # 2. 参数设置
    with st.expander(f"⚙️ {t('parameter_settings')}", expanded=True):
        # PGA 设置
        pga_option = st.selectbox(t('pga_gain'), [1, 2, 64, 128], index=3)
        if st.button(t('apply_pga'), use_container_width=True):
            success, msg = set_device_property({"pga": pga_option})
            if success: 
                # PGA=xxx is universal, no need too much translation
                st.toast(f"{t('pga_sent')}{pga_option}", icon="✅")
                time.sleep(0.5)
            else: st.toast(msg, icon="❌")
            
        st.divider()
        
        # 采样率设置
        rate_map = {"10 Hz": 0, "40 Hz": 1, "640 Hz": 2, "1280 Hz": 3}
        rate_option = st.selectbox(t('sample_rate'), list(rate_map.keys()), index=0)
        if st.button(t('apply_sample_rate'), use_container_width=True):
            val = rate_map[rate_option]
            success, msg = set_device_property({"mode": val})
            if success: 
                st.toast(f"{t('mode_sent')}{val}", icon="✅")
                time.sleep(0.5)
            else: st.toast(msg, icon="❌")

    st.divider()
    
    # 3. 系统设置
    st.subheader(f"🛠️ {t('system_settings')}")
    # 自动刷新
    auto = st.toggle(t('auto_refresh'), value=st.session_state.auto_refresh)
    if auto:
        st.session_state.auto_refresh = True
    else:
        st.session_state.auto_refresh = False
        
    if st.button(f"🗑️ {t('clear_history')}", use_container_width=True):
        st.session_state.history_data = []
        st.rerun()
        
    if st.button(f"🧹 {t('clear_logs')}", use_container_width=True):
        st.session_state.cmd_logs = []
        st.rerun()


# --- 主页面逻辑 ---

# 获取最新数据
voltage_val, voltage_time = get_device_property("voltage")
pga_val, _ = get_device_property("pga")

# 数据处理与缓存
if voltage_val is not None:
    try:
        v_float = float(voltage_val)
        current_entry = {"time": time.strftime("%H:%M:%S"), "voltage": v_float}
        
        # 简单去重：如果时间和数值都一样，或者时间非常接近（这里只判断时间字符串）
        if not st.session_state.history_data or st.session_state.history_data[-1]["time"] != current_entry["time"]:
            st.session_state.history_data.append(current_entry)
    except:
        pass
    
    # 保持最近 50 个点
    if len(st.session_state.history_data) > 50:
        st.session_state.history_data.pop(0)

# 顶部指标栏
m1, m2, m3, m4 = st.columns(4)

with m1:
    try:
        v_display = f"{float(voltage_val):.4f} V" if voltage_val is not None else "--"
    except:
        v_display = f"{voltage_val} V" if voltage_val is not None else "--"
    st.metric(f"⚡ {t('current_voltage')}", v_display)

with m2:
    st.metric(f"🎚️ {t('current_pga')}", f"x{pga_val}" if pga_val is not None else "--")

with m3:
    # 计算最后更新时间
    if voltage_time:
        try:
            last_time = int(voltage_time) / 1000.0
            diff = time.time() - last_time
            if diff < 60:
                time_str = f"{diff:.0f} {t('seconds_ago')}"
            else:
                time_str = f"{diff/60:.0f} {t('minutes_ago')}"
        except:
            time_str = "--"
    else:
        time_str = "--"
    st.metric(f"🕒 {t('last_updated')}", time_str)

with m4:
    # 简单判断在线状态：如果最后更新时间在 5 分钟内，认为在线
    is_online = False
    if voltage_time:
        try:
            last_time = int(voltage_time) / 1000.0
            if time.time() - last_time < 300:
                is_online = True
        except:
            pass
            
    status = f"🟢 {t('online')}" if is_online else f"🔴 {t('offline_unknown')}"
    st.metric(f"📡 {t('device_status')}", status)

# 页面主体 Tabs
tab1, tab2, tab3 = st.tabs([f"📈 {t('realtime_monitor')}", f"📊 {t('data_details')}", f"📝 {t('operation_logs')}"])

with tab1:
    if st.session_state.history_data:
        df = pd.DataFrame(st.session_state.history_data)
        
        # 统计信息
        c1, c2, c3 = st.columns(3)
        c1.info(f"Max: {df['voltage'].max():.4f} V") # 'Max/Min/Avg' can be universally understood or translated if strict. I'll keep English/simple.
        c2.info(f"Min: {df['voltage'].min():.4f} V")
        c3.info(f"Avg: {df['voltage'].mean():.4f} V")
        
        # 图表
        y_min = df['voltage'].min() * 0.95
        y_max = df['voltage'].max() * 1.05
        if y_min == y_max:
            y_min -= 0.1
            y_max += 0.1

        chart = alt.Chart(df).mark_area(
            line={'color':'#FF4B4B'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#FF4B4B', offset=0),
                       alt.GradientStop(color='white', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('time', title='Time'),
            y=alt.Y('voltage', title='Voltage (V)', scale=alt.Scale(domain=[y_min, y_max])),
            tooltip=['time', 'voltage']
        ).properties(
            height=400
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info(t('no_history_data'))

with tab2:
    if st.session_state.history_data:
        df = pd.DataFrame(st.session_state.history_data)
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            f"📥 {t('download_csv')}",
            csv,
            "voltage_data.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info(t('no_data'))

with tab3:
    if st.session_state.cmd_logs:
        for log in st.session_state.cmd_logs:
            st.text(log)
    else:
        st.caption(t('no_logs'))

# 自动刷新触发
if st.session_state.auto_refresh:
    time.sleep(3)
    st.rerun()
