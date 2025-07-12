import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DesktopLayout from '../components/DesktopLayout';

/**
 * 桌面端 Guidelines 页面组件
 * 显示研究指南和用户同意表单
 */
function DesktopGuidelines() {
  const [agreed, setAgreed] = useState(false);
  const navigate = useNavigate();

  // 处理复选框变化
  const handleAgreeChange = useCallback((e) => {
    setAgreed(e.target.checked);
  }, []);

  // 处理下一步按钮点击
  const handleNextClick = useCallback(() => {
    if (agreed) {
      navigate('/examples');
    }
  }, [agreed, navigate]);

  return (
    <DesktopLayout title="Annotation Guide">
      <div className="desktop-panel">
        <div className="panel-header">
          <h1 className="panel-title">Your Annotation Guide</h1>
        </div>
        
        <div className="panel-body">
          <p className="intro-paragraph">
            Before proceeding with the annotation task, please familiarize yourself with 
            the database information and the annotation tasks you will be performing.
          </p>
          <br />
          <div className="section-container">
            <p className="section-title"><strong><u>Database Information</u></strong></p>
            <ul className="enhanced-list">
              <li className="enhanced-list-item"><i>Database Overview</i> : a brief introduction to the domain and contents of the database.</li>
              <li className="enhanced-list-item"><i>Table Names</i> : the names of the tables involved.</li>
              <li className="enhanced-list-item"><i>Column Descriptions</i> : short explanations of each column's role or meaning.</li>
              <li className="enhanced-list-item"><i>10 Sampled Rows per Table</i> : real sample data from each table to give you a concrete understanding of the database content.</li>
            </ul>
            <br />  
          </div>

          <div className="section-container">
            <p className="section-title"><strong><u>Task</u></strong></p>
            <p className="section-content">
              Imagine you are using an query tool (e.g., Siri, Google Assistant, or ChatGPT) that is able to retrieve relevant contents from a given database based on your natural language text. <span className="text-danger fw-bold">Type one or more 
               natural language statements/commands/questions/queries</span> that you would pose to a tool like Siri, Google Assistant, or ChatGPT to retrieve each of the presented text description. 
            </p>
            <br />
          </div>

          <div className="section-container">
            <p><strong><u>Notes</u></strong></p>
            <ul className="enhanced-list">
              <li className="enhanced-list-item">To enter more than one statement/command/question/query for the text description, you can press the Add button.</li>
            </ul>
            <br />
          </div>
        </div>
        
        <div className="panel-footer">
          <div className="desktop-form-check">
            <input 
              type="checkbox" 
              id="agree-checkbox"
              checked={agreed}
              onChange={handleAgreeChange}
              className="desktop-form-check-input"
            />
            <label htmlFor="agree-checkbox" className="desktop-form-check-label text-danger fw-bold">
              I have read the guide and am ready to perform the tasks.   
            </label>
          </div>
          
          <button 
            className={`desktop-button desktop-button-primary ${!agreed ? 'disabled' : ''}`}
            onClick={handleNextClick} 
            disabled={!agreed}
          >
            Next
          </button>
        </div>
      </div>
    </DesktopLayout>
  );
}

export default DesktopGuidelines;
