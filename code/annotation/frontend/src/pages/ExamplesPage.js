import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/apiConfig';
import { useParams, useNavigate } from 'react-router-dom';
import { Alert, Spinner } from 'react-bootstrap';
import DesktopLayout from '../components/DesktopLayout';

/**
 * 桌面端 ExamplesPage 页面组件
 * 显示数据库表、任务描述和用户输入表单
 */
function ExamplesPage() {
  // 状态管理
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [displayTables, setDisplayTables] = useState([]);
  const [availableTables, setAvailableTables] = useState([]);
  const [tableData, setTableData] = useState({});
  const [currentTask, setCurrentTask] = useState(null);
  const [userQueries, setUserQueries] = useState(['']);
  const [taskCompleted, setTaskCompleted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [totalTasks, setTotalTasks] = useState(1);
  const [allTableNames, setAllTableNames] = useState([]);
  const [currentDbId, setCurrentDbId] = useState('');
  const [taskData, setTaskData] = useState([]);
  const [currentDbOverview, setCurrentDbOverview] = useState('');
  // 为用户生成唯一ID
  const [userId] = useState(() => {
    // 检查localStorage中是否已有userId
    const storedId = localStorage.getItem('annotationUserId');
    if (storedId) return storedId;
    
    // 如果没有，创建一个新的UUID
    const newId = `user_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
    localStorage.setItem('annotationUserId', newId);
    return newId;
  });
  
  const navigate = useNavigate();
  const { index } = useParams();
  
  // 当前任务索引
  const currentIndex = index !== undefined ? parseInt(index, 10) : 0;
  
  // 从API加载动态数据和任务数据
  useEffect(() => {
    // 重置用户输入和任务完成状态
    setUserQueries(['']);
    setTaskCompleted(false);
    
    const loadDynamicData = async () => {
      setLoading(true);
      try {
        console.log('Fetching task and table data...');
  
        // 1. 加载任务描述数据
        const taskRes = await fetch(`${API_BASE_URL}/api/task-descriptions`);
        if (!taskRes.ok) throw new Error('Failed to fetch task descriptions');
        const tasks = await taskRes.json();
        console.log('Loaded task descriptions:', tasks.length);
  
        setTaskData(tasks);
        setTotalTasks(tasks.length);
  
        const currentTask = tasks[currentIndex];
        if (!currentTask) throw new Error('Current task not found');
        
        const dbId = currentTask.db_id;
        setCurrentDbId(dbId);
        setCurrentTask({
          db_id: dbId,
          task_id: currentIndex,
          question_id: currentTask.question_id.toString(),
          task_description: currentTask.task_description,
        });
  
        // 2. 加载动态表格数据
        const tablesRes = await fetch(`${API_BASE_URL}/api/dynamic-tables?db_id=${dbId}`);
        if (!tablesRes.ok) throw new Error(`Failed to fetch dynamic tables: ${tablesRes.status}`);
        const dynamicData = await tablesRes.json();
        console.log('Loaded dynamic table data');
  
        // 3. 处理表格数据结构
        const { table_names = [], tables_to_display = [], column_names = {}, column_descriptions = {}, table_data = {} } = dynamicData;
        const formattedTables = {};
        tables_to_display.forEach(tableName => {
          formattedTables[tableName] = {
            columns: column_names[tableName] || [],
            columnDescriptions: column_descriptions[tableName] || [],
            data: table_data[tableName] || []
          };
        });
  
        setAllTableNames(table_names);
        setDisplayTables(tables_to_display);
        setAvailableTables(table_names.filter(name => !tables_to_display.includes(name)));
        setTableData(formattedTables);
  
        // 4. 设置任务数据（优先来自动态数据中的task）
        setCurrentTask(prev => ({
          ...prev,
          ...dynamicData.task,
          task_id: dynamicData.task?.task_id || prev.task_id,
          task_description: dynamicData.task?.task_description || prev.task_description,
        }));
  
        // 5. 设置数据库概览
        if (dynamicData.db_overview) {
          setCurrentDbOverview(dynamicData.db_overview);
        }
  
      } catch (err) {
        console.error('Error loading dynamic data:', err);
        setError(`加载失败: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
  
    loadDynamicData();
  }, [currentIndex]);
  
  
  // 处理查询输入变更
  const handleQueryChange = (index, value) => {
    const updatedQueries = [...userQueries];
    updatedQueries[index] = value;
    setUserQueries(updatedQueries);
  };
  
  // 添加新的查询输入框
  const addQueryInput = () => {
    setUserQueries([...userQueries, '']);
  };
  
  // 处理表格切换
  const handleTableSwitch = async (selectedTable, indexToReplace) => {
    if (!selectedTable || selectedTable === displayTables[indexToReplace]) {
      return; // 相同表格，不做切换
    }
    
    // 检查我们是否有所选表格的数据
    if (!tableData[selectedTable] || 
        !tableData[selectedTable].columns || 
        !tableData[selectedTable].data) {
      
      console.log(`Data for ${selectedTable} not found in tableData, fetching it...`);
      
      try {
        // 临时显示加载状态
        const tempTableData = {...tableData};
        tempTableData[selectedTable] = { 
          columns: [], 
          columnDescriptions: [],
          data: [], 
          isLoading: true 
        };
        setTableData(tempTableData);
        
        // 尝试从API获取该表格的数据 - 使用当前任务的db_id
        const response = await fetch(`${API_BASE_URL}/api/table-data?tableName=${selectedTable}&db_id=${currentDbId}`);
        
        if (response.ok) {
          const tableInfo = await response.json();
          
          // 更新表格数据
          const updatedTableData = {...tableData};
          updatedTableData[selectedTable] = {
            columns: tableInfo.columns || [],
            columnDescriptions: tableInfo.columnDescriptions || [],
            data: tableInfo.data || [],
            isLoading: false
          };
          
          setTableData(updatedTableData);
        } else {
          console.error(`Failed to fetch data for table ${selectedTable}:`, response.status);
          
          // 将错误状态标记在表格数据中
          const updatedTableData = {...tableData};
          updatedTableData[selectedTable] = { 
            columns: [], 
            columnDescriptions: [],
            data: [], 
            error: true,
            isLoading: false
          };
          setTableData(updatedTableData);
        }
      } catch (error) {
        console.error(`Error fetching table data for ${selectedTable}:`, error);
        
        // 将错误状态标记在表格数据中
        const updatedTableData = {...tableData};
        updatedTableData[selectedTable] = { 
          columns: [], 
          columnDescriptions: [],
          data: [], 
          error: true,
          isLoading: false
        };
        setTableData(updatedTableData);
      }
    }
    
    // 复制当前显示的表格列表
    const updatedDisplayTables = [...displayTables];
    
    // 替换选中的索引位置的表格
    const oldTable = updatedDisplayTables[indexToReplace];
    updatedDisplayTables[indexToReplace] = selectedTable;
    
    // 更新显示的表格
    setDisplayTables(updatedDisplayTables);
    
    // 更新可用的表格
    const updatedAvailableTables = [...availableTables];
    const selectedTableIndex = updatedAvailableTables.indexOf(selectedTable);
    
    if (selectedTableIndex !== -1) {
      // 如果选择的表格在可用列表中，则从可用列表中移除
      updatedAvailableTables.splice(selectedTableIndex, 1);
      // 将被替换的表格添加到可用列表
      updatedAvailableTables.push(oldTable);
      setAvailableTables(updatedAvailableTables);
    }
  };
  
  // 提交当前任务
  const submitCurrentTask = async () => {
    if (userQueries.some(q => !q.trim())) return false;
    
    setSubmitting(true);
    
    try {
      // 提取当前任务数据
      const currentTaskData = taskData[currentIndex];
      
      // 准备要提交的数据
      const submissionData = {
        user_id: userId,
        inputs: userQueries,
        question_id: currentTaskData.question_id,
        db_id: currentDbId,
        task_description: currentTaskData.task_description
      };
      
      // 发送到API保存到CSV
      const response = await fetch(`${API_BASE_URL}/api/save-annotation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });
      
      const responseData = await response.json();
      
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to save annotation');
      }
      
      console.log('Annotation saved successfully:', responseData);
      setTaskCompleted(true);
      return true; // 成功提交
    } catch (err) {
      console.error('Error saving annotation:', err);
      alert(`Failed to save: ${err.message}`);
      return false; // 提交失败
    } finally {
      setSubmitting(false);
    }
  };
  // 处理Next按钮点击事件
  const handleNextClick = async () => {
    const success = await submitCurrentTask();
    if (success) {
      if (currentIndex < totalTasks - 1) {
        // 如果还有更多例子，跳转到下一个
        navigate(`/examples/${currentIndex + 1}`);
      } else {
        // 如果这是最后一个例子，跳转到感谢页面
        navigate('/thankyou');
      }
    }
  };
  
  // 渲染表格选择器
  const renderTableSelector = (tableIndex) => {
    const currentTable = displayTables[tableIndex];
    
    // 如果没有其他表格可选，则显示当前表格名称
    if (availableTables.length === 0 || allTableNames.length <= 3) {
      return (
        <div className="desktop-table-header">
          <span className="table-name-display">{currentTable}</span>
        </div>
      );
    }
    
    // 否则显示下拉选择器
    return (
      <div className="desktop-table-header">
        <select
          className="desktop-table-select"
          value={currentTable}
          onChange={(e) => handleTableSwitch(e.target.value, tableIndex)}
        >
          <option value={currentTable}>{currentTable}</option>
          {availableTables.map(tableName => (
            <option key={tableName} value={tableName}>
              {tableName}
            </option>
          ))}
        </select>
      </div>
    );
  };
  
  // 渲染单个表格
  const renderSingleTable = (tableName, tableIndex) => {
    console.log('Rendering table:', tableName, 'with data:', tableData[tableName]);
    const data = tableData[tableName];
    
    // 如果没有数据，显示错误提示
    if (!data) {
      console.error('No data for table:', tableName);
      return <Alert variant="warning">Unable to load table data for {tableName}</Alert>;
    }
    
    const tableStyle = {
      fontSize: '0.8rem'
    };
    
    // 如果表格数据正在加载中
    if (data.isLoading) {
      return (
        <div className="desktop-table-panel">
          {renderTableSelector(tableIndex)}
          <div className="desktop-tables-container text-center py-4">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading table {tableName}...</span>
            </Spinner>
            <p className="mt-2">Loading table data...</p>
          </div>
        </div>
      );
    }
    
    // 如果加载表格数据时发生错误
    if (data.error) {
      return (
        <div className="desktop-table-panel">
          {renderTableSelector(tableIndex)}
          <div className="desktop-tables-container">
            <Alert variant="danger">
              Failed to load data for table: {tableName}. Please try selecting a different table.
            </Alert>
          </div>
        </div>
      );
    }
    
    // 确保数据结构正确
    const columns = data.columns || [];
    const columnDescriptions = data.columnDescriptions || [];
    const tableRows = data.data || [];
    
    console.log('Table structure:', {
      columns: columns.length,
      columnDescriptions: columnDescriptions.length,
      rows: tableRows.length
    });
    
    return (
      <div className="desktop-table-panel">
        {renderTableSelector(tableIndex)}
        
        <div className="desktop-tables-container">
          <div className="table-scroll-container">
            <table className="desktop-table">
              <thead>
                <tr>
                  {columns.map((col, idx) => {
                    let displayText = col;
                    if (columnDescriptions && columnDescriptions[idx]) {
                      const columnInfo = columnDescriptions[idx];
                      if (columnInfo.description && columnInfo.description.trim() !== '') {
                        displayText = columnInfo.description;
                      } else if (columnInfo.name && columnInfo.name.trim() !== '') {
                        displayText = columnInfo.name;
                      }
                    }
                    return <th key={idx} title={col}>{displayText}</th>;
                  })}
                </tr>
              </thead>
              <tbody>
                {tableRows && tableRows.length > 0 ? tableRows.map((row, rowIdx) => {
                  // 处理不同类型的行数据格式
                  if (Array.isArray(row)) {
                    // 如果行是数组格式
                    return (
                      <tr key={rowIdx}>
                        {row.map((cell, cellIdx) => {
                          const displayValue = cell === null || cell === undefined ? '' : String(cell);
                          return <td key={cellIdx}>{displayValue}</td>;
                        })}
                      </tr>
                    );
                  } else if (typeof row === 'object' && row !== null) {
                    // 如果行是对象格式 (API 可能返回对象而不是数组)
                    return (
                      <tr key={rowIdx}>
                        {columns.map((colName, colIdx) => {
                          const cell = row[colName];
                          const displayValue = cell === null || cell === undefined ? '' : String(cell);
                          return <td key={colIdx}>{displayValue}</td>;
                        })}
                      </tr>
                    );
                  } else {
                    // 未知格式
                    return <tr key={rowIdx}><td>Invalid row format</td></tr>;
                  }
                }) : (
                  <tr><td colSpan={columns.length || 1}>No data available</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };
  
  // 渲染所有表格 - 垂直排列
  const renderTables = () => {
    return displayTables.map((tableName, index) => (
      <div key={tableName} className="vertical-table-container">
        {renderSingleTable(tableName, index)}
      </div>
    ));
  };
  
  // 渲染任务描述
  const renderTaskDescription = () => {
    if (!currentTask) {
      return <Alert variant="info">No task information available</Alert>;
    }
    
    // 提取当前任务索引的数据
    const currentTaskData = taskData[currentIndex];
    
    if (!currentTaskData) {
      return <Alert variant="warning">Task data not found</Alert>;
    }
    
    // 处理可能包含换行符的文本
    const formatTaskDescription = (text) => {
      if (!text) return null;
    
      return text.split('\n').map((line, i) => (
        <div key={i} style={{ paddingLeft: '2em' }}>
          {line}
        </div>
      ));
    };
    
    return (
      <div className="task-description">
        <div className="d-flex justify-content-between align-items-center mb-2">
          <h4 className="mb-0"> <strong>Task Description</strong> <span style={{fontSize: '1rem'}}>includes both the intended goal and all necessary conditions.</span></h4> 
        </div>
        <div className="desktop-task-description">
          <br />
          {formatTaskDescription(currentTaskData.task_description)}
        </div>
      </div>
    );    
  };
  
  // 渲染用户输入区域
  const renderUserInput = () => {
    // Define different orderings based on the current page index
    const orderings = [
      "statements/commands/questions/queries", // for index 0
      "queries/statements/commands/questions", // for index 1
      "questions/queries/statements/commands", // for index 2
      "commands/questions/queries/statements"  // for index 3
    ];
    
    // Get the ordering based on the currentIndex, using modulo to handle more pages than orderings
    const currentOrdering = orderings[currentIndex % orderings.length];
    
    return (
      <div className="desktop-input-container">
        <div className="d-flex justify-content-between align-items-center mb-1">
          <p> Type one or more natural language {currentOrdering} to retrieve the expected information from the left database based on the task description. </p>
        </div>

        {userQueries.map((query, index) => (
          <div key={index} className="desktop-input-row">
            <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <input 
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(index, e.target.value)}
                className="desktop-input-field"
                disabled={submitting || taskCompleted}
                placeholder="Enter text here..."
                style={{ flex: 1 }}
              />
              {!taskCompleted && index === userQueries.length - 1 && (
                <div style={{ marginLeft: '15px' }}>
                  <button 
                    className={`desktop-button desktop-button-secondary ${!query.trim() ? 'disabled' : ''}`}
                    onClick={addQueryInput}
                    disabled={!query.trim()}
                  >
                  <strong> + </strong> Add More
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  // 加载中显示
  if (loading) {
    return (
      <DesktopLayout title="Loading Task...">
        <div className="d-flex justify-content-center align-items-center" style={{height: '60vh'}}>
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      </DesktopLayout>
    );
  }

  // 错误显示
  if (error) {
    console.log('Rendering error state:', error);
    return (
      <DesktopLayout title="Error">
        <div className="desktop-panel">
          <div className="panel-header">
            <h2 className="panel-title text-danger">Error Loading Data</h2>
          </div>
          <div className="panel-body">
            <p>{error}</p>
            <p>Using sample data to continue. The real data couldn't be loaded from the API.</p>
          </div>
          <div className="panel-footer">
            <button 
              className="desktop-button desktop-button-primary"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </DesktopLayout>
    );
  }
  
  // 主要内容显示
  // 确保只渲染有数据的表格
  // No longer needed: const tableNames = Object.keys(tableData || {}).filter(name => tableData[name]);
  return (
    <DesktopLayout>
      <div className="desktop-panel">  
        <div className="panel-header">
          <h1 className="panel-title">Task {currentIndex + 1} / {totalTasks} </h1>
        </div>
        <div className="panel-body">
          <div className="database-header mb-3">
            <h4><strong> Database:</strong> <span className="database-name">{currentDbId}</span></h4>
            <p>{currentDbOverview}</p>
            <br />
          </div>
          
          <div className="desktop-layout-container">
            {/* 左侧表格区域 - 垂直排列3个表格 */}
            <div className="tables-column">
              <h4 className="section-title"><strong>Table Content</strong></h4>
              <div className="vertical-tables-container">
                    {renderTables()}
              </div>
            </div>
            
            {/* 右侧任务描述和用户输入区域 */}
            <div className="task-column">
              <div className="task-description-container">
                {renderTaskDescription()}
              </div>
              <div className="user-input-container">
                {renderUserInput()}
              </div>
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <button 
                  className={`desktop-button desktop-button-primary ${submitting || userQueries.some(q => !q.trim()) ? 'disabled' : ''}`}
                  onClick={handleNextClick} 
                  disabled={submitting || userQueries.some(q => !q.trim())}
                >
                  {submitting ? 'Submitting...' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DesktopLayout>
  );
}
  
export default ExamplesPage;
