import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DesktopLayout from '../components/DesktopLayout';

/**
 * 桌面端 Introduction 页面组件
 * 显示研究介绍信息和用户同意表单
 * 用户需要勾选同意复选框才能继续
 */
function DesktopIntroduction() {
  const [agreed, setAgreed] = useState(false);
  const navigate = useNavigate();

  // 处理复选框变化
  const handleAgreeChange = useCallback((e) => {
    setAgreed(e.target.checked);
  }, []);

  // 处理下一步按钮点击
  const handleNextClick = useCallback(() => {
    if (agreed) {
      navigate('/guidelines');
    }
  }, [agreed, navigate]);

  return (
    <DesktopLayout title="Research Study Introduction">
      <div className="desktop-panel">
        <div className="panel-header">
          <h1 className="panel-title">Introduction</h1>
        </div>
        
        <div className="panel-body">
          <div className="desktop-content-text">
            <p>
              Thank you for volunteering to participate in this study. The goal of this study is to understand how people use natural language to query data.
            </p> 
            <br />
            <p><strong>Note:</strong></p>
            <ul>
              <li>The study will take approximately <strong>25 minutes</strong> to complete.</li>
              <li>We recommend running the study on the <strong>Google Chrome</strong> browser with a maximized window.</li>
              <li>Pressing the "Refresh" button or "Back" button during the session will always return you to this introduction page.</li>
            </ul>
            <br />
            <p><strong>Disclosures:</strong></p>
            <ul>
              <li>You do not waive any of your legal rights by agreeing to be in the study.</li>
              <li>You <strong>WILL NOT</strong> be financially compensated.</li>
              <li>We <strong>DO NOT</strong> collect any personally identifiable information.</li>
              <li>This study is for research purposes only.</li>
            </ul>
          </div>
        </div>
        
        <div className="panel-footer">
          <div className="desktop-form-check">
            <input 
              type="checkbox" 
              id="agreement-checkbox"
              checked={agreed}
              onChange={handleAgreeChange}
              className="desktop-form-check-input"
            />
            <label htmlFor="agreement-checkbox" className="desktop-form-check-label text-danger fw-bold">
              I have read the above disclosure and consent to volunteer.
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

export default DesktopIntroduction;
