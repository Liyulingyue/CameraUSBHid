import React from 'react';
import { History, Play, Save, Trash2 } from 'lucide-react';

const PoseRecorder: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white">姿态录制</h1>
        <p className="text-slate-400 mt-1">采集并录制人体关键点姿态数据</p>
      </header>

      <div className="grid grid-cols-3 gap-8">
        <div className="col-span-2">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-xl text-white">实时数据流</h3>
              <div className="flex space-x-2">
                <button className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors">
                  <Play className="w-4 h-4 fill-current" />
                  <span>开始录制</span>
                </button>
                <button className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  <span>导出 JSON</span>
                </button>
              </div>
            </div>
            
            <div className="aspect-video bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center text-slate-700 font-mono">
              [ 等待录制信号 ... ]
            </div>
          </div>
        </div>

        <div className="col-span-1">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 h-full">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <History className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-white">录制队列</h3>
              </div>
              <button className="text-slate-500 hover:text-rose-400">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 bg-slate-950 rounded-lg border border-slate-800/50 flex justify-between items-center group">
                  <div>
                    <p className="text-sm font-medium text-white">Pose_Sample_{i}.json</p>
                    <p className="text-xs text-slate-500">2026-01-11 14:0{i}:21 | 120 Frames</p>
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-all">
                    下载
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PoseRecorder;
