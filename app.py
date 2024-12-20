from flask import Flask, render_template, request, jsonify
import re
import os
import time
from datetime import datetime

app = Flask(__name__)
# 设置最大文件大小为1MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

# 确保data目录存在
data_dir = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def parse_config(config_text):
    """解析Aruba配置文件"""
    config_dict = {}
    current_ap_group = None
    current_profile_type = None
    
    # 先解析所有profile配置
    virtual_ap_configs = {}
    ssid_profile_configs = {}
    aaa_profile_configs = {}
    dot11a_radio_configs = {}
    dot11g_radio_configs = {}
    ap_system_configs = {}
    regulatory_domain_configs = {}
    iot_radio_configs = {}
    dot11_6ghz_configs = {}
    
    # 先解析ssid-profile和aaa-profile配置
    lines = config_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('wlan ssid-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                ssid_profile_configs[profile_name] = commands
                i = j
        elif line.startswith('aaa profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                aaa_profile_configs[profile_name] = commands
                i = j
        i += 1

    # 解析virtual-ap配置
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('wlan virtual-ap'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                ssid_name = None
                aaa_name = None
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        if current_line.startswith('ssid-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                ssid_name = parts[1]
                        elif current_line.startswith('aaa-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                aaa_name = parts[1]
                        else:
                            commands.append(current_line)
                    j += 1
                virtual_ap_configs[profile_name] = {
                    'commands': commands,
                    'ssid_profile': {
                        'name': ssid_name,
                        'commands': ssid_profile_configs.get(ssid_name, [])
                    } if ssid_name else None,
                    'aaa_profile': {
                        'name': aaa_name,
                        'commands': aaa_profile_configs.get(aaa_name, [])
                    } if aaa_name else None
                }
                i = j
        elif line.startswith('rf dot11a-radio-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                dot11a_radio_configs[profile_name] = commands
                i = j
        elif line.startswith('rf dot11g-radio-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                dot11g_radio_configs[profile_name] = commands
                i = j
        elif line.startswith('ap system-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                ap_system_configs[profile_name] = commands
                i = j
        elif line.startswith('ap regulatory-domain-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                regulatory_domain_configs[profile_name] = commands
                i = j
        elif line.startswith('iot radio-profile') or line.startswith('ap regulatory-domain-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                # 合并iot radio-profile的配置
                if profile_name in iot_radio_configs:
                    iot_radio_configs[profile_name].extend(commands)
                else:
                    iot_radio_configs[profile_name] = commands
                i = j
        elif line.startswith('rf dot11-6GHz-radio-profile'):
            parts = line.split('"')
            if len(parts) >= 2:
                profile_name = parts[1]
                commands = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        commands.append(current_line)
                    j += 1
                dot11_6ghz_configs[profile_name] = commands
                i = j
        i += 1

    # 解析ap-group配置
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('ap-group'):
            parts = line.split('"')
            if len(parts) >= 2:
                group_name = parts[1]
                current_ap_group = group_name
                if current_ap_group not in config_dict:
                    config_dict[current_ap_group] = {
                        'profiles': {},
                        'commands': []
                    }
                
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('!'):
                    current_line = lines[j].strip()
                    if current_line:
                        is_profile = False
                        # 检查是否是profile引用
                        if current_line.startswith('virtual-ap'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'virtual-ap' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['virtual-ap'] = {}
                                
                                vap_config = virtual_ap_configs.get(profile_name, {
                                    'commands': [],
                                    'ssid_profile': None,
                                    'aaa_profile': None
                                })
                                
                                vap_entry = {
                                    'commands': vap_config['commands'],
                                    'ssid_profile': vap_config['ssid_profile'],
                                    'aaa_profile': vap_config['aaa_profile']
                                }
                                
                                config_dict[current_ap_group]['profiles']['virtual-ap'][profile_name] = vap_entry
                            is_profile = True
                        elif current_line.startswith('dot11a-radio-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'dot11a-radio-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['dot11a-radio-profile'] = {}
                                config_dict[current_ap_group]['profiles']['dot11a-radio-profile'][profile_name] = {
                                    'commands': dot11a_radio_configs.get(profile_name, [])
                                }
                            is_profile = True
                        elif current_line.startswith('dot11g-radio-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'dot11g-radio-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['dot11g-radio-profile'] = {}
                                config_dict[current_ap_group]['profiles']['dot11g-radio-profile'][profile_name] = {
                                    'commands': dot11g_radio_configs.get(profile_name, [])
                                }
                            is_profile = True
                        elif current_line.startswith('ap-system-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'ap-system-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['ap-system-profile'] = {}
                                config_dict[current_ap_group]['profiles']['ap-system-profile'][profile_name] = {
                                    'commands': ap_system_configs.get(profile_name, [])
                                }
                            is_profile = True
                        elif current_line.startswith('regulatory-domain-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'regulatory-domain-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['regulatory-domain-profile'] = {}
                                config_dict[current_ap_group]['profiles']['regulatory-domain-profile'][profile_name] = {
                                    'commands': regulatory_domain_configs.get(profile_name, [])
                                }
                            is_profile = True
                        elif current_line.startswith('iot radio-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'iot radio-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['iot radio-profile'] = {}
                                config_dict[current_ap_group]['profiles']['iot radio-profile'][profile_name] = {
                                    'commands': iot_radio_configs.get(profile_name, [])
                                }
                            is_profile = True
                        elif current_line.startswith('dot11-6GHz-radio-profile'):
                            parts = current_line.split('"')
                            if len(parts) >= 2:
                                profile_name = parts[1]
                                if 'dot11-6GHz-radio-profile' not in config_dict[current_ap_group]['profiles']:
                                    config_dict[current_ap_group]['profiles']['dot11-6GHz-radio-profile'] = {}
                                config_dict[current_ap_group]['profiles']['dot11-6GHz-radio-profile'][profile_name] = {
                                    'commands': dot11_6ghz_configs.get(profile_name, [])
                                }
                            is_profile = True
                        
                        if not is_profile:
                            config_dict[current_ap_group]['commands'].append(current_line)
                    j += 1
                i = j
        i += 1
    
    return config_dict

def get_counter():
    """获取处理次数"""
    counter_file = os.path.join('templates', 'counters')
    try:
        with open(counter_file, 'r') as f:
            return int(f.read().strip() or '0')
    except (FileNotFoundError, ValueError):
        return 0

def increment_counter():
    """增加处理次数并保存"""
    counter_file = os.path.join('templates', 'counters')
    try:
        counter = get_counter() + 1
        with open(counter_file, 'w') as f:
            f.write(str(counter))
        return counter
    except Exception:
        return 0

def save_content(content):
    """保存内容到data目录，使用时间戳作为文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}.log"
    filepath = os.path.join(data_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return None

@app.route('/')
def index():
    counter = get_counter()
    return render_template('index.html', counter=counter)

@app.route('/upload', methods=['POST'])
def upload_file():
    content = None
    
    # Handle file upload
    if 'config_file' in request.files:
        file = request.files['config_file']
        if file.filename != '':
            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > 1024 * 1024:  # 1MB = 1024 * 1024 bytes
                return jsonify({'error': 'File size cannot exceed 1MB'})
            
            try:
                content = file.read().decode('utf-8')
            except UnicodeDecodeError:
                return jsonify({'error': 'Unsupported file format, please upload a text file'})
    
    # Handle pasted text
    elif 'config_text' in request.form:
        content = request.form['config_text']
        if not content.strip():
            return jsonify({'error': 'Configuration content cannot be empty'})
    
    if not content:
        return jsonify({'error': 'Please upload a file or paste configuration content'})
    
    # 保存内容到文件
    save_content(content)
    
    # 增加处理次数
    increment_counter()
    
    config_structure = parse_config(content)
    return render_template('result.html', config=config_structure)

if __name__ == '__main__':
    app.run(debug=True) 