import React, { useState, useEffect } from 'react';
import { Calendar, Users, BookOpen, Clock, AlertTriangle, CheckCircle, Plus, Filter, Search } from 'lucide-react';

// API утилиты
const API_BASE = '/api';

const apiCall = async (endpoint, options = {}) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  
  return response.json();
};

// Главный Dashboard компонент
const Dashboard = () => {
  const [statistics, setStatistics] = useState({
    totalStudents: 0,
    totalGroups: 0,
    totalTeachers: 0,
    todayLessons: 0,
    conflicts: 0,
    completedUnits: 0
  });
  
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Загружаем основную статистику
        const [studentsData, groupsData, teachersData] = await Promise.all([
          apiCall('/students/'),
          apiCall('/groups/'),
          apiCall('/teachers/')
        ]);
        
        setStatistics({
          totalStudents: studentsData.length,
          totalGroups: groupsData.length,
          totalTeachers: teachersData.length,
          todayLessons: 12, // заглушка
          conflicts: 2, // заглушка
          completedUnits: 8 // заглушка
        });
        
        // Имитируем последние действия
        setRecentActivity([
          { id: 1, action: 'Создана новая группа "Advanced A1"', time: '10:30', type: 'group' },
          { id: 2, action: 'Завершен юнит группы "Intermediate B2"', time: '09:15', type: 'unit' },
          { id: 3, action: 'Добавлен новый ученик: Иван Петров', time: '08:45', type: 'student' }
        ]);
        
        setLoading(false);
      } catch (error) {
        console.error('Ошибка загрузки данных dashboard:', error);
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);
  
  const StatCard = ({ icon: Icon, title, value, color, onClick }) => (
    <div 
      className={`bg-white rounded-lg shadow-lg p-6 border-l-4 ${color} cursor-pointer hover:shadow-xl transition-shadow`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <Icon className="h-12 w-12 text-gray-400" />
      </div>
    </div>
  );
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Панель управления</h1>
          <p className="text-gray-600 mt-2">Обзор деятельности учебного центра</p>
        </div>
        
        {/* Карточки статистики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={Users}
            title="Активные ученики"
            value={statistics.totalStudents}
            color="border-blue-500"
          />
          <StatCard
            icon={BookOpen}
            title="Активные группы"
            value={statistics.totalGroups}
            color="border-green-500"
          />
          <StatCard
            icon={Users}
            title="Преподаватели"
            value={statistics.totalTeachers}
            color="border-purple-500"
          />
          <StatCard
            icon={Calendar}
            title="Занятия сегодня"
            value={statistics.todayLessons}
            color="border-yellow-500"
          />
          <StatCard
            icon={AlertTriangle}
            title="Конфликты расписания"
            value={statistics.conflicts}
            color="border-red-500"
          />
          <StatCard
            icon={CheckCircle}
            title="Завершенные юниты"
            value={statistics.completedUnits}
            color="border-indigo-500"
          />
        </div>
        
        {/* Быстрые действия */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Быстрые действия</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button className="flex items-center justify-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
              <Plus className="h-5 w-5 text-blue-600 mr-2" />
              <span className="text-blue-600 font-medium">Новый ученик</span>
            </button>
            <button className="flex items-center justify-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
              <BookOpen className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-green-600 font-medium">Создать группу</span>
            </button>
            <button className="flex items-center justify-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
              <Calendar className="h-5 w-5 text-purple-600 mr-2" />
              <span className="text-purple-600 font-medium">Генерация расписания</span>
            </button>
            <button className="flex items-center justify-center p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors">
              <Clock className="h-5 w-5 text-yellow-600 mr-2" />
              <span className="text-yellow-600 font-medium">Завершить юнит</span>
            </button>
          </div>
        </div>
        
        {/* Последняя активность */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Последняя активность</h2>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center p-3 bg-gray-50 rounded-lg">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  activity.type === 'group' ? 'bg-green-500' :
                  activity.type === 'unit' ? 'bg-blue-500' : 'bg-purple-500'
                }`}></div>
                <div className="flex-1">
                  <p className="text-gray-900 font-medium">{activity.action}</p>
                </div>
                <span className="text-sm text-gray-500">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Компонент управления учениками
const StudentManagement = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchStudents();
  }, [searchTerm, statusFilter, levelFilter]);

  const fetchStudents = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (statusFilter) params.append('status', statusFilter);
      if (levelFilter) params.append('level', levelFilter);

      const data = await apiCall(`/students/?${params.toString()}`);
      setStudents(data);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки учеников:', error);
      setLoading(false);
    }
  };

  const StudentCard = ({ student }) => (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {student.first_name} {student.last_name}
          </h3>
          <p className="text-sm text-gray-600">{student.level}</p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          student.status === 'active' ? 'bg-green-100 text-green-800' :
          student.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {student.status === 'active' ? 'Активный' :
           student.status === 'paused' ? 'Приостановлен' : 'Завершил'}
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <span className="w-20">Телефон:</span>
          <span>{student.phone}</span>
        </div>
        {student.email && (
          <div className="flex items-center text-sm text-gray-600">
            <span className="w-20">Email:</span>
            <span>{student.email}</span>
          </div>
        )}
      </div>

      {student.groups_info && student.groups_info.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Группы:</h4>
          <div className="space-y-1">
            {student.groups_info.map((group) => (
              <div key={group.id} className="text-sm text-gray-600 bg-gray-50 rounded px-2 py-1">
                {group.name} ({group.branch})
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between items-center pt-4 border-t">
        <span className="text-sm text-gray-500">
          Посещаемость: {student.attendance_rate}%
        </span>
        <div className="space-x-2">
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Редактировать
          </button>
          <button className="text-green-600 hover:text-green-800 text-sm font-medium">
            Записать в группу
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок и фильтры */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900">Управление учениками</h1>
            <button 
              onClick={() => setShowAddModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              Добавить ученика
            </button>
          </div>

          {/* Фильтры */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Поиск по имени, телефону..."
                  className="pl-10 w-full p-2 border border-gray-300 rounded-lg"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <select
                className="p-2 border border-gray-300 rounded-lg"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">Все статусы</option>
                <option value="active">Активные</option>
                <option value="paused">Приостановленные</option>
                <option value="finished">Завершили обучение</option>
              </select>

              <select
                className="p-2 border border-gray-300 rounded-lg"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="">Все уровни</option>
                <option value="beginner">Beginner</option>
                <option value="elementary">Elementary</option>
                <option value="pre_intermediate">Pre-Intermediate</option>
                <option value="intermediate">Intermediate</option>
                <option value="upper_intermediate">Upper-Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>
        </div>

        {/* Список учеников */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {students.map((student) => (
              <StudentCard key={student.id} student={student} />
            ))}
          </div>
        )}

        {students.length === 0 && !loading && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Ученики не найдены</h3>
            <p className="mt-1 text-sm text-gray-500">
              Попробуйте изменить параметры поиска
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Компонент календаря расписания
const ScheduleCalendar = () => {
  const [lessons, setLessons] = useState([]);
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [branches, setBranches] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCalendarData();
    fetchFiltersData();
  }, [currentWeek, selectedBranch, selectedTeacher]);

  const fetchCalendarData = async () => {
    try {
      const startOfWeek = new Date(currentWeek);
      startOfWeek.setDate(currentWeek.getDate() - currentWeek.getDay() + 1); // Понедельник
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6); // Воскресенье

      const params = new URLSearchParams({
        start_date: startOfWeek.toISOString().split('T')[0],
        end_date: endOfWeek.toISOString().split('T')[0],
      });

      if (selectedBranch) params.append('branch', selectedBranch);
      if (selectedTeacher) params.append('teacher', selectedTeacher);

      const [calendarData, conflictsData] = await Promise.all([
        apiCall(`/schedule/calendar/?${params.toString()}`),
        apiCall(`/schedule/conflicts/?${params.toString()}`)
      ]);

      setLessons(calendarData.lessons);
      setConflicts(conflictsData.conflicts);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки расписания:', error);
      setLoading(false);
    }
  };

  const fetchFiltersData = async () => {
    try {
      const [branchesData, teachersData] = await Promise.all([
        apiCall('/branches/'),
        apiCall('/teachers/')
      ]);

      setBranches(branchesData);
      setTeachers(teachersData);
    } catch (error) {
      console.error('Ошибка загрузки данных фильтров:', error);
    }
  };

  const getWeekDays = () => {
    const days = [];
    const startOfWeek = new Date(currentWeek);
    startOfWeek.setDate(currentWeek.getDate() - currentWeek.getDay() + 1);

    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }

    return days;
  };

  const getTimeSlots = () => {
    const slots = [];
    for (let hour = 11; hour <= 18; hour++) {
      slots.push(`${hour}:00`);
    }
    return slots;
  };

  const getLessonsForSlot = (day, time) => {
    const dayStr = day.toISOString().split('T')[0];
    const timeStr = `${time}:00`;
    
    return lessons.filter(lesson => {
      const lessonDate = new Date(lesson.start).toISOString().split('T')[0];
      const lessonTime = new Date(lesson.start).toTimeString().substring(0, 5);
      return lessonDate === dayStr && lessonTime === timeStr;
    });
  };

  const LessonCard = ({ lesson }) => (
    <div 
      className={`p-2 rounded text-xs font-medium text-white mb-1 cursor-pointer hover:opacity-80 transition-opacity`}
      style={{ backgroundColor: lesson.color }}
      title={`${lesson.group.name} - ${lesson.teacher.name} (${lesson.classroom.name})`}
    >
      <div className="font-semibold">{lesson.group.name}</div>
      <div className="text-xs opacity-90">{lesson.teacher.name}</div>
      <div className="text-xs opacity-75">{lesson.classroom.name}</div>
    </div>
  );

  const weekDays = getWeekDays();
  const timeSlots = getTimeSlots();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок и управление */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900">Расписание занятий</h1>
            <div className="flex space-x-2">
              <button 
                onClick={() => {
                  const prevWeek = new Date(currentWeek);
                  prevWeek.setDate(currentWeek.getDate() - 7);
                  setCurrentWeek(prevWeek);
                }}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                ← Пред. неделя
              </button>
              <button 
                onClick={() => setCurrentWeek(new Date())}
                className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Сегодня
              </button>
              <button 
                onClick={() => {
                  const nextWeek = new Date(currentWeek);
                  nextWeek.setDate(currentWeek.getDate() + 7);
                  setCurrentWeek(nextWeek);
                }}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                След. неделя →
              </button>
            </div>
          </div>

          {/* Фильтры и конфликты */}
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <div className="flex justify-between items-center">
              <div className="flex space-x-4">
                <select
                  className="p-2 border border-gray-300 rounded-lg"
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                >
                  <option value="">Все филиалы</option>
                  {branches.map(branch => (
                    <option key={branch.id} value={branch.id}>{branch.name}</option>
                  ))}
                </select>

                <select
                  className="p-2 border border-gray-300 rounded-lg"
                  value={selectedTeacher}
                  onChange={(e) => setSelectedTeacher(e.target.value)}
                >
                  <option value="">Все преподаватели</option>
                  {teachers.map(teacher => (
                    <option key={teacher.id} value={teacher.id}>{teacher.full_name}</option>
                  ))}
                </select>
              </div>

              {conflicts.length > 0 && (
                <div className="flex items-center text-red-600">
                  <AlertTriangle className="h-5 w-5 mr-1" />
                  <span className="text-sm font-medium">
                    {conflicts.length} конфликт(ов) в расписании
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Календарная сетка */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="grid grid-cols-8 border-b border-gray-200">
              <div className="p-4 bg-gray-50 font-medium text-gray-700">Время</div>
              {weekDays.map((day, index) => (
                <div key={index} className="p-4 bg-gray-50 font-medium text-gray-700 text-center">
                  <div className="text-sm">{day.toLocaleDateString('ru-RU', { weekday: 'short' })}</div>
                  <div className="text-lg">{day.getDate()}</div>
                </div>
              ))}
            </div>

            {timeSlots.map(time => (
              <div key={time} className="grid grid-cols-8 border-b border-gray-100">
                <div className="p-2 bg-gray-50 text-sm text-gray-600 font-medium flex items-center">
                  {time}
                </div>
                {weekDays.map((day, dayIndex) => {
                  const dayLessons = getLessonsForSlot(day, time);
                  return (
                    <div key={dayIndex} className="p-2 min-h-[80px] border-r border-gray-100 last:border-r-0">
                      {dayLessons.map((lesson, lessonIndex) => (
                        <LessonCard key={lessonIndex} lesson={lesson} />
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Главный компонент приложения
const LearningCenterApp = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'students':
        return <StudentManagement />;
      case 'schedule':
        return <ScheduleCalendar />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Боковое меню */}
      <nav className="w-64 bg-white shadow-lg">
        <div className="p-4">
          <h1 className="text-xl font-bold text-gray-800">Учебный центр</h1>
        </div>
        
        <ul className="mt-4">
          <li>
            <button
              onClick={() => setCurrentPage('dashboard')}
              className={`w-full text-left px-4 py-3 hover:bg-gray-100 flex items-center ${
                currentPage === 'dashboard' ? 'bg-blue-50 border-r-2 border-blue-500 text-blue-700' : 'text-gray-700'
              }`}
            >
              <Calendar className="h-5 w-5 mr-3" />
              Панель управления
            </button>
          </li>
          <li>
            <button
              onClick={() => setCurrentPage('students')}
              className={`w-full text-left px-4 py-3 hover:bg-gray-100 flex items-center ${
                currentPage === 'students' ? 'bg-blue-50 border-r-2 border-blue-500 text-blue-700' : 'text-gray-700'
              }`}
            >
              <Users className="h-5 w-5 mr-3" />
              Ученики
            </button>
          </li>
          <li>
            <button
              onClick={() => setCurrentPage('schedule')}
              className={`w-full text-left px-4 py-3 hover:bg-gray-100 flex items-center ${
                currentPage === 'schedule' ? 'bg-blue-50 border-r-2 border-blue-500 text-blue-700' : 'text-gray-700'
              }`}
            >
              <Clock className="h-5 w-5 mr-3" />
              Расписание
            </button>
          </li>
        </ul>
      </nav>

      {/* Основной контент */}
      <main className="flex-1">
        {renderCurrentPage()}
      </main>
    </div>
  );
};

export default LearningCenterApp;