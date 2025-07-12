import React from 'react';
import { useNavigate } from 'react-router-dom';
import DesktopLayout from '../components/DesktopLayout';

/**
 * Thank You Page shown after completing all examples
 * Displays a thank you message and completion confirmation
 */
function ThankYouPage() {
  const navigate = useNavigate();
  
  return (
    <DesktopLayout>
      <div className="desktop-panel">
        <div className="panel-header">
          <h1 className="panel-title">Thank You!</h1>
        </div>
        <div className="panel-body">
          <div className="thank-you-container" style={{ 
            textAlign: 'center', 
            padding: '3rem',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            <div style={{ fontSize: '72px', marginBottom: '2rem' }}>
              🎉
            </div>
            
            <h2 style={{ marginBottom: '2rem', color: '#2c3e50' }}>
              All Tasks Completed
            </h2>
            
            <p style={{ 
              fontSize: '1.2rem', 
              lineHeight: '1.7', 
              marginBottom: '2rem',
              color: '#34495e'
            }}>
              Thank you for completing all the tasks! Your contributions are extremely valuable 
              and will help us better understanding the nature of utterances people use to specify query intents through natural language.
            </p>
            
            <p style={{ 
              fontSize: '1.1rem',
              marginBottom: '2rem',
              color: '#34495e'
            }}>
              All of your input texts have been successfully saved. You may now close this window or return to the introduction.
            </p>
            
            <div style={{ marginTop: '3rem' }}>
              <button
                className="desktop-button desktop-button-primary"
                onClick={() => navigate('/')}
                style={{ marginRight: '1rem' }}
              >
                Return to Introduction
              </button>
            </div>
          </div>
        </div>
      </div>
    </DesktopLayout>
  );
}

export default ThankYouPage;
