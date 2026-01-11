import React from 'react';
import { MousePointer2, Settings, AlertTriangle } from 'lucide-react';

const MouseControl: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white">远程控制</h1>
        <p className="text-slate-400 mt-1">基于手势的鼠标模拟与键盘控制系统</p>
      </header>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-12 flex flex-col items-center justify-center text-center space-y-6">
            <div className="w-24 h-24 bg-indigo-500/10 rounded-full flex items-center justify-center">
              <MousePointer2 className="w-12 h-12 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">手势交互面板</h2>
              <p className="text-slate-500 mt-2 max-w-md">此处将展示手势与鼠标动作的映射配置。您可以通过预设的手势来控制远程设备的鼠标移动、点击以及滚动操作。</p>
            </div>
            <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-full font-bold transition-all shadow-lg shadow-indigo-900/20">
              配置映射关系
            </button>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-8">
          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center space-x-2 mb-6">
              <Settings className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-xl text-white">控制设置</h3>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                <p className="text-sm text-slate-400">灵敏度调节</p>
                <input type="range" className="w-full mt-2" />
              </div>
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                <p className="text-sm text-slate-400">平滑因子</p>
                <input type="range" className="w-full mt-2" />
              </div>
            </div>
          </section>

          <section className="bg-amber-950/20 border border-amber-900/30 rounded-2xl p-6">
            <div className="flex items-start space-x-3 text-amber-300">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <div className="text-sm">
                <p className="font-bold mb-1">注意事项</p>
                <p className="opacity-80">使用远程控制前请确保下位机已正确连接至 HID 模拟接口。</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default MouseControl;
