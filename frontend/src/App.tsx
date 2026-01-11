import { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';
import { Toaster, toast } from 'react-hot-toast';

// Components & Pages
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import MouseControl from './pages/MouseControl';
import PoseRecorder from './pages/PoseRecorder';
import KeyDebug from './pages/KeyDebug';

// 基础配置
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';

export interface Stats {
  fps: number;
  detections: number;
  inference_time: number;
  is_running: boolean;
  current_fps: number;
}

export interface Config {
  confidence_threshold: number;
  send_commands_enabled: boolean;
  detection_enabled: boolean;
  fps_limit: number;
  target_ip: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'realtime' | 'mouse' | 'recorder' | 'keydebug'>('home');
  const [stats, setStats] = useState<Stats>({ fps: 0, detections: 0, inference_time: 0, is_running: false, current_fps: 0 });
  const [config, setConfig] = useState<Config>({ 
    confidence_threshold: 0.5, 
    send_commands_enabled: false, 
    detection_enabled: false,
    fps_limit: 30, 
    target_ip: '' 
  });
  const [commands, setCommands] = useState<any[]>([]);
  const [imageSrc, setImageSrc] = useState<string>('');
  const [currentInstruction, setCurrentInstruction] = useState<string[]>([]);
  const [currentActions, setCurrentActions] = useState<string[]>([]);
  
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
      if (data.fps !== undefined) {
        setStats(prev => ({ ...prev, fps: data.fps, inference_time: data.stats?.inference_time || 0 }));
      }
      setCurrentInstruction(data.instruction || []);
      setCurrentActions(data.state || []);
    });

    socketRef.current.on('stats', (data: Stats) => {
      setStats(prev => ({ ...prev, ...data }));
    });

    socketRef.current.on('config_updated', (data: Partial<Config>) => {
      setConfig(prev => ({ ...prev, ...data }));
    });

    socketRef.current.on('new_command', (cmd: any) => {
      setCommands(prev => [cmd, ...prev].slice(0, 50));
    });

    socketRef.current.on('error', (err: any) => {
      toast.error(err.message);
    });

    // 定时获取状态
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
      const res = await axios.post(`${BACKEND_URL}/api/config`, newConfig);
      if (res.status === 200) {
        setConfig(prev => ({ ...prev, ...newConfig }));
        toast.success('设置已更新');
      }
    } catch (e: any) {
      toast.error(e.response?.data?.message || '更新失败');
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-200 font-sans">
      <Toaster position="top-right" />
      
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        fps={stats.fps} 
        latency={stats.inference_time} 
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        {activeTab === 'home' && <Home onStart={() => setActiveTab('realtime')} />}

        {activeTab === 'realtime' && (
          <Dashboard 
            stats={stats}
            config={config}
            imageSrc={imageSrc}
            currentInstruction={currentInstruction}
            currentActions={currentActions}
            commands={commands}
            setCommands={setCommands}
            updateConfig={updateConfig}
            setConfig={setConfig}
          />
        )}

        {activeTab === 'mouse' && <MouseControl />}
        
        {activeTab === 'recorder' && <PoseRecorder />}

        {activeTab === 'keydebug' && <KeyDebug />}
      </main>
    </div>
  );
}

export default App;
