import React, { useState, useEffect, useRef } from 'react';
import { Settings, Eye, Edit3, Save, X, Key, Activity, Clock, Plus, Trash2 } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface PoseConfig {
  name: string;
  index: number;
  inner_flag: boolean;
  enable?: boolean;
  similarity_threshold: number;
  camera_type: string;
  keys: string[];
  basekeypoints: string;
  list_corekeypoints: string[];
  value_dict: { [key: string]: number[] };
  raw_value_dict?: { [key: string]: number[] }; // 建议增加此字段存储原始坐标
  pose_img: string;
}

interface PoseConfigProps {
  imageSrc?: string;
  personDetected?: boolean;
  isCameraRunning?: boolean;
}

const PoseConfig: React.FC<PoseConfigProps> = ({ imageSrc, personDetected, isCameraRunning }) => {
  const [poseConfigs, setPoseConfigs] = useState<PoseConfig[]>([]);
  const [selectedPose, setSelectedPose] = useState<PoseConfig | null>(null);
  const [editingKeys, setEditingKeys] = useState<string[]>([]);
  const [editingPose, setEditingPose] = useState<PoseConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  // 重录相关状态
  const [isRecordingModalOpen, setIsRecordingModalOpen] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const allKeypoints = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
  ];

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
    if (!canvas) return;

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

    const keypointPositions: { [key: string]: { x: number; y: number } } = {};

    if (pose.raw_value_dict) {
      // 使用原始坐标绘制（绝对坐标）
      const allCoords = Object.values(pose.raw_value_dict);
      if (allCoords.length === 0) return;

      // 计算原始坐标的边界
      const xs = allCoords.map(([x]) => x);
      const ys = allCoords.map(([, y]) => y);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);

      const originalWidth = maxX - minX;
      const originalHeight = maxY - minY;

      // 计算缩放因子，使姿态适应画布
      const scaleX = (canvas.width - 40) / originalWidth;
      const scaleY = (canvas.height - 40) / originalHeight;
      const scale = Math.min(scaleX, scaleY, 1); // 不放大

      // 计算偏移，使姿态居中
      const offsetX = (canvas.width - originalWidth * scale) / 2 - minX * scale;
      const offsetY = (canvas.height - originalHeight * scale) / 2 - minY * scale;

      // 计算所有关键点位置
      Object.entries(pose.raw_value_dict).forEach(([keypointName, coords]) => {
        if (coords && coords.length >= 2) {
          const [x, y] = coords;
          // 水平翻转：为了匹配 Dashboard 中翻转后的镜像视频效果
          // 使用坐标范围 (minX ~ maxX) 进行镜像转换
          const mirroredX = maxX - (x - minX);
          const canvasX = mirroredX * scale + offsetX;
          const canvasY = y * scale + offsetY;
          keypointPositions[keypointName] = { x: canvasX, y: canvasY };
        }
      });
    } else if (pose.value_dict) {
      // 使用相对坐标绘制（原有逻辑）
      let baseX = canvas.width / 2;
      let baseY = canvas.height / 2;

      // 计算所有关键点的坐标
      Object.entries(pose.value_dict).forEach(([keypointName, coords]) => {
        if (coords && coords.length >= 2) {
          const [offsetX, offsetY] = coords;
          
          // 水平翻转偏移量：为了匹配镜像视图
          const mirroedOffsetX = -offsetX;
          
          // 将相对坐标转换为画布坐标
          const scale = Math.min(canvas.width, canvas.height) / 500; // 调整缩放因子
          const canvasX = baseX + mirroedOffsetX * scale * 0.8;
          const canvasY = baseY - offsetY * scale * 0.8;

          // 确保坐标在画布范围内
          const clampedX = Math.max(20, Math.min(canvas.width - 20, canvasX));
          const clampedY = Math.max(20, Math.min(canvas.height - 20, canvasY));
          
          keypointPositions[keypointName] = { x: clampedX, y: clampedY };
        }
      });
    } else {
      return; // 没有数据可绘制
    }

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
      const isBase = keypointName === pose.basekeypoints;
      const isCore = pose.list_corekeypoints?.includes(keypointName);
      
      // 绘制关键点阴影
      ctx.beginPath();
      ctx.arc(pos.x + 1, pos.y + 1, 8, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
      ctx.fill();
      
      // 绘制关键点
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
      
      if (pose.raw_value_dict) {
        // 有原始坐标时
        if (isBase) {
          ctx.fillStyle = '#10b981'; // 基准点 - 绿色
        } else if (isCore) {
          ctx.fillStyle = '#f59e0b'; // 核心点 - 琥珀色
        } else {
          ctx.fillStyle = '#60a5fa'; // 其他点 - 蓝色
        }
      } else {
        // 没有原始坐标时：原有颜色逻辑
        if (isBase) {
          ctx.fillStyle = '#10b981'; // 基准点 - 绿色
        } else if (isCore) {
          ctx.fillStyle = '#f59e0b'; // 核心点 - 琥珀色
        } else {
          ctx.fillStyle = '#ef4444'; // 其他点 - 红色
        }
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
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditKeys = (pose: PoseConfig) => {
    setEditingPose(pose);
    setEditingKeys([...pose.keys]);
  };

  const handleAddNewAction = () => {
    // 找到最大的 index 并加 1
    const maxIndex = poseConfigs.reduce((max, p) => Math.max(max, p.index), -1);
    const newIndex = maxIndex + 1;
    
    const newPose: PoseConfig = {
      name: `新姿态模板_${newIndex}`,
      index: newIndex,
      inner_flag: false,
      enable: true,
      similarity_threshold: 0.8,
      camera_type: '72camera',
      keys: [],
      basekeypoints: 'nose',
      list_corekeypoints: ['nose', 'left_shoulder', 'right_shoulder'],
      value_dict: {},
      pose_img: ''
    };
    
    setEditingPose(newPose);
    setEditingKeys([]);
    setSelectedPose(newPose);
  };

  const handleSaveKeys = async () => {
    if (!editingPose) return;

    // 检查是否修改了关键结构逻辑
    const structureChanged = 
      editingPose.basekeypoints !== (selectedPose?.basekeypoints) ||
      JSON.stringify(editingPose.list_corekeypoints.sort()) !== JSON.stringify([...(selectedPose?.list_corekeypoints || [])].sort());

    // 对于没有 raw_value_dict 的旧数据，禁止修改基准点或核心点列表
    if (structureChanged && !editingPose.raw_value_dict) {
      toast.error('该姿态缺少原始坐标记录 (raw_value_dict)，无法修改基准点或核心点列表。请重新录制该姿态。');
      return;
    }

    let updatedValueDict = { ...editingPose.value_dict };
    
    // 如果有原始坐标，根据新的基准点和核心点列表重新计算向量映射
    if (editingPose.raw_value_dict) {
      const basePos = editingPose.raw_value_dict[editingPose.basekeypoints] || [0, 0];
      updatedValueDict = {};
      editingPose.list_corekeypoints.forEach(kp => {
        const kpPos = editingPose.raw_value_dict![kp] || [0, 0];
        updatedValueDict[kp] = [
          kpPos[0] - basePos[0],
          kpPos[1] - basePos[1]
        ];
      });
    }

    const finalPose = {
      ...editingPose,
      keys: editingKeys,
      value_dict: updatedValueDict
    };

    setIsSaving(true);
    try {
      // 使用现有的保存接口
      await axios.post('/api/save_pose', finalPose);

      // 更新本地状态
      setPoseConfigs(prev => {
        const index = prev.findIndex(p => p.index === finalPose.index);
        if (index !== -1) {
          const newList = [...prev];
          newList[index] = finalPose;
          return newList;
        } else {
          return [...prev, finalPose];
        }
      });

      setSelectedPose(finalPose);
      // 不关闭编辑框，让用户可以继续编辑其他字段
      setEditingPose(finalPose);
      toast.success('配置已保存 (向量已自动重新计算)');
    } catch (error) {
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingPose(null);
    setEditingKeys([]);
  };

  const handleDeletePose = async (pose: PoseConfig) => {
    if (!window.confirm(`确定要删除姿态 "${pose.name}" 吗？`)) return;

    try {
      const response = await axios.post('/api/delete_pose', { index: pose.index });
      if (response.data.success) {
        toast.success('删除成功');
        setPoseConfigs(prev => prev.filter(p => p.index !== pose.index));
        if (selectedPose?.index === pose.index) {
          setSelectedPose(null);
        }
        if (editingPose?.index === pose.index) {
          setEditingPose(null);
        }
      } else {
        toast.error(response.data.message || '删除失败');
      }
    } catch (error) {
      toast.error('删除请求失败');
    }
  };

  const addKey = () => {
    setEditingKeys(prev => [...prev, '']);
  };

  // 开始重录流程
  const startReRecording = () => {
    if (!isCameraRunning) {
      toast.error('请先在 Dashboard 启动摄像头');
      return;
    }
    setIsRecordingModalOpen(true);
    setCountdown(5);
  };

  // 处理倒计时逻辑
  useEffect(() => {
    let timer: any;
    if (isRecordingModalOpen && countdown !== null && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (countdown === 0) {
      // 倒计时结束，从后端拉取最新的有效原始坐标
      const fetchLatestAndCapture = async () => {
        try {
          const res = await axios.get('/api/latest_keypoints');
          if (res.data) {
            handleCapturePose(res.data);
          } else {
            toast.error('未能捕获到关键点数据，请确保人出现在画面中并重试');
            setIsRecordingModalOpen(false);
            setCountdown(null);
          }
        } catch (err) {
          toast.error('请求后端数据失败');
          setIsRecordingModalOpen(false);
          setCountdown(null);
        }
      };
      
      fetchLatestAndCapture();
    }
    return () => clearTimeout(timer);
  }, [isRecordingModalOpen, countdown]);

  const handleCapturePose = (capturedRaw: any) => {
    if (!editingPose) return;

    // 重新计算 value_dict
    const basePos = capturedRaw[editingPose.basekeypoints] || [0, 0];
    const newValueDict: { [key: string]: number[] } = {};
    
    editingPose.list_corekeypoints.forEach(kp => {
      const kpPos = capturedRaw[kp] || [0, 0];
      newValueDict[kp] = [
        kpPos[0] - basePos[0],
        kpPos[1] - basePos[1]
      ];
    });

    setEditingPose({
      ...editingPose,
      raw_value_dict: capturedRaw,
      value_dict: newValueDict
    });

    setIsRecordingModalOpen(false);
    setCountdown(null);
    toast.success('捕捉成功！请记得保存配置。');
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
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-xl text-white">姿态模板</h3>
              </div>
              <button
                onClick={handleAddNewAction}
                className="p-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center space-x-1 shadow-lg shadow-indigo-900/20"
                title="新增动作"
              >
                <Plus className="w-4 h-4" />
                <span className="text-xs font-bold px-1">新增动作</span>
              </button>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {poseConfigs.map((pose) => (
                <div
                  key={`${pose.index}`}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedPose?.index === pose.index
                      ? 'bg-indigo-600/20 border-indigo-500'
                      : 'bg-slate-950 border-slate-800 hover:bg-slate-800'
                  }`}
                  onClick={() => setSelectedPose(pose)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-white">{pose.name}</h4>
                        {pose.enable === false && (
                          <span className="px-1.5 py-0.5 bg-rose-500/20 border border-rose-500/30 rounded text-[10px] font-bold text-rose-400">
                            禁用
                          </span>
                        )}
                      </div>
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
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePose(pose);
                        }}
                        className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                        title="删除姿态"
                      >
                        <Trash2 className="w-4 h-4" />
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
                      <div className="flex justify-between">
                        <span className="text-slate-400">启用状态:</span>
                        <span className={`font-mono ${(selectedPose.enable !== false) ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {(selectedPose.enable !== false) ? '已启用' : '已禁用'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">相机类型:</span>
                        <span className="text-white font-mono">{selectedPose.camera_type || '72camera'}</span>
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
              {editingPose && selectedPose && editingPose.index === selectedPose.index && (
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

                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-slate-800">
                      <div>
                        <label className="text-sm font-medium text-slate-400 block mb-2">姿态名称</label>
                        <input
                          type="text"
                          value={editingPose.name}
                          onChange={(e) => setEditingPose({ ...editingPose, name: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-400 block mb-2">基准关键点 (Base)</label>
                        <select
                          value={editingPose.basekeypoints}
                          onChange={(e) => setEditingPose({ ...editingPose, basekeypoints: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                        >
                          {allKeypoints.map(kp => (
                            <option key={kp} value={kp}>{kp}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-400 block mb-2">录制时的相机类型</label>
                        <select
                          value={editingPose.camera_type || '72camera'}
                          onChange={(e) => setEditingPose({ ...editingPose, camera_type: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                        >
                          <option value="72camera">72°相机 (72camera)</option>
                          <option value="120width_camera">120°横向畸变相机 (120width_camera)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-400 block mb-2">相似度阈值</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={editingPose.similarity_threshold}
                          onChange={(e) => setEditingPose({ ...editingPose, similarity_threshold: parseFloat(e.target.value) })}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div className="flex items-center space-x-3 h-full pt-6">
                        <label className="text-sm font-medium text-slate-400">是否启用</label>
                        <button
                          onClick={() => setEditingPose({ ...editingPose, enable: !editingPose.hasOwnProperty('enable') ? false : !editingPose.enable })}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                            (editingPose.enable !== false) ? 'bg-indigo-600' : 'bg-slate-700'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              (editingPose.enable !== false) ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                        <span className="text-xs text-slate-500">
                          {(editingPose.enable !== false) ? '启用' : '禁用'}
                        </span>
                      </div>
                    </div>

                    <div className="pb-6 border-b border-slate-800">
                      <div className="flex items-center justify-between mb-4">
                        <label className="text-sm font-medium text-slate-400">核心关键点 (Core Keypoints)</label>
                        <span className="text-xs text-slate-500">勾选参与姿态匹配的点</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {allKeypoints.map(kp => (
                          <label key={kp} className="flex items-center space-x-2 p-2 bg-slate-950 rounded border border-slate-800 cursor-pointer hover:border-indigo-500 transition-colors">
                            <input
                              type="checkbox"
                              checked={editingPose.list_corekeypoints.includes(kp)}
                              disabled={kp === editingPose.basekeypoints}
                              onChange={(e) => {
                                const newList = e.target.checked
                                  ? [...editingPose.list_corekeypoints, kp]
                                  : editingPose.list_corekeypoints.filter(p => p !== kp);
                                setEditingPose({ ...editingPose, list_corekeypoints: newList });
                              }}
                              className="w-4 h-4 rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-900"
                            />
                            <span className={`text-xs ${editingPose.list_corekeypoints.includes(kp) ? 'text-indigo-400 font-bold' : 'text-slate-400'}`}>
                              {kp === editingPose.basekeypoints ? `${kp} (Base)` : kp}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

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

                    {/* 姿态具体信息 (Raw JSON) */}
                    <div className="pt-6 border-t border-slate-800">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          <Activity className="w-4 h-4 text-indigo-400" />
                          <h4 className="font-medium text-white">姿态具体信息 (Raw Data)</h4>
                        </div>
                        <button
                          onClick={startReRecording}
                          className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 shadow-lg shadow-rose-900/20"
                        >
                          <Activity className="w-3.5 h-3.5" />
                          <span>立即重录 (生成 Raw)</span>
                        </button>
                      </div>
                      <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-[10px] leading-relaxed text-slate-400 max-h-48 overflow-y-auto custom-scrollbar">
                        {editingPose.raw_value_dict ? (
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(editingPose.raw_value_dict, null, 2)}
                          </pre>
                        ) : (
                          <div className="flex flex-col items-center justify-center py-8 text-slate-600 italic">
                            <Clock className="w-8 h-8 mb-2 opacity-20" />
                            <p>暂无原始关键点数据，请在录制模式下采集</p>
                          </div>
                        )}
                      </div>
                    </div>
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

      {/* 重新录制弹窗 */}
      {isRecordingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-5xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <Clock className="w-6 h-6 text-rose-500 animate-pulse" />
                <h2 className="text-xl font-bold text-white">姿态捕获中...</h2>
              </div>
              <button 
                onClick={() => { setIsRecordingModalOpen(false); setCountdown(null); }}
                className="p-2 hover:bg-slate-800 rounded-full text-slate-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-8">
              <div className="relative aspect-video bg-black rounded-2xl border border-slate-800 flex items-center justify-center overflow-hidden mb-6">
                {imageSrc ? (
                  <img src={imageSrc} className="w-full h-full object-contain" alt="Live Feed" />
                ) : (
                  <div className="text-slate-600">等待视频流...</div>
                )}
                
                {/* 状态指示器 */}
                <div className="absolute top-4 left-4 flex items-center space-x-2 bg-slate-900/60 backdrop-blur px-3 py-1.5 rounded-full border border-white/10">
                  <div className={`w-2 h-2 rounded-full ${personDetected ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-rose-500'}`} />
                  <span className="text-xs font-medium text-white">
                    {personDetected ? '已检测到姿态' : '未检测到人'}
                  </span>
                </div>
                
                {/* 倒计时覆盖层 */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-[120px] font-black text-white drop-shadow-[0_0_30px_rgba(0,0,0,0.8)]">
                    {countdown}
                  </div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-slate-400 text-lg">请摆好姿势，系统将在倒计时结束时捕捉您的动作</p>
                <div className="mt-6 flex justify-center space-x-2">
                  <span className={`h-2 w-12 rounded-full transition-all duration-300 ${countdown! <= 5 ? 'bg-indigo-600' : 'bg-slate-800'}`} />
                  <span className={`h-2 w-12 rounded-full transition-all duration-300 ${countdown! <= 4 ? 'bg-indigo-600' : 'bg-slate-800'}`} />
                  <span className={`h-2 w-12 rounded-full transition-all duration-300 ${countdown! <= 3 ? 'bg-indigo-600' : 'bg-slate-800'}`} />
                  <span className={`h-2 w-12 rounded-full transition-all duration-300 ${countdown! <= 2 ? 'bg-indigo-600' : 'bg-slate-800'}`} />
                  <span className={`h-2 w-12 rounded-full transition-all duration-300 ${countdown! <= 1 ? 'bg-indigo-600' : 'bg-slate-800'}`} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PoseConfig;