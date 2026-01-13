import React from 'react';
import { Camera, Activity, MousePointer2, History, Zap, Settings } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  fps: number;
  latency: number;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, fps, latency }) => {
  const menuItems = [
    { id: 'realtime', label: '采集与监测', icon: Activity },
    { id: 'recorder', label: '姿态录制', icon: History },
    { id: 'keydebug', label: '按键调试', icon: Zap },
    { id: 'poseconfig', label: '姿态配置', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-4 space-y-2">
      <div 
        onClick={() => setActiveTab('home')}
        className="flex items-center space-x-2 px-2 py-4 mb-4 cursor-pointer hover:opacity-80 transition-all"
      >
        <Camera className="w-8 h-8 text-indigo-500" />
        <span className="text-xl font-bold tracking-tight text-white">CameraHID</span>
      </div>

      <nav className="space-y-1">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === item.id 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' 
                : 'hover:bg-slate-800 text-slate-400'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto pt-4 border-t border-slate-800">
        <div className="px-2 py-2">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">系统状态</div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">FPS</span>
            <span className="font-mono text-indigo-400">{fps}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-slate-400">延迟</span>
            <span className="font-mono text-indigo-400">{Math.round(latency)}ms</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
