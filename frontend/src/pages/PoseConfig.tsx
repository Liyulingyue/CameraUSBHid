import React, { useState, useEffect, useRef } from 'react';
import { Settings, Eye, Edit3, Save, X, Key } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface PoseConfig {
  name: string;
  index: number;
  inner_flag: boolean;
  similarity_threshold: number;
  keys: string[];
  basekeypoints: string;
  list_corekeypoints: string[];
  value_dict: { [key: string]: number[] };
  pose_img: string;
}

const PoseConfig: React.FC = () => {
  const [poseConfigs, setPoseConfigs] = useState<PoseConfig[]>([]);
  const [selectedPose, setSelectedPose] = useState<PoseConfig | null>(null);
  const [editingKeys, setEditingKeys] = useState<string[]>([]);
  const [editingPose, setEditingPose] = useState<PoseConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 格式化按键显示名称
  const formatKeyDisplay = (key: string): string => {
    const keyMap: { [key: string]: string } = {
      'enter': 'ENTER',
      'space': 'SPACE',
      'backspace': 'BKSP',
      'tab': 'TAB',
      'escape': 'ESC',
      'shift': 'SHIFT',
      'ctrl': 'CTRL',
      'alt': 'ALT',
      'up': '↑',
      'down': '↓',
      'left': '←',
      'right': '→',
      'home': 'HOME',
      'end': 'END',
      'pageup': 'PGUP',
      'pagedown': 'PGDN',
      'insert': 'INS',
      'delete': 'DEL',
      // 鼠标按键
      'mouse_left_click': '鼠标左键',
      'mouse_right_click': '鼠标右键',
      'mouse_middle_click': '鼠标中键',
      'mouse_wheel_up': '滚轮上',
      'mouse_wheel_down': '滚轮下',
      'move_left': '鼠标左移',
      'move_right': '鼠标右移',
      'mouse_release': '鼠标释放'
    };
    
    return keyMap[key] || key.toUpperCase();
  };

  // 可选按键列表
  const availableKeys = [
    // 字母键
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    // 数字键
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    // 功能键
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    // 控制键
    'enter', 'space', 'backspace', 'tab', 'escape', 'shift', 'ctrl', 'alt',
    // 方向键
    'up', 'down', 'left', 'right',
    // 其他常用键
    'home', 'end', 'pageup', 'pagedown', 'insert', 'delete',
    // 鼠标按键
    'mouse_left_click', 'mouse_right_click', 'mouse_middle_click',
    // 鼠标滚轮
    'mouse_wheel_up', 'mouse_wheel_down',
    // 鼠标移动
    'move_left', 'move_right',
    // 鼠标释放
    'mouse_release'
  ];

  // 绘制关键点函数
  const drawKeypoints = (pose: PoseConfig) => {
    const canvas = canvasRef.current;
    if (!canvas || !pose.value_dict) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸与容器匹配
    const container = canvas.parentElement;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }

    // 清空画布并绘制背景
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制渐变背景
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#1e293b');
    gradient.addColorStop(1, '#0f172a');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 获取基准关键点坐标
    const baseKeypoint = pose.basekeypoints;
    let baseX = canvas.width / 2;
    let baseY = canvas.height / 2;

    // 计算所有关键点的坐标
    const keypointPositions: { [key: string]: { x: number; y: number } } = {};
    
    Object.entries(pose.value_dict).forEach(([keypointName, coords]) => {
      if (coords && coords.length >= 2) {
        const [offsetX, offsetY] = coords;
        
        // 将相对坐标转换为画布坐标
        const scale = Math.min(canvas.width, canvas.height) / 500; // 调整缩放因子
        const canvasX = baseX + offsetX * scale * 0.8;
        const canvasY = baseY - offsetY * scale * 0.8;

        // 确保坐标在画布范围内
        const clampedX = Math.max(20, Math.min(canvas.width - 20, canvasX));
        const clampedY = Math.max(20, Math.min(canvas.height - 20, canvasY));
        
        keypointPositions[keypointName] = { x: clampedX, y: clampedY };
      }
    });

    // 定义骨架连接关系
    const skeletonConnections = [
      // 右臂
      ['right_shoulder', 'right_elbow'],
      ['right_elbow', 'right_wrist'],
      // 左臂
      ['left_shoulder', 'left_elbow'],
      ['left_elbow', 'left_wrist'],
      // 其他可能的连接
      ['nose', 'right_shoulder'],
      ['nose', 'left_shoulder'],
      ['right_shoulder', 'right_hip'],
      ['left_shoulder', 'left_hip'],
      ['right_hip', 'left_hip'],
      ['right_hip', 'right_knee'],
      ['right_knee', 'right_ankle'],
      ['left_hip', 'left_knee'],
      ['left_knee', 'left_ankle'],
    ];

    // 绘制骨架连接线
    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    
    skeletonConnections.forEach(([start, end]) => {
      const startPos = keypointPositions[start];
      const endPos = keypointPositions[end];
      
      if (startPos && endPos) {
        ctx.beginPath();
        ctx.moveTo(startPos.x, startPos.y);
        ctx.lineTo(endPos.x, endPos.y);
        ctx.stroke();
      }
    });

    // 绘制核心关键点连接线（高亮）
    if (pose.list_corekeypoints && pose.list_corekeypoints.length > 1) {
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 4;
      ctx.setLineDash([8, 4]);
      
      for (let i = 0; i < pose.list_corekeypoints.length - 1; i++) {
        const current = pose.list_corekeypoints[i];
        const next = pose.list_corekeypoints[i + 1];
        
        const startPos = keypointPositions[current];
        const endPos = keypointPositions[next];
        
        if (startPos && endPos) {
          ctx.beginPath();
          ctx.moveTo(startPos.x, startPos.y);
          ctx.lineTo(endPos.x, endPos.y);
          ctx.stroke();
        }
      }
      
      ctx.setLineDash([]); // 恢复实线
    }

    // 绘制关键点
    Object.entries(keypointPositions).forEach(([keypointName, pos]) => {
      const isBase = keypointName === baseKeypoint;
      const isCore = pose.list_corekeypoints?.includes(keypointName);
      
      // 绘制关键点阴影
      ctx.beginPath();
      ctx.arc(pos.x + 1, pos.y + 1, 8, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
      ctx.fill();
      
      // 绘制关键点
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
      
      if (isBase) {
        ctx.fillStyle = '#10b981'; // 基准点 - 绿色
      } else if (isCore) {
        ctx.fillStyle = '#f59e0b'; // 核心点 - 琥珀色
      } else {
        ctx.fillStyle = '#ef4444'; // 其他点 - 红色
      }
      ctx.fill();
      
      // 绘制关键点边框
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // 绘制关键点名称
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 11px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      const label = keypointName.replace(/_/g, ' ').replace(/^(left|right)/i, (match) => match.toUpperCase());
      ctx.fillText(label, pos.x, pos.y - 12);
    });

    // 添加标题
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(pose.name, canvas.width / 2, 20);

    // 添加说明文字
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('绿色: 基准关键点 | 琥珀色: 核心关键点 | 红色: 其他关键点', canvas.width / 2, canvas.height - 20);
  };

  // 当选择姿态改变时，绘制关键点
  useEffect(() => {
    if (selectedPose) {
      // 直接绘制姿态骨架
      drawKeypoints(selectedPose);
    }
  }, [selectedPose]);

  useEffect(() => {
    loadPoseConfigs();
  }, []);

  const loadPoseConfigs = async () => {
    try {
      const response = await axios.get('/api/pose_configs');
      setPoseConfigs(response.data);
    } catch (error) {
      toast.error('加载姿态配置失败');
      console.error('加载姿态配置失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditKeys = (pose: PoseConfig) => {
    setEditingPose(pose);
    setEditingKeys([...pose.keys]);
  };

  const handleSaveKeys = async () => {
    if (!editingPose) return;

    setIsSaving(true);
    try {
      await axios.post('/api/update_pose_keys', {
        name: editingPose.name,
        keys: editingKeys
      });

      // 更新本地状态
      setPoseConfigs(prev => prev.map(p =>
        p.name === editingPose.name ? { ...p, keys: [...editingKeys] } : p
      ));

      // 如果当前选中的姿态是正在编辑的姿态，也更新selectedPose
      if (selectedPose && selectedPose.name === editingPose.name) {
        setSelectedPose({ ...selectedPose, keys: [...editingKeys] });
      }

      setEditingPose(null);
      setEditingKeys([]);
      toast.success('按键配置已保存');
    } catch (error) {
      toast.error('保存失败');
      console.error('保存按键配置失败:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingPose(null);
    setEditingKeys([]);
  };

  const addKey = () => {
    setEditingKeys(prev => [...prev, '']);
  };

  const removeKey = (index: number) => {
    setEditingKeys(prev => prev.filter((_, i) => i !== index));
  };

  const updateKey = (index: number, value: string) => {
    setEditingKeys(prev => prev.map((key, i) => i === index ? value : key));
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col p-8 overflow-y-auto">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white">姿态配置</h1>
        <p className="text-slate-400 mt-1">管理姿态模板和按键映射配置</p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* 姿态列表 */}
        <div className="xl:col-span-1">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <Settings className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-xl text-white">姿态模板</h3>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {poseConfigs.map((pose) => (
                <div
                  key={`${pose.name}_${pose.index}`}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedPose?.name === pose.name
                      ? 'bg-indigo-600/20 border-indigo-500'
                      : 'bg-slate-950 border-slate-800 hover:bg-slate-800'
                  }`}
                  onClick={() => setSelectedPose(pose)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-white">{pose.name}</h4>
                      <p className="text-xs text-slate-400 mt-1">
                        基准点: {pose.basekeypoints}
                      </p>
                      <p className="text-xs text-slate-400">
                        相似度阈值: {pose.similarity_threshold}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditKeys(pose);
                        }}
                        className="p-1 text-slate-400 hover:text-indigo-400 transition-colors"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* 显示当前按键 */}
                  {pose.keys && pose.keys.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {pose.keys.map((key, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded text-xs font-mono text-indigo-400"
                        >
                          {formatKeyDisplay(key)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 姿态详情和预览 */}
        <div className="xl:col-span-2">
          {selectedPose ? (
            <div className="space-y-6">
              {/* 姿态信息 */}
              <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <div className="flex items-center space-x-2 mb-6">
                  <Eye className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-bold text-xl text-white">{selectedPose.name} 详情</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 姿态图片预览 */}
                  <div>
                    <h4 className="font-medium text-white mb-3">姿态预览</h4>
                    <div className="aspect-video bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
                      <canvas
                        ref={canvasRef}
                        className="w-full h-full"
                        style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)' }}
                      />
                    </div>
                  </div>

                  {/* 姿态参数 */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-white">姿态参数</h4>
                      <button
                        onClick={() => handleEditKeys(selectedPose)}
                        className="flex items-center space-x-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm transition-colors"
                      >
                        <Key className="w-4 h-4" />
                        <span>配置键位</span>
                      </button>
                    </div>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">基准关键点:</span>
                        <span className="text-white font-mono">{selectedPose.basekeypoints}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">相似度阈值:</span>
                        <span className="text-white font-mono">{selectedPose.similarity_threshold}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block mb-2">核心关键点:</span>
                        <div className="flex flex-wrap gap-1">
                          {selectedPose.list_corekeypoints.map((point, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-slate-800 rounded text-xs font-mono text-slate-300"
                            >
                              {point}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-slate-400 block mb-2">当前按键映射:</span>
                        {selectedPose.keys && selectedPose.keys.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {selectedPose.keys.map((key, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded text-xs font-mono text-indigo-400"
                              >
                                {formatKeyDisplay(key)}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-500 text-sm">暂无按键映射</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 按键编辑 */}
              {editingPose && selectedPose && editingPose.name === selectedPose.name && (
                <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-2">
                      <Key className="w-5 h-5 text-indigo-400" />
                      <h3 className="font-bold text-xl text-white">编辑按键映射</h3>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={handleSaveKeys}
                        disabled={isSaving}
                        className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white rounded-lg text-sm transition-colors"
                      >
                        <Save className="w-4 h-4" />
                        <span>{isSaving ? '保存中...' : '保存'}</span>
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="flex items-center space-x-2 px-3 py-1.5 bg-slate-600 hover:bg-slate-700 text-white rounded-lg text-sm transition-colors"
                      >
                        <X className="w-4 h-4" />
                        <span>取消</span>
                      </button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-400">按键序列</label>
                      <button
                        onClick={addKey}
                        className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-sm transition-colors"
                      >
                        添加按键
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {editingKeys.map((key, index) => (
                        <div key={index} className="flex space-x-2">
                          <select
                            value={key}
                            onChange={(e) => updateKey(index, e.target.value)}
                            className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                          >
                            <option value="">选择按键</option>
                            {availableKeys.map((availableKey) => (
                              <option key={availableKey} value={availableKey}>
                                {formatKeyDisplay(availableKey)}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() => removeKey(index)}
                            className="p-2 bg-rose-600 hover:bg-rose-700 text-white rounded transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>

                    {editingKeys.length === 0 && (
                      <div className="text-center py-8 text-slate-500">
                        <Key className="w-12 h-12 mx-auto mb-2 opacity-50" />
                        <p>暂无按键映射，点击"添加按键"开始配置</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-12 flex items-center justify-center">
              <div className="text-center text-slate-500">
                <Eye className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-medium mb-2">选择姿态模板</h3>
                <p>从左侧列表中选择一个姿态模板进行预览和配置</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PoseConfig;