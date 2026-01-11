import React from 'react';
import { Camera, Cpu, Zap, Shield, Github, ArrowRight, History } from 'lucide-react';

interface HomeProps {
  onStart: () => void;
}

const Home: React.FC<HomeProps> = ({ onStart }) => {
  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto custom-scrollbar">
      <div className="max-w-4xl mx-auto py-12">
        {/* Hero Section */}
        <section className="text-center mb-20">
          <div className="inline-flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full mb-6">
            <Zap className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">RDK X5 Powered</span>
          </div>
          <h1 className="text-5xl font-extrabold text-white mb-6 leading-tight">
            CameraUSB <span className="text-indigo-500">HID</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            基于 RDK X5 的人体姿态检测与远程设备交互系统。通过 AI 加速实现高实时性的手势控制与 HID 模拟。
          </p>
          <div className="flex justify-center space-x-4 mt-10">
            <button 
              onClick={onStart}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-full font-bold transition-all shadow-lg shadow-indigo-900/40 flex items-center space-x-2"
            >
              <span>快速开始</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="bg-slate-800 hover:bg-slate-700 text-white px-8 py-3 rounded-full font-bold transition-all flex items-center space-x-2">
              <Github className="w-4 h-4" />
              <span>GitHub</span>
            </a>
          </div>
        </section>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Camera className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">实时姿态检测</h3>
            <p className="text-slate-400 leading-relaxed">
              利用 RDK X5 的 BPU 硬件加速，实现亚毫秒级的推理延迟，支持 17 个关键点的人体姿态追踪。
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Cpu className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">HID 指令模拟</h3>
            <p className="text-slate-400 leading-relaxed">
              将人体姿态即时编码为 USB 键盘与鼠标协议，实现对远程主机的无感知操作。
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 bg-rose-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <History className="w-6 h-6 text-rose-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">姿态录制与分析</h3>
            <p className="text-slate-400 leading-relaxed">
              支持一键采集姿态数据序列，方便离线分析或用于自定义动作训练。
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Shield className="w-6 h-6 text-amber-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">安全与稳定性</h3>
            <p className="text-slate-400 leading-relaxed">
              系统集成了自动心跳监测与 HID 冗余保护，确保在网络异常时自动发送停止命令。
            </p>
          </div>
        </div>

        {/* Project Context */}
        <section className="bg-indigo-600/10 border border-indigo-500/20 rounded-3xl p-10 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">关于项目</h2>
          <p className="text-slate-300 leading-relaxed mb-0">
            这是基于地平线 RDK X5 开发套件构建的完整端到端方案。
            前端采用 React + TailwindCSS 构建，后端通过 Flask 与 Socket.IO 实现高效的数据传输与硬件控制。
          </p>
        </section>
      </div>
    </div>
  );
};

export default Home;
