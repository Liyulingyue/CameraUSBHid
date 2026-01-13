import React from 'react';
import { Settings, Save, Camera, History, Zap } from 'lucide-react';

interface DashboardProps {
  stats: any;
  config: any;
  imageSrc: string;
  currentInstruction: string[];
  currentActions: string[];
  commands: any[];
  setCommands: (cmds: any) => void;
  updateConfig: (cfg: any) => void;
  setConfig: (cfg: any) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  stats, 
  config, 
  imageSrc, 
  currentInstruction,
  currentActions,
  commands, 
  setCommands, 
  updateConfig, 
  setConfig 
}) => {
  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">采集与监测</h1>
        </div>
      </header>

      {/* 第一行：算法参数（全宽） */}
      <div className="grid grid-cols-12 gap-8 mb-8">
        <div className="col-span-12">
          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center space-x-2 mb-6">
              <Settings className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-xl text-white">算法参数</h3>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">当前摄像头类型</label>
                  <select
                    value={config.camera_type || '72camera'}
                    onChange={(e) => updateConfig({ camera_type: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="72camera">72° 相机 (72camera)</option>
                    <option value="120width_camera">120° 横向畸变相机 (120width_camera)</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">目标设备 IP (UDP)</label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={config.target_ip}
                    onChange={(e) => setConfig({...config, target_ip: e.target.value})}
                    placeholder="192.168.1.5"
                    className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 flex-1 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => updateConfig({ target_ip: config.target_ip })}
                    className="p-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                  >
                    <Save className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-white">指令下发开关</h4>
                      <p className="text-xs text-slate-500">检测后自动映射为 HID 动作</p>
                    </div>
                    <button
                      onClick={() => updateConfig({ send_commands_enabled: !config.send_commands_enabled })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${config.send_commands_enabled ? 'bg-indigo-600' : 'bg-slate-700'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.send_commands_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-white">检测控制</h4>
                      <p className="text-xs text-slate-500">启用/停止姿态检测</p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => updateConfig({ detection_enabled: true })}
                        disabled={config.detection_enabled}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                          config.detection_enabled ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        }`}
                      >
                        开始检测
                      </button>
                      <button
                        onClick={() => updateConfig({ detection_enabled: false })}
                        disabled={!config.detection_enabled}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                          !config.detection_enabled ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-rose-600 hover:bg-rose-700 text-white'
                        }`}
                      >
                        停止检测
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* 第二行：图像与指令并排 */}
      <div className="grid grid-cols-12 gap-8 mb-8 items-stretch">
        <div className="col-span-12 lg:col-span-8">
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
        </div>

        <div className="col-span-12 lg:col-span-4">
          <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl relative h-full flex flex-col min-h-[300px]">
            <div className="absolute top-4 left-6 flex items-center space-x-2 opacity-50 z-10">
              <Zap className="w-5 h-5 text-amber-500" />
              <span className="text-sm font-bold uppercase tracking-wider text-slate-400">实时映射状态</span>
            </div>
            
            <div className="flex-1 flex flex-col h-full">
              {/* 上部分：动作名称 - 缩小比例 */}
              <div className="flex-[0.4] flex flex-col items-center justify-center p-4 bg-slate-900/50">
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Detected Actions / 识别动作</p>
                {currentActions && currentActions.length > 0 ? (
                  <div className="flex flex-wrap justify-center gap-2">
                    {currentActions.map((action, idx) => (
                      <span 
                        key={idx} 
                        className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-sm font-bold text-emerald-400 animate-in fade-in slide-in-from-bottom-1 duration-300"
                      >
                        {action}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-700 text-xs font-medium italic">Idle / 无动作</span>
                )}
              </div>

              {/* 分隔线 */}
              <div className="h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent"></div>

              {/* 下部分：对应按键 - 占据主要空间 */}
              <div className="flex-1 flex flex-col items-center justify-center p-6 bg-indigo-500/5">
                <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-500/60 mb-3">HID Commands / 执行按键</p>
                {currentInstruction && currentInstruction.length > 0 ? (
                  <div className="flex flex-wrap justify-center gap-6">
                    {currentInstruction.map((inst, idx) => (
                      <div key={idx} className="relative group">
                        <span className="text-8xl md:text-9xl font-black text-indigo-500 drop-shadow-[0_0_30px_rgba(99,102,241,0.4)] animate-in zoom-in duration-300">
                          {inst.toUpperCase()}
                        </span>
                        <div className="absolute inset-0 bg-indigo-500/15 blur-3xl -z-10 rounded-full scale-150" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-800 text-6xl font-black tracking-tighter opacity-10">---</span>
                )}
              </div>
            </div>

            {/* 背景修饰层 */}
            <div className="absolute -right-32 -bottom-32 w-64 h-64 bg-indigo-500/5 rounded-full blur-[80px] pointer-events-none" />
            <div className="absolute -left-32 -top-32 w-64 h-64 bg-emerald-500/5 rounded-full blur-[80px] pointer-events-none" />
          </section>
        </div>
      </div>

      {/* 第三行：日志（全宽） */}
      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12">
          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 flex flex-col h-64">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <History className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-white">指令输出记录</h3>
              </div>
              <button onClick={() => setCommands([])} className="text-xs text-slate-500 hover:text-white transition-colors">清除</button>
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
      </div>
    </div>
  );
};

export default Dashboard;
