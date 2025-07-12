/**
 * API 配置文件
 * 根据不同的环境返回对应的 API 基础 URL
 */

// 获取当前环境的 API 基础 URL
const getApiBaseUrl = () => {
  // 判断是否在生产环境中
  const isProduction = process.env.NODE_ENV === 'production';
  
  // 如果有明确设置的 API 基础 URL，优先使用（通过环境变量）
  if (process.env.REACT_APP_API_BASE) {
    return process.env.REACT_APP_API_BASE;
  }
  
  // 判断当前 URL 是否是本地开发环境
  const isLocalhost = 
    window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1';
    
  // 本地开发环境：使用相对路径（setupProxy.js 会处理代理）
  if (isLocalhost) {
    return '';
  }
  
  // 生产环境：使用部署的后端 API 地址
  return 'https://question-demo-backend.onrender.com';
};

// API 基础 URL
export const API_BASE_URL = getApiBaseUrl();

// API 调用函数
export const fetchApi = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${url}:`, error);
    throw error;
  }
};
