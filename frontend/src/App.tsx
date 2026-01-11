import { useState, useEffect, useRef } from 'react';
import { 
  Camera, 
  Settings, 
  History, 
  Activity, 
  MousePointer2, 
  Play, 
  Square, 
  Save, 
  AlertTriangle
} from 'lucide-react';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';

// 基础配置
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';

interface Stats {
  fps: number;
  detections: number;
  inference_time: number;
  is_running: boolean;
}

interface Config {
  confidence_threshold: number;
  send_commands_enabled: boolean;
  fps_limit: number;
  target_ip: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'realtime' | 'mouse' | 'recorder'>('realtime');
  const [stats, setStats] = useState<Stats>({ fps: 0, detections: 0, inference_time: 0, is_running: false });
  const [config, setConfig] = useState<Config>({ 
    confidence_threshold: 0.5, 
    send_commands_enabled: false, 
    fps_limit: 30, 
    target_ip: '' 
  });
  const [commands, setCommands] = useState<any[]>([]);
  const [imageSrc, setImageSrc] = useState<string>('');
  
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // 初始化 Socket.IO
    socketRef.current = io(BACKEND_URL);

    socketRef.current.on('connect', () => {
      toast.success('已连接至后端服务');
    });

    socketRef.current.on('frame_update', (data: any) => {
      if (data.image) {
        setImageSrc(`data:image/jpeg;base64,${data.image}`);
      }
      if (data.fps) {
        setStats(prev => ({ ...prev, fps: data.fps, inference_time: data.stats?.inference_time || 0 }));
      }
    });

    socketRef.current.on('stats', (data: Stats) => {
      setStats(data);
    });

    socketRef.current.on('new_command', (cmd: any) => {
      setCommands(prev => [cmd, ...prev].slice(0, 50));
    });

    socketRef.current.on('error', (err: any) => {
      toast.error(err.message);
    });

    // 定时获取配置和状态
    fetchConfig();
    const interval = setInterval(fetchStats, 1000);

    return () => {
      socketRef.current?.disconnect();
      clearInterval(interval);
    };
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/config`);
      setConfig(res.data);
    } catch (e) {
      console.error('获取配置失败', e);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/stats`);
      setStats(prev => ({ ...prev, ...res.data }));
    } catch (e) {
      // 忽略失败
    }
  };

  const updateConfig = async (newConfig: Partial<Config>) => {
    try {
      await axios.post(`${BACKEND_URL}/api/config`, newConfig);
      setConfig(prev => ({ ...prev, ...newConfig }));
      toast.success('设置已更新');
    } catch (e) {
      toast.error('更新失败');
    }
  };

  const toggleCamera = () => {
    if (stats.is_running) {
      socketRef.current?.emit('stop_camera');
    } else {
      socketRef.current?.emit('start_camera');
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-200 font-sans">
      <Toaster position="top-right" />
      
      {/* 侧边栏 */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-4 space-y-2">
        <div className="flex items-center space-x-2 px-2 py-4 mb-4">
          <Camera className="w-8 h-8 text-indigo-500" />
          <span className="text-xl font-bold tracking-tight">CameraHID</span>
        </div>

        <button 
          onClick={() => setActiveTab('realtime')}
          className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'realtime' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
        >
          <Activity className="w-5 h-5" />
          <span>采集与监测</span>
        </button>

        <button 
          onClick={() => setActiveTab('mouse')}
          className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'mouse' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
        >
          <MousePointer2 className="w-5 h-5" />
          <span>远程控制</span>
        </button>

        <button 
          onClick={() => setActiveTab('recorder')}
          className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'recorder' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
        >
          <History className="w-5 h-5" />
          <span>姿态录制</span>
        </button>

        <div className="mt-auto pt-4 border-t border-slate-800">
          <div className="px-2 py-2">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">系统状态</div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">FPS</span>
              <span className="font-mono text-indigo-400">{stats.fps}</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-slate-400">延迟</span>
              <span className="font-mono text-indigo-400">{Math.round(stats.inference_time)}ms</span>
            </div>
          </div>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">仪表盘</h1>
            <p className="text-slate-400 mt-1">
              {activeTab === 'realtime' ? '实时人体姿态检测与系统指标' : 
               activeTab === 'mouse' ? '基于手势的鼠标模拟控制' : '人体关键点数据序列采集'}
            </p>
          </div>
          <div className="flex space-x-3">
            <button 
              onClick={toggleCamera}
              className={`flex items-center space-x-2 px-6 py-2.5 rounded-full font-semibold transition-all shadow-lg ${
                stats.is_running 
                ? 'bg-rose-500 hover:bg-rose-600 text-white shadow-rose-900/20' 
                : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-900/20'
              }`}
            >
              {stats.is_running ? <><Square className="w-4 h-4 fill-current" /><span>停止监测</span></> : <><Play className="w-4 h-4 fill-current" /><span>开始监测</span></>}
            </button>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-8">
          {/* 视频流预览 */}
          <div className="col-span-12 lg:col-span-8 space-y-8">
            <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl relative aspect-video flex items-center justify-center bg-black">
              {imageSrc ? (
                <img src={imageSrc} className="w-full h-full object-contain" alt="Stream Preview" />
              ) : (
                <div className="flex flex-col items-center text-slate-600">
                  <Camera className="w-16 h-16 mb-4 animate-pulse" />
                  <p>等待摄像头信号...</p>
                </div>
              )}
              {stats.is_running && (
                <div className="absolute top-4 left-4 flex items-center space-x-2 bg-slate-950/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                  <div className="w-2.5 h-2.5 bg-rose-500 rounded-full animate-ping" />
                  <span className="text-xs font-bold text-white uppercase tracking-widest">Live</span>
                </div>
              )}
            </section>

            {/* 控制终端 / 历史记录 */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 flex flex-col h-64">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <History className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-bold">指令输出记录</h3>
                </div>
                <button onClick={() => setCommands([])} className="text-xs text-slate-500 hover:text-white">清除</button>
              </div>
              <div className="flex-1 overflow-y-auto font-mono text-sm space-y-1 custom-scrollbar">
                {commands.length === 0 ? (
                  <p className="text-slate-600 italic">暂无检测结果或指令下发...</p>
                ) : (
                  commands.map((cmd, i) => (
                    <div key={i} className="flex space-x-4 py-1 border-b border-slate-800/50">
                      <span className="text-slate-500 shrink-0">[{new Date(cmd.timestamp * 1000).toLocaleTimeString()}]</span>
                      <span className={cmd.type === 'command' ? 'text-emerald-400' : 'text-slate-300'}>
                        {cmd.message || JSON.stringify(cmd.data)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>

          {/* 快速设置面板 */}
          <div className="col-span-12 lg:col-span-4 space-y-8">
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl">
              <div className="flex items-center space-x-2 mb-6">
                <Settings className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-xl">算法参数</h3>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm font-medium text-slate-400">置信度阈值</label>
                    <span className="text-sm font-mono text-indigo-400">{config.confidence_threshold}</span>
                  </div>
                  <input 
                    type="range" min="0" max="1" step="0.05" 
                    value={config.confidence_threshold}
                    onChange={(e) => updateConfig({ confidence_threshold: parseFloat(e.target.value) })}
                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm font-medium text-slate-400">FPS 上限</label>
                    <span className="text-sm font-mono text-indigo-400">{config.fps_limit}</span>
                  </div>
                  <input 
                    type="range" min="1" max="60" step="1" 
                    value={config.fps_limit}
                    onChange={(e) => updateConfig({ fps_limit: parseInt(e.target.value) })}
                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                </div>

                <div className="pt-4 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">指令下发开关</h4>
                      <p className="text-xs text-slate-500">检测后自动映射为 HID 动作</p>
                    </div>
                    <button 
                      onClick={() => updateConfig({ send_commands_enabled: !config.send_commands_enabled })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${config.send_commands_enabled ? 'bg-indigo-600' : 'bg-slate-700'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.send_commands_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>
                </div>

                <div className="pt-4">
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">目标设备 IP (UDP)</label>
                  <div className="flex space-x-2">
                    <input 
                      type="text" 
                      value={config.target_ip}
                      onChange={(e) => setConfig({...config, target_ip: e.target.value})}
                      placeholder="192.168.1.5"
                      className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 flex-1 text-sm focus:outline-none focus:border-indigo-500"
                    />
                    <button 
                      onClick={() => updateConfig({ target_ip: config.target_ip })}
                      className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </section>

            {/* 警告/消息提示 */}
            <section className="bg-indigo-950/20 border border-indigo-900/30 rounded-2xl p-6">
              <div className="flex items-start space-x-3 text-indigo-300">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <div className="text-sm">
                  <p className="font-bold mb-1">提示</p>
                  <p className="opacity-80">当前正在使用 RDK X5 的 BPU 加速进行推理。</p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
