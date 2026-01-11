import React, { useState } from 'react';
import { Settings, Zap } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const KeyDebug: React.FC = () => {
  const [config, setConfig] = useState({
    ip: '192.168.2.121',
    port: 80,
    commandType: 'keyboard', // 'keyboard' or 'mouse'
    command: 'a'
  });

  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    setIsSending(true);
    try {
      const response = await axios.post('/api/send_mouse', {
        url: config.ip,
        port: config.port,
        words: config.command
      });

      if (response.data.status === 'success') {
        toast.success(`发送成功: ${response.data.result}`);
      } else {
        toast.error(`发送失败: ${response.data.message}`);
      }
    } catch (error: any) {
      toast.error(`发送失败: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const handleReset = async () => {
    setIsSending(true);
    try {
      const response = await axios.post('/api/reset_hid', {
        url: config.ip,
        port: config.port
      });

      if (response.data.status === 'success') {
        toast.success('HID复位成功');
      } else {
        toast.error(`HID复位失败: ${response.data.message}`);
      }
    } catch (error: any) {
      toast.error(`HID复位失败: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const keyboardCommands = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'space', 'enter', 'backspace', 'tab', 'esc', 'left_shift', 'left_ctrl', 'left_alt',
    'up', 'down', 'left', 'right', 'f1', 'f2', 'f3', 'f4', 'f5'
  ];

  const mouseCommands = [
    'mouse_left_click', 'mouse_right_click', 'mouse_middle_click',
    'move_left', 'move_right', 'mouse_wheel_up', 'mouse_wheel_down', 'mouse_release'
  ];

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white">按键调试</h1>
        <p className="text-slate-400 mt-1">验证设备连通性和HID可执行性</p>
      </header>

      <div className="w-full">
        <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
          <div className="flex items-center space-x-2 mb-6">
            <Settings className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-xl text-white">HID调试配置</h3>
          </div>

          <div className="space-y-6">
            {/* IP和端口配置 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="md:col-span-2 lg:col-span-2">
                <label className="block text-sm font-medium text-slate-400 mb-2">目标IP地址</label>
                <input
                  type="text"
                  value={config.ip}
                  onChange={(e) => setConfig(prev => ({ ...prev, ip: e.target.value }))}
                  placeholder="192.168.2.121"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">端口</label>
                <input
                  type="number"
                  value={config.port}
                  onChange={(e) => setConfig(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                  placeholder="80"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* 命令类型选择 */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">命令类型</label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="commandType"
                    value="keyboard"
                    checked={config.commandType === 'keyboard'}
                    onChange={(e) => setConfig(prev => ({ ...prev, commandType: e.target.value }))}
                    className="mr-2"
                  />
                  <span className="text-white">键盘命令</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="commandType"
                    value="mouse"
                    checked={config.commandType === 'mouse'}
                    onChange={(e) => setConfig(prev => ({ ...prev, commandType: e.target.value }))}
                    className="mr-2"
                  />
                  <span className="text-white">鼠标命令</span>
                </label>
              </div>
            </div>

            {/* 命令选择和自定义输入 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">选择命令</label>
                <select
                  value={config.command}
                  onChange={(e) => setConfig(prev => ({ ...prev, command: e.target.value }))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {(config.commandType === 'keyboard' ? keyboardCommands : mouseCommands).map(cmd => (
                    <option key={cmd} value={cmd}>{cmd}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">或输入自定义命令</label>
                <input
                  type="text"
                  value={config.command}
                  onChange={(e) => setConfig(prev => ({ ...prev, command: e.target.value }))}
                  placeholder="输入自定义命令..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* 发送和复位按钮 */}
            <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={handleSend}
                disabled={isSending}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                <Zap className="w-5 h-5" />
                <span>{isSending ? '发送中...' : '发送HID命令'}</span>
              </button>
              
              <button
                onClick={handleReset}
                disabled={isSending}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-rose-600 hover:bg-rose-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                <Settings className="w-5 h-5" />
                <span>{isSending ? '复位中...' : '复位HID输出'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* 说明 */}
        <div className="mt-6 bg-slate-900 rounded-2xl border border-slate-800 p-6">
          <h3 className="font-bold text-lg text-white mb-4">使用说明</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-2 text-sm text-slate-400">
              <p>• 配置目标设备的IP地址和端口</p>
              <p>• 选择命令类型：键盘或鼠标</p>
              <p>• 从预设命令中选择，或输入自定义命令</p>
              <p>• 点击"发送HID命令"按钮测试设备连通性</p>
              <p>• <strong>重要：</strong>发送按键命令后，设备会持续输出直到复位</p>
            </div>
            <div className="space-y-2 text-sm text-slate-400">
              <p>• 点击"复位HID输出"按钮停止所有按键输出</p>
              <p>• 鼠标命令示例：mouse_left_click (左键按下), move_left (左移)</p>
              <p>• 键盘命令支持字母、数字、功能键和控制键</p>
              <p>• 自定义命令可输入任意支持的命令字符串</p>
              <p>• 发送结果会在右上角显示Toast提示</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KeyDebug;