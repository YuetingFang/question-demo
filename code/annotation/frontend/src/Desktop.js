import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, unstable_HistoryRouter as HistoryRouter } from 'react-router-dom';
import { createBrowserHistory } from 'history';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Desktop.css';

// Import only desktop pages
import Introduction from './pages/Introduction';
import Guidelines from './pages/Guidelines';
import ExamplesPage from './pages/ExamplesPage';
import ThankYouPage from './pages/ThankYouPage';

// 创建自定义历史对象，使我们可以完全控制导航器历史
const history = createBrowserHistory();

// 自定义路由器组件，使用传入的history对象
function CustomRouter({ history, ...props }) {
  return (
    <HistoryRouter history={history} {...props} />
  );
}


// 应用已启动标记
let appStarted = false;

// 主路由组件 - 只使用桌面版本
function DesktopRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Introduction />} />
      <Route path="/introduction" element={<Introduction />} />
      <Route path="/guidelines" element={<Guidelines />} />
      <Route path="/examples" element={<Navigate to="/examples/0" replace />} />
      <Route path="/examples/:index" element={<ExamplesPage />} />
      <Route path="/thankyou" element={<ThankYouPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// 强制阻止后退按钮功能
// 这种方法更强大，可以确保每次点击后退按钮都停留在当前页面
history.listen(({ action }) => {
  // 监听所有的POP动作（浏览器的后退按钮操作）
  if (action === 'POP') {
    // 立即进行一次前进操作来抛掉后退操作
    // 同时使用replace而不是push，以避免创建新的历史记录
    const currentPath = window.location.pathname;
    console.log('Blocking back button navigation from path:', currentPath);
    history.replace(currentPath);
  }
});

// 简化历史管理代码，避免干扰正常导航
if (typeof window !== 'undefined') {
  // 添加popstate事件监听器阻止后退按钮
  window.addEventListener('popstate', function(e) {
    // 获取当前路径
    const currentPath = window.location.pathname;
    
    // 如果是例子页面，允许导航
    if (currentPath.startsWith('/examples/')) {
      console.log('Allowing navigation to examples page:', currentPath);
      return true;
    }
    
    // 对于其他页面，阻止后退
    console.log('Blocking back button navigation from path:', currentPath);
    window.history.pushState({noBackButton: true, path: currentPath}, document.title, currentPath);
    
    // 阻止默认行为
    e.preventDefault();
    return false;
  });
  
  // 在DOM加载完成后设置历史状态
  document.addEventListener('DOMContentLoaded', function() {
    // 保存当前路径
    const currentPath = window.location.pathname;
    console.log('Setting history state for path:', currentPath);
    
    // 如果是例子页面，不进行历史操作
    if (currentPath.startsWith('/examples/')) {
      console.log('Preserving history for examples page');
      return;
    }
    
    // 对于其他页面，设置历史状态
    window.history.replaceState({firstPage: true}, document.title, currentPath);
  });
}

// 导航管理组件 - 增强版本，每个页面都清空历史栈
function NavigationManager() {
  const location = useLocation();
  const navigate = useNavigate();

  // 处理页面切换时清空历史栈
  useEffect(() => {
    // 清空当前页面的历史栈
    const clearHistoryStack = () => {
      if (typeof window !== 'undefined') {
        // 1. 替换当前历史条目
        window.history.replaceState({ noBackButton: true }, document.title);
        // 2. 添加新的历史条目（这样当前页面成为历史中的第二页）
        window.history.pushState({ noBackButton: true }, document.title);
        // 3. 修改当前条目的状态以区分
        window.history.replaceState({ currentPage: location.pathname }, document.title);
        
        console.log('History stack cleared on page:', location.pathname);
      }
    };
    
    // 在每次页面切换时清空历史栈
    clearHistoryStack();
    
  }, [location.pathname]); // 依赖于当前路径，每次路径变化时执行

  // 处理初始化和页面刷新
  useEffect(() => {
    // 处理初始化、刷新或直接URL访问
    if (!appStarted) {
      // 如果不在首页并且应用刚刚加载，重定向到首页
      if (location.pathname !== '/') {
        navigate('/', { replace: true });
      }
      appStarted = true;
    }
  }, [location.pathname, navigate]);

  // 监听浏览器的后退按钮
  useEffect(() => {
    const handleBeforeUnload = () => {
      // 刷新则清除应用状态
      appStarted = false;
    };
    
    // 添加页面卸载事件监听器
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return null;
}

// 主应用组件
function Desktop() {
  return (
    <CustomRouter history={history}>
      <div className="App">
        <NavigationManager />
        <main className="desktop-main">
          <DesktopRoutes />
        </main>
      </div>
    </CustomRouter>
  );
}

export default Desktop;
