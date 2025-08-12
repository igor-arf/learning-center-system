import React from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;

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
