import React, { useState, useEffect } from 'react';
import { 
  RotateCcw, 
  Calendar, 
  Clock, 
  User, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign,
  BookOpen,
  Settings,
  Zap,
  TrendingUp,
  Award,
  Target
} from 'lucide-react';

// Компонент планировщика ротации
const RotationPlanner = () => {
  const [groups, setGroups] = useState([]);
  const [pendingUnits, setPendingUnits] = useState([]);
  const [rotationPlan, setRotationPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState(null);

  useEffect(() => {
    fetchRotationData();
  }, []);

  const fetchRotationData = async () => {
    try {
      // Загружаем группы, которым нужно завершение юнитов
      const groupsData = await fetch('/api/groups/?needs_rotation=true').then(r => r.json());
      
      // Фильтруем группы, у которых завершены 6 занятий
      const needingRotation = groupsData.filter(group => 
        group.current_unit_info && group.current_unit_info.lessons_completed >= 6
      );

      setGroups(needingRotation);
      
      // Создаем список юнитов для завершения
      const units = needingRotation.map(group => ({
        id: group.current_unit_info?.unit_number || 1,
        group: group,
        status: 'pending',
        mainTeacher: group.teacher_info,
        studentsCount: group.students_info?.length || 0
      }));

      setPendingUnits(units);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки данных ротации:', error);
      setLoading(false);
    }
  };

  const planUnitCompletion = async (unitData) => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/groups/${unitData.group.id}/complete_unit/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setRotationPlan(result);
        
        // Обновляем статус юнита
        setPendingUnits(prev => 
          prev.map(unit => 
            unit.group.id === unitData.group.id 
              ? { ...unit, status: 'planned' }
              : unit
          )
        );
      } else {
        alert(`Ошибка: ${result.error}`);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Ошибка планирования завершения юнита:', error);
      setLoading(false);
    }
  };

  const UnitCard = ({ unit }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{unit.group.name}</h3>
          <p className="text-sm text-gray-600">
            Юнит {unit.id} • {unit.group.branch_info?.name}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          unit.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
          unit.status === 'planned' ? 'bg-green-100 text-green-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {unit.status === 'pending' ? 'Ожидает планирования' :
           unit.status === 'planned' ? 'Запланировано' : 'В процессе'}
        </span>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center text-sm">
          <User className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-gray-600">Основной преподаватель:</span>
          <span className="ml-2 font-medium">{unit.mainTeacher?.full_name}</span>
        </div>
        
        <div className="flex items-center text-sm">
          <BookOpen className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-gray-600">Учеников в группе:</span>
          <span className="ml-2 font-medium">{unit.studentsCount}</span>
        </div>

        <div className="flex items-center text-sm">
          <Clock className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-gray-600">Паттерн занятий:</span>
          <span className="ml-2 font-medium">{unit.group.schedule_pattern}</span>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
        <div className="flex items-start">
          <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium">Требуется ротация:</p>
            <ul className="mt-1 space-y-1">
              <li>• Назначить Екатерину на контрольное занятие</li>
              <li>• Назначить Екатерину на расширенную лексику</li>
              <li>• Найти компенсационную работу для {unit.mainTeacher?.full_name}</li>
            </ul>
          </div>
        </div>
      </div>

      <button
        onClick={() => planUnitCompletion(unit)}
        disabled={unit.status === 'planned' || loading}
        className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
          unit.status === 'planned'
            ? 'bg-green-100 text-green-800 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {unit.status === 'planned' ? (
          <>
            <CheckCircle className="h-4 w-4 inline mr-2" />
            Ротация запланирована
          </>
        ) : (
          <>
            <RotateCcw className="h-4 w-4 inline mr-2" />
            Спланировать ротацию
          </>
        )}
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Планировщик ротации</h1>
          <p className="text-gray-600">
            Управление завершением юнитов и автоматическим назначением специальных занятий
          </p>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Юнитов к завершению</p>
                <p className="text-2xl font-bold text-blue-600">{pendingUnits.length}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Запланированных ротаций</p>
                <p className="text-2xl font-bold text-green-600">
                  {pendingUnits.filter(u => u.status === 'planned').length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Преподавателей затронуто</p>
                <p className="text-2xl font-bold text-purple-600">
                  {new Set(pendingUnits.map(u => u.mainTeacher?.id)).size}
                </p>
              </div>
              <User className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Список юнитов для ротации */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : pendingUnits.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {pendingUnits.map((unit, index) => (
              <UnitCard key={index} unit={unit} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <RotateCcw className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Нет юнитов для ротации</h3>
            <p className="mt-1 text-sm text-gray-500">
              Все группы находятся в процессе прохождения текущих юнитов
            </p>
          </div>
        )}

        {/* Результат планирования */}
        {rotationPlan && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              Результат планирования ротации
            </h2>
            
            <div className="space-y-4">
              {rotationPlan.special_lessons && rotationPlan.special_lessons.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Специальные занятия:</h3>
                  <div className="space-y-2">
                    {rotationPlan.special_lessons.map((lesson, index) => (
                      <div key={index} className="bg-blue-50 border border-blue-200 rounded p-3">
                        <p className="text-sm font-medium text-blue-900">
                          {lesson.lesson_type === 'control' ? 'Контрольное занятие' : 'Расширенная лексика'}
                        </p>
                        <p className="text-sm text-blue-700">
                          {lesson.datetime} • {lesson.classroom?.name}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {rotationPlan.compensation_work && rotationPlan.compensation_work.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Компенсационная работа:</h3>
                  <div className="space-y-2">
                    {rotationPlan.compensation_work.map((work, index) => (
                      <div key={index} className="bg-green-50 border border-green-200 rounded p-3">
                        <p className="text-sm font-medium text-green-900">{work.description}</p>
                        <p className="text-sm text-green-700">
                          Оплата: {work.total_payment} руб.
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {rotationPlan.main_teacher_guaranteed_income && (
                <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                  <p className="text-sm font-medium text-yellow-900">
                    Гарантированный доход преподавателя: {rotationPlan.main_teacher_guaranteed_income} руб.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Компонент автоматической генерации расписания
const AutoScheduleGenerator = () => {
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [weekStart, setWeekStart] = useState('');
  const [generationResult, setGenerationResult] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationSettings, setGenerationSettings] = useState({
    optimizePeakTime: true,
    avoidConflicts: true,
    balanceTeacherLoad: true,
    prioritizeRegularSchedule: true
  });

  useEffect(() => {
    fetchBranches();
    
    // Установить начало текущей недели как значение по умолчанию
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    setWeekStart(monday.toISOString().split('T')[0]);
  }, []);

  const fetchBranches = async () => {
    try {
      const data = await fetch('/api/branches/').then(r => r.json());
      setBranches(data);
    } catch (error) {
      console.error('Ошибка загрузки филиалов:', error);
    }
  };

  const generateSchedule = async () => {
    if (!selectedBranch || !weekStart) {
      alert('Выберите филиал и дату начала недели');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/schedule/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          branch_id: selectedBranch,
          week_start: weekStart,
          settings: generationSettings
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        setGenerationResult(result);
      } else {
        alert(`Ошибка генерации: ${result.error}`);
      }
    } catch (error) {
      console.error('Ошибка генерации расписания:', error);
      alert('Произошла ошибка при генерации расписания');
    } finally {
      setIsGenerating(false);
    }
  };

  const StatisticCard = ({ icon: Icon, title, value, color, description }) => (
    <div className={`bg-white rounded-lg shadow p-6 border-l-4 ${color}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Icon className="h-6 w-6 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <span className="text-2xl font-bold text-gray-900">{value}</span>
      </div>
      {description && (
        <p className="text-sm text-gray-600">{description}</p>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Автогенерация расписания</h1>
          <p className="text-gray-600">
            Умное планирование расписания с учетом всех ограничений и оптимизацией ресурсов
          </p>
        </div>

        {/* Форма настроек генерации */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Параметры генерации</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Основные параметры */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Основные настройки</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Филиал
                </label>
                <select
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Выберите филиал</option>
                  {branches.map(branch => (
                    <option key={branch.id} value={branch.id}>
                      {branch.name} ({branch.address})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Начало недели
                </label>
                <input
                  type="date"
                  value={weekStart}
                  onChange={(e) => setWeekStart(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Настройки оптимизации */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Настройки оптимизации</h3>
              
              {Object.entries({
                optimizePeakTime: 'Оптимизировать пиковое время (13:00-17:00)',
                avoidConflicts: 'Избегать конфликтов расписания',
                balanceTeacherLoad: 'Балансировать нагрузку преподавателей',
                prioritizeRegularSchedule: 'Приоритет регулярному расписанию'
              }).map(([key, label]) => (
                <label key={key} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={generationSettings[key]}
                    onChange={(e) => setGenerationSettings(prev => ({
                      ...prev,
                      [key]: e.target.checked
                    }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={generateSchedule}
              disabled={isGenerating || !selectedBranch || !weekStart}
              className={`px-6 py-3 rounded-lg font-medium flex items-center ${
                isGenerating || !selectedBranch || !weekStart
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Генерируется...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Сгенерировать расписание
                </>
              )}
            </button>
          </div>
        </div>

        {/* Результаты генерации */}
        {generationResult && (
          <div className="space-y-6">
            {/* Статистика */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatisticCard
                icon={Calendar}
                title="Занятий создано"
                value={generationResult.generated_lessons_count || 0}
                color="border-blue-500"
                description="Обычных и специальных"
              />
              
              <StatisticCard
                icon={TrendingUp}
                title="Загрузка пик. времени"
                value={`${generationResult.statistics?.peak_time_utilization || 0}%`}
                color="border-green-500"
                description="13:00-17:00"
              />
              
              <StatisticCard
                icon={AlertTriangle}
                title="Конфликтов"
                value={generationResult.conflicts?.length || 0}
                color="border-red-500"
                description="Требуют разрешения"
              />
              
              <StatisticCard
                icon={Target}
                title="Эффективность"
                value={`${generationResult.statistics?.classroom_utilization || 0}%`}
                color="border-purple-500"
                description="Использование кабинетов"
              />
            </div>

            {/* Детальная информация */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Конфликты */}
              {generationResult.conflicts && generationResult.conflicts.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                    Обнаруженные конфликты ({generationResult.conflicts.length})
                  </h3>
                  
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {generationResult.conflicts.map((conflict, index) => (
                      <div key={index} className="bg-red-50 border border-red-200 rounded p-3">
                        <p className="text-sm font-medium text-red-900">
                          {conflict.type === 'classroom_double_booking' ? 'Конфликт кабинета' :
                           conflict.type === 'teacher_double_booking' ? 'Конфликт преподавателя' :
                           conflict.type === 'teacher_overload' ? 'Перегрузка преподавателя' :
                           'Другой конфликт'}
                        </p>
                        <p className="text-sm text-red-700 mt-1">{conflict.description}</p>
                        {conflict.suggested_solutions && conflict.suggested_solutions.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs text-red-600">Предложения:</p>
                            <ul className="text-xs text-red-600 ml-2">
                              {conflict.suggested_solutions.map((solution, sIndex) => (
                                <li key={sIndex}>• {solution}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Статистика по преподавателям */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <User className="h-5 w-5 text-blue-500 mr-2" />
                  Распределение нагрузки
                </h3>
                
                {generationResult.statistics?.teacher_load_distribution ? (
                  <div className="space-y-3">
                    {Object.entries(generationResult.statistics.teacher_load_distribution).map(([teacherId, load]) => (
                      <div key={teacherId} className="flex justify-between items-center">
                        <span className="text-sm text-gray-700">Преподаватель {teacherId}</span>
                        <div className="flex items-center">
                          <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${Math.min(load * 10, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">{load} ур.</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Данные о распределении нагрузки недоступны</p>
                )}
              </div>
            </div>

            {/* Сообщение об успехе */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <p className="text-green-800 font-medium">
                  Расписание успешно сгенерировано!
                </p>
              </div>
              <p className="text-green-700 text-sm mt-1">
                Создано {generationResult.generated_lessons_count} занятий. 
                {generationResult.conflicts && generationResult.conflicts.length > 0 
                  ? ` Обнаружено ${generationResult.conflicts.length} конфликт(ов), требующих разрешения.`
                  : ' Конфликтов не обнаружено.'
                }
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Компонент распределения нагрузки
const WorkloadDistributor = () => {
  const [teachers, setTeachers] = useState([]);
  const [workloadData, setWorkloadData] = useState({});
  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkloadData();
  }, [selectedPeriod]);

  const fetchWorkloadData = async () => {
    try {
      const teachersData = await fetch('/api/teachers/').then(r => r.json());
      
      // Загружаем данные о нагрузке для каждого преподавателя
      const workloadPromises = teachersData.map(async (teacher) => {
        const scheduleData = await fetch(`/api/teachers/${teacher.id}/schedule/`).then(r => r.json());
        return {
          ...teacher,
          currentLoad: scheduleData.total_hours || 0,
          estimatedIncome: scheduleData.estimated_income || 0,
          compensationWork: scheduleData.compensation_work || []
        };
      });

      const teachersWithWorkload = await Promise.all(workloadPromises);
      setTeachers(teachersWithWorkload);
      
      // Создаем объект для быстрого доступа
      const workloadMap = {};
      teachersWithWorkload.forEach(teacher => {
        workloadMap[teacher.id] = {
          current: teacher.currentLoad,
          target: teacher.preferred_load,
          min: teacher.min_weekly_load,
          max: teacher.max_daily_load * 7, // примерный максимум в неделю
          income: teacher.estimatedIncome
        };
      });
      
      setWorkloadData(workloadMap);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки данных о нагрузке:', error);
      setLoading(false);
    }
  };

  const getLoadStatus = (teacher) => {
    const workload = workloadData[teacher.id];
    if (!workload) return 'unknown';
    
    const utilization = workload.current / workload.target;
    
    if (utilization < 0.7) return 'underloaded';
    if (utilization > 1.2) return 'overloaded';
    return 'optimal';
  };

  const getLoadColor = (status) => {
    switch (status) {
      case 'underloaded': return 'text-yellow-600 bg-yellow-100';
      case 'overloaded': return 'text-red-600 bg-red-100';
      case 'optimal': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getLoadLabel = (status) => {
    switch (status) {
      case 'underloaded': return 'Недогружен';
      case 'overloaded': return 'Перегружен';
      case 'optimal': return 'Оптимально';
      default: return 'Неизвестно';
    }
  };

  const TeacherWorkloadCard = ({ teacher }) => {
    const status = getLoadStatus(teacher);
    const workload = workloadData[teacher.id] || {};
    
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{teacher.full_name}</h3>
            <p className="text-sm text-gray-600">{teacher.get_teacher_role_display}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getLoadColor(status)}`}>
            {getLoadLabel(status)}
          </span>
        </div>

        {/* Прогресс-бар нагрузки */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Текущая нагрузка</span>
            <span>{workload.current || 0} / {workload.target || 0} ур.</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                status === 'underloaded' ? 'bg-yellow-500' :
                status === 'overloaded' ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ 
                width: `${Math.min((workload.current / workload.target) * 100, 100)}%` 
              }}
            ></div>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Доход в неделю</p>
            <p className="text-lg font-semibold text-gray-900">
              {workload.income ? `${workload.income.toLocaleString()} ₽` : '0 ₽'}
            </p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Филиалы</p>
            <p className="text-lg font-semibold text-gray-900">
              {teacher.available_branches_names?.length || 0}
            </p>
          </div>
        </div>

        {/* Компенсационная работа */}
        {teacher.compensationWork && teacher.compensationWork.length > 0 && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-900 mb-2">Компенсационная работа:</p>
            <div className="space-y-1">
              {teacher.compensationWork.slice(0, 2).map((work, index) => (
                <div key={index} className="text-xs text-gray-600 bg-blue-50 rounded px-2 py-1">
                  {work.description}
                </div>
              ))}
              {teacher.compensationWork.length > 2 && (
                <p className="text-xs text-gray-500">+{teacher.compensationWork.length - 2} еще...</p>
              )}
            </div>
          </div>
        )}

        {/* Действия */}
        <div className="flex space-x-2">
          <button className="flex-1 py-2 px-3 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100">
            Назначить работу
          </button>
          <button className="flex-1 py-2 px-3 text-sm font-medium text-gray-600 bg-gray-50 rounded hover:bg-gray-100">
            Подробнее
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Распределение нагрузки</h1>
          <p className="text-gray-600">
            Мониторинг и оптимизация рабочей нагрузки преподавателей
          </p>
        </div>

        {/* Общая статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Всего преподавателей</p>
                <p className="text-2xl font-bold text-gray-900">{teachers.length}</p>
              </div>
              <User className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Недогруженных</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {teachers.filter(t => getLoadStatus(t) === 'underloaded').length}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Перегруженных</p>
                <p className="text-2xl font-bold text-red-600">
                  {teachers.filter(t => getLoadStatus(t) === 'overloaded').length}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Оптимальная нагрузка</p>
                <p className="text-2xl font-bold text-green-600">
                  {teachers.filter(t => getLoadStatus(t) === 'optimal').length}
                </p>
              </div>
              <Award className="h-8 w-8 text-green-500" />
            </div>
          </div>
        </div>

        {/* Фильтры и сортировка */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="p-2 border border-gray-300 rounded-lg"
              >
                <option value="week">Текущая неделя</option>
                <option value="month">Текущий месяц</option>
                <option value="quarter">Квартал</option>
              </select>
              
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Автоматическое распределение
              </button>
            </div>

            <button
              onClick={fetchWorkloadData}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Обновить данные
            </button>
          </div>
        </div>

        {/* Список преподавателей */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teachers.map((teacher) => (
              <TeacherWorkloadCard key={teacher.id} teacher={teacher} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export { RotationPlanner, AutoScheduleGenerator, WorkloadDistributor };