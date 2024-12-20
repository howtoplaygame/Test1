from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'config_file' not in request.files:
        return jsonify({'error': '没有上传文件'})
        
    file = request.files['config_file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'})
        
    if file:
        content = file.read().decode('utf-8')
        config_structure = parse_config(content)
        return render_template('result.html', config=config_structure)

if __name__ == '__main__':
    app.run(debug=True) 